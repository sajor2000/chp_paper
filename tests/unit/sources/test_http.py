from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest
import respx

from chicagohealthmap.sources.adapters.base import AcquisitionPlan
from chicagohealthmap.sources.http import (
    HTTP_TIMEOUT,
    AcquisitionError,
    HttpAcquirer,
    JsonPagination,
    redacted_request_record,
)
from chicagohealthmap.sources.registry import RegistrySource, load_registry
from chicagohealthmap.sources.snapshot import SnapshotWriter


ROOT = Path(__file__).parents[3]


@pytest.fixture(scope="module")
def tiger_source() -> RegistrySource:
    return load_registry(ROOT / "config" / "source_registry.yml").by_id["census_tiger_2024_tract"]


def test_timeout_contract_is_exact() -> None:
    assert HTTP_TIMEOUT.connect == 20.0
    assert HTTP_TIMEOUT.read == 120.0
    assert HTTP_TIMEOUT.write == 120.0
    assert HTTP_TIMEOUT.pool == 20.0


def test_plan_is_immutable_deterministic_and_credential_free(tiger_source: RegistrySource) -> None:
    acquirer = HttpAcquirer(required_environment_variables=("CENSUS_API_KEY",))

    first = acquirer.plan(tiger_source)
    second = acquirer.plan(tiger_source)

    assert first == second
    assert isinstance(first, AcquisitionPlan)
    assert first.parameters == ()
    assert first.destination_paths == ("original/tl_2024_17_tract.zip",)
    assert first.required_environment_variables == ("CENSUS_API_KEY",)
    assert "reviewer-secret" not in str(first.model_dump(mode="json")).casefold()
    with pytest.raises(Exception):
        first.source_id = "changed"  # type: ignore[misc]


@respx.mock
def test_successful_bytes_stream_to_an_immutable_snapshot(
    tmp_path: Path, tiger_source: RegistrySource
) -> None:
    payload = b"PK\x03\x04fixture"
    route = respx.get(str(tiger_source.endpoint_url)).mock(
        return_value=httpx.Response(
            200, content=payload, headers={"content-type": "application/zip"}
        )
    )
    writer = SnapshotWriter(tmp_path, tiger_source.source_id, "2026-07-14")

    manifest = HttpAcquirer(expected_content_types=("application/zip",)).fetch(tiger_source, writer)

    assert route.call_count == 1
    assert manifest.files[0].byte_count == len(payload)
    final = tmp_path / tiger_source.source_id / "snapshots" / "2026-07-14"
    assert (final / manifest.files[0].path).read_bytes() == payload


@respx.mock
def test_json_page_sequence_accumulates_rows(tmp_path: Path, tiger_source: RegistrySource) -> None:
    route = respx.get(str(tiger_source.endpoint_url)).mock(
        side_effect=[
            httpx.Response(
                200, json=[{"id": 1}, {"id": 2}], headers={"content-type": "application/json"}
            ),
            httpx.Response(200, json=[{"id": 3}], headers={"content-type": "application/json"}),
        ]
    )
    writer = SnapshotWriter(tmp_path, tiger_source.source_id, "2026-07-14")
    acquirer = HttpAcquirer(
        expected_content_types=("application/json",),
        pagination=JsonPagination(parameter="offset", page_size=2, expected_total_rows=3),
    )

    manifest = acquirer.fetch(tiger_source, writer)

    assert route.call_count == 2
    assert [item.path for item in manifest.files] == [
        "original/page-0001.json",
        "original/page-0002.json",
    ]
    assert [item.row_count for item in manifest.files] == [2, 1]


@pytest.mark.parametrize("status", [408, 425, 429, 500, 502, 503, 504])
@respx.mock
def test_retryable_statuses_retry_then_succeed(
    tmp_path: Path, tiger_source: RegistrySource, status: int
) -> None:
    route = respx.get(str(tiger_source.endpoint_url)).mock(
        side_effect=[
            httpx.Response(status, headers={"Retry-After": "0"}),
            httpx.Response(200, content=b"ok", headers={"content-type": "application/zip"}),
        ]
    )
    delays: list[float] = []
    writer = SnapshotWriter(tmp_path, tiger_source.source_id, "2026-07-14")

    HttpAcquirer(expected_content_types=("application/zip",), sleep=delays.append).fetch(
        tiger_source, writer
    )

    assert route.call_count == 2
    assert delays == [0.0]


@respx.mock
def test_http_date_retry_after_is_honored_and_capped(
    tmp_path: Path, tiger_source: RegistrySource
) -> None:
    route = respx.get(str(tiger_source.endpoint_url)).mock(
        side_effect=[
            httpx.Response(429, headers={"Retry-After": "Wed, 15 Jul 2026 00:02:00 GMT"}),
            httpx.Response(200, content=b"ok", headers={"content-type": "application/zip"}),
        ]
    )
    delays: list[float] = []
    writer = SnapshotWriter(tmp_path, tiger_source.source_id, "2026-07-14")

    HttpAcquirer(
        expected_content_types=("application/zip",),
        sleep=delays.append,
        now=lambda: datetime(2026, 7, 15, tzinfo=timezone.utc),
    ).fetch(tiger_source, writer)

    assert route.call_count == 2
    assert delays == [60.0]


@pytest.mark.parametrize("status", [400, 401, 403, 404, 405, 409, 422])
@respx.mock
def test_other_client_errors_are_never_retried(
    tmp_path: Path, tiger_source: RegistrySource, status: int
) -> None:
    route = respx.get(str(tiger_source.endpoint_url)).mock(return_value=httpx.Response(status))
    writer = SnapshotWriter(tmp_path, tiger_source.source_id, "2026-07-14")

    with pytest.raises(AcquisitionError, match=f"HTTP {status}"):
        HttpAcquirer(sleep=lambda _: None).fetch(tiger_source, writer)

    assert route.call_count == 1
    assert not writer.staging_path.exists()


@respx.mock
def test_timeout_exhaustion_stops_after_five_attempts(
    tmp_path: Path, tiger_source: RegistrySource
) -> None:
    route = respx.get(str(tiger_source.endpoint_url)).mock(
        side_effect=httpx.ReadTimeout("timed out")
    )
    writer = SnapshotWriter(tmp_path, tiger_source.source_id, "2026-07-14")

    with pytest.raises(AcquisitionError, match="after 5 attempts"):
        HttpAcquirer(sleep=lambda _: None).fetch(tiger_source, writer)

    assert route.call_count == 5
    assert not writer.staging_path.exists()


@respx.mock
def test_content_type_mismatch_fails_without_publishing(
    tmp_path: Path, tiger_source: RegistrySource
) -> None:
    respx.get(str(tiger_source.endpoint_url)).mock(
        return_value=httpx.Response(200, content=b"<html>", headers={"content-type": "text/html"})
    )
    writer = SnapshotWriter(tmp_path, tiger_source.source_id, "2026-07-14")

    with pytest.raises(AcquisitionError, match="content type"):
        HttpAcquirer(expected_content_types=("application/zip",)).fetch(tiger_source, writer)

    assert not writer.staging_path.exists()


@respx.mock
def test_json_expected_total_mismatch_and_malformed_payload_clean_staging(
    tmp_path: Path, tiger_source: RegistrySource
) -> None:
    respx.get(str(tiger_source.endpoint_url)).mock(
        return_value=httpx.Response(
            200, content=b"not-json", headers={"content-type": "application/json"}
        )
    )
    writer = SnapshotWriter(tmp_path, tiger_source.source_id, "2026-07-14")
    acquirer = HttpAcquirer(
        expected_content_types=("application/json",),
        pagination=JsonPagination(parameter="offset", page_size=2, expected_total_rows=3),
    )
    with pytest.raises(AcquisitionError, match="malformed JSON"):
        acquirer.fetch(tiger_source, writer)
    assert not writer.staging_path.exists()

    respx.get(str(tiger_source.endpoint_url)).mock(
        return_value=httpx.Response(
            200, json=[{"id": 1}], headers={"content-type": "application/json"}
        )
    )
    writer = SnapshotWriter(tmp_path, tiger_source.source_id, "2026-07-15")
    with pytest.raises(AcquisitionError, match="expected 3 rows; received 1"):
        acquirer.fetch(tiger_source, writer)
    assert not writer.staging_path.exists()


@respx.mock
def test_json_page_that_exceeds_expected_total_fails_without_an_extra_request(
    tmp_path: Path, tiger_source: RegistrySource
) -> None:
    route = respx.get(str(tiger_source.endpoint_url)).mock(
        return_value=httpx.Response(
            200,
            json=[{"id": 1}, {"id": 2}],
            headers={"content-type": "application/json"},
        )
    )
    writer = SnapshotWriter(tmp_path, tiger_source.source_id, "2026-07-14")
    acquirer = HttpAcquirer(
        expected_content_types=("application/json",),
        pagination=JsonPagination(parameter="offset", page_size=2, expected_total_rows=1),
    )

    with pytest.raises(AcquisitionError, match="expected 1 rows; received 2"):
        acquirer.fetch(tiger_source, writer)

    assert route.call_count == 1
    assert not writer.staging_path.exists()


@respx.mock
def test_oversized_response_is_rejected_before_or_during_streaming(
    tmp_path: Path, tiger_source: RegistrySource
) -> None:
    respx.get(str(tiger_source.endpoint_url)).mock(
        return_value=httpx.Response(
            200,
            content=b"12345",
            headers={"content-type": "application/zip", "content-length": "5"},
        )
    )
    writer = SnapshotWriter(tmp_path, tiger_source.source_id, "2026-07-14")

    with pytest.raises(AcquisitionError, match="response exceeds"):
        HttpAcquirer(max_response_bytes=4).fetch(tiger_source, writer)

    assert not writer.staging_path.exists()


def test_credential_headers_and_query_values_never_enter_request_record() -> None:
    secret = "reviewer-secret-92741"
    record = redacted_request_record(
        method="GET",
        url="https://api.census.gov/data",
        query=(("get", "NAME"), ("api_key", secret), ("access-token", secret)),
        headers=(("Accept", "application/json"), ("Authorization", secret), ("Cookie", secret)),
    )

    serialized = json.dumps(record.model_dump(mode="json"))
    assert secret not in serialized
    assert record.query == {"get": "NAME"}
    assert record.headers == {"Accept": "application/json"}


def test_runtime_secret_channels_accept_only_credential_named_fields() -> None:
    with pytest.raises(ValueError, match="credential_query"):
        HttpAcquirer(credential_query={"offset": "hidden-change"})
    with pytest.raises(ValueError, match="credential_headers"):
        HttpAcquirer(credential_headers={"Accept": "hidden-change"})


@respx.mock
def test_redirect_is_terminal_even_when_injected_client_follows_and_secrets_never_move(
    tmp_path: Path, tiger_source: RegistrySource
) -> None:
    secret = "redirect-secret-92741"
    origin = respx.get(str(tiger_source.endpoint_url)).mock(
        return_value=httpx.Response(302, headers={"location": "https://evil.example/collect"})
    )
    evil = respx.get("https://evil.example/collect").mock(
        return_value=httpx.Response(200, content=b"stolen")
    )
    writer = SnapshotWriter(tmp_path, tiger_source.source_id, "2026-07-14")
    client = httpx.Client(follow_redirects=True)
    try:
        with pytest.raises(AcquisitionError, match="HTTP 302") as captured:
            HttpAcquirer(
                client=client,
                credential_headers={"X-API-Key": secret},
                credential_query={"api_key": secret},
            ).fetch(tiger_source, writer)
    finally:
        client.close()

    assert origin.call_count == 1
    assert evil.call_count == 0
    rendered = repr(captured.value)
    assert secret not in rendered
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None
    assert not writer.staging_path.exists()


@respx.mock
def test_zero_byte_success_is_rejected(tmp_path: Path, tiger_source: RegistrySource) -> None:
    route = respx.get(str(tiger_source.endpoint_url)).mock(
        return_value=httpx.Response(200, content=b"", headers={"content-type": "application/zip"})
    )
    writer = SnapshotWriter(tmp_path, tiger_source.source_id, "2026-07-14")

    with pytest.raises(AcquisitionError, match="zero-byte"):
        HttpAcquirer(expected_content_types=("application/zip",)).fetch(tiger_source, writer)

    assert route.call_count == 1
    assert not writer.staging_path.exists()


def test_exact_timeout_is_forced_on_every_injected_client_request(
    tmp_path: Path, tiger_source: RegistrySource
) -> None:
    observed: list[dict[str, float]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        observed.append(request.extensions["timeout"])
        return httpx.Response(200, content=b"complete", headers={"content-type": "application/zip"})

    client = httpx.Client(transport=httpx.MockTransport(handler), timeout=1.0)
    writer = SnapshotWriter(tmp_path, tiger_source.source_id, "2026-07-14")
    try:
        HttpAcquirer(client=client, expected_content_types=("application/zip",)).fetch(
            tiger_source, writer
        )
    finally:
        client.close()

    assert observed == [{"connect": 20.0, "read": 120.0, "write": 120.0, "pool": 20.0}]


class _FailingStream(httpx.SyncByteStream):
    def __iter__(self):
        yield b"partial-secret-free-bytes"
        raise httpx.ReadError("stream failed")


def test_partial_stream_retries_with_fresh_file_and_publishes_once(
    tmp_path: Path, tiger_source: RegistrySource
) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        if attempts == 1:
            return httpx.Response(
                200, stream=_FailingStream(), headers={"content-type": "application/zip"}
            )
        return httpx.Response(
            200, content=b"complete-second-attempt", headers={"content-type": "application/zip"}
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    writer = SnapshotWriter(tmp_path, tiger_source.source_id, "2026-07-14")
    try:
        manifest = HttpAcquirer(
            client=client,
            expected_content_types=("application/zip",),
            sleep=lambda _: None,
        ).fetch(tiger_source, writer)
    finally:
        client.close()

    final = tmp_path / tiger_source.source_id / "snapshots" / "2026-07-14"
    assert attempts == 2
    assert len(manifest.files) == 1
    assert (final / manifest.files[0].path).read_bytes() == b"complete-second-attempt"


def test_partial_stream_exhaustion_cleans_every_attempt(
    tmp_path: Path, tiger_source: RegistrySource
) -> None:
    attempts = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal attempts
        attempts += 1
        return httpx.Response(
            200, stream=_FailingStream(), headers={"content-type": "application/zip"}
        )

    client = httpx.Client(transport=httpx.MockTransport(handler))
    writer = SnapshotWriter(tmp_path, tiger_source.source_id, "2026-07-14")
    try:
        with pytest.raises(AcquisitionError, match="after 5 attempts") as captured:
            HttpAcquirer(client=client, sleep=lambda _: None).fetch(tiger_source, writer)
    finally:
        client.close()

    assert attempts == 5
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None
    assert not writer.staging_path.exists()


def test_transport_exception_chain_cannot_retain_runtime_secret(
    tmp_path: Path, tiger_source: RegistrySource
) -> None:
    secret = "transport-secret-92741"

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout(f"failed request {request.url}", request=request)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    writer = SnapshotWriter(tmp_path, tiger_source.source_id, "2026-07-14")
    try:
        with pytest.raises(AcquisitionError) as captured:
            HttpAcquirer(
                client=client,
                credential_headers={"X-API-Key": secret},
                credential_query={"api_key": secret},
                sleep=lambda _: None,
            ).fetch(tiger_source, writer)
    finally:
        client.close()

    assert secret not in repr(captured.value)
    assert captured.value.__cause__ is None
    assert captured.value.__context__ is None
