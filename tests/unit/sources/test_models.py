import json
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from chicagohealthmap.sources.models import (
    RequestRecord,
    SnapshotAcquisition,
    SnapshotFile,
    SnapshotManifest,
    SourceSpec,
    Transport,
    ValidationStatus,
)


def valid_source_spec(**overrides: object) -> SourceSpec:
    values: dict[str, object] = {
        "source_id": "census_acs_2024_5y",
        "organization": "US Census Bureau",
        "dataset_title": "2024 American Community Survey 5-Year Estimates",
        "transport": Transport.census_api,
        "landing_url": "https://www.census.gov/programs-surveys/acs",
        "documentation_url": "https://api.census.gov/data/2024/acs/acs5.html",
        "license": "US government public data",
        "snapshot_subdir": "census_acs",
    }
    values.update(overrides)
    return SourceSpec.model_validate(values)


def valid_manifest(**overrides: object) -> SnapshotManifest:
    values: dict[str, object] = {
        "source_id": "census_acs_2024_5y",
        "snapshot_id": "census_acs_2024_5y_2024-12-19",
        "snapshot_date": "2024-12-19",
        "retrieval_started_at": datetime(2024, 12, 19, 14, 0, tzinfo=timezone.utc),
        "retrieval_completed_at": datetime(2024, 12, 19, 14, 1, tzinfo=timezone.utc),
        "files": [
            {
                "path": "response.json",
                "sha256": "a" * 64,
                "byte_count": 128,
                "row_count": 3,
                "page_count": None,
            }
        ],
        "validation_status": ValidationStatus.passed,
    }
    values.update(overrides)
    return SnapshotManifest.model_validate(values)


def valid_acquisition(**overrides: object) -> SnapshotAcquisition:
    values: dict[str, object] = {
        "group": "B01001",
        "url": "https://api.census.gov/data/2024/acs/acs5",
        "parameters": (
            ("get", "NAME,group(B01001)"),
            ("for", "tract:*"),
            ("in", "state:17 county:031"),
        ),
        "row_count": 2,
        "header_sha256": "b" * 64,
    }
    values.update(overrides)
    return SnapshotAcquisition.model_validate(values)


def test_manifest_without_acquisitions_remains_backward_compatible() -> None:
    assert valid_manifest().acquisitions == ()


def test_snapshot_acquisition_is_immutable_and_revalidates_copies() -> None:
    acquisition = valid_acquisition()

    with pytest.raises(ValidationError):
        acquisition.group = "B17001"  # type: ignore[misc]
    with pytest.raises(ValidationError, match="parameters"):
        acquisition.model_copy(update={"parameters": (("key", "secret"),)})


@pytest.mark.parametrize(
    "overrides",
    [
        {"url": "https://api.census.gov/data?api_key=manifest-secret"},
        {"parameters": (("api_key", "manifest-secret"),)},
        {"parameters": {"api_key": "manifest-secret"}},
    ],
)
def test_snapshot_acquisition_rejects_and_redacts_credentials(
    overrides: dict[str, object],
) -> None:
    with pytest.raises(ValidationError) as captured:
        valid_acquisition(**overrides)

    assert "manifest-secret" not in str(captured.value)
    assert "manifest-secret" not in captured.value.json()


def test_source_spec_requires_authoritative_origin() -> None:
    spec = valid_source_spec()

    assert spec.source_id == "census_acs_2024_5y"


@pytest.mark.parametrize(
    "field",
    [
        "organization",
        "dataset_title",
        "landing_url",
        "documentation_url",
        "license",
        "snapshot_subdir",
    ],
)
def test_source_spec_rejects_missing_authority_field(field: str) -> None:
    with pytest.raises(ValidationError):
        valid_source_spec(**{field: None})


@pytest.mark.parametrize("field", ["organization", "dataset_title", "license"])
def test_source_spec_rejects_blank_authority_text(field: str) -> None:
    with pytest.raises(ValidationError):
        valid_source_spec(**{field: "   "})


@pytest.mark.parametrize(
    "source_id",
    ["Census_ACS", "census-acs", "census acs", "census.acs", "census/acs"],
)
def test_source_spec_rejects_malformed_source_identifier(source_id: str) -> None:
    with pytest.raises(ValidationError, match="source_id"):
        valid_source_spec(source_id=source_id)


def test_source_spec_accepts_lowercase_letters_digits_and_underscores() -> None:
    assert valid_source_spec(source_id="acs_2024_5y").source_id == "acs_2024_5y"


@pytest.mark.parametrize("snapshot_subdir", ["/tmp/raw", "../raw", "raw/../../secret"])
def test_source_spec_rejects_snapshot_subdir_outside_repository(snapshot_subdir: str) -> None:
    with pytest.raises(ValidationError, match="snapshot_subdir"):
        valid_source_spec(snapshot_subdir=snapshot_subdir)


@pytest.mark.parametrize(
    ("field", "url"),
    [
        ("landing_url", "https://user:password@example.org/data"),
        ("documentation_url", "https://example.org/docs?API_KEY=secret"),
        ("landing_url", "https://example.org/data?access-token=secret"),
        ("documentation_url", "https://example.org/docs?Authorization=secret"),
    ],
)
def test_source_spec_rejects_credentials_in_urls(field: str, url: str) -> None:
    with pytest.raises(ValidationError, match=field):
        valid_source_spec(**{field: url})


@pytest.mark.parametrize("field", ["landing_url", "documentation_url"])
@pytest.mark.parametrize(
    "parameter",
    [
        "x-api-key",
        "subscription-key",
        "private-key",
        "API_KEY",
        "access-token",
        "Authorization",
    ],
)
def test_source_spec_rejects_normalized_credential_query_names(field: str, parameter: str) -> None:
    with pytest.raises(ValidationError, match=field):
        valid_source_spec(**{field: f"https://example.org/data?{parameter}=sensitive"})


def test_transport_exposes_supported_values() -> None:
    assert {transport.value for transport in Transport} == {
        "local",
        "census_api",
        "socrata",
        "arcgis",
        "http_file",
        "documented_export",
    }


@pytest.mark.parametrize("header", ["authorization", "Authorization", "x-api-key", "cookie"])
def test_request_record_rejects_secret_headers(header: str) -> None:
    with pytest.raises(ValidationError, match="headers"):
        RequestRecord(method="GET", url="https://example.org/data", headers={header: "secret"})


@pytest.mark.parametrize("field", ["authorization", "api_key", "password", "token"])
def test_request_record_rejects_credential_fields(field: str) -> None:
    with pytest.raises(ValidationError):
        RequestRecord.model_validate(
            {"method": "GET", "url": "https://example.org/data", field: "secret"}
        )


@pytest.mark.parametrize("parameter", ["key", "api_key", "access_token", "password"])
def test_request_record_rejects_secret_query_parameters(parameter: str) -> None:
    with pytest.raises(ValidationError, match="query"):
        RequestRecord(
            method="GET",
            url="https://example.org/data",
            query={parameter: "secret"},
        )


def test_request_record_keeps_non_secret_request_metadata() -> None:
    record = RequestRecord(
        method="get",
        url="https://example.org/data",
        query={"year": "2024"},
        headers={"accept": "application/json"},
    )

    assert record.method == "GET"
    assert record.query == {"year": "2024"}


@pytest.mark.parametrize(
    "url",
    [
        "https://user:password@example.org/data",
        "https://example.org/data?api_key=secret",
        "https://example.org/data?TOKEN=secret",
        "https://example.org/data?access-token=secret",
        "https://example.org/data?password=secret",
        "https://example.org/data?secret=secret",
        "https://example.org/data?authorization=secret",
    ],
)
def test_request_record_rejects_credentials_in_url(url: str) -> None:
    with pytest.raises(ValidationError, match="url"):
        RequestRecord(method="GET", url=url)


@pytest.mark.parametrize(
    "parameter",
    [
        "x-api-key",
        "subscription-key",
        "private-key",
        "API_KEY",
        "access-token",
        "Authorization",
    ],
)
def test_request_record_rejects_normalized_credential_query_names(parameter: str) -> None:
    with pytest.raises(ValidationError, match="url"):
        RequestRecord(method="GET", url=f"https://example.org/data?{parameter}=sensitive")


def test_url_validation_error_does_not_log_credential_value() -> None:
    credential = "do-not-log-this-credential"

    with pytest.raises(ValidationError) as error:
        RequestRecord(method="GET", url=f"https://example.org/data?token={credential}")

    assert credential not in str(error.value)


def assert_error_redacts_url(error: ValidationError, raw_url: str, credential: str) -> None:
    renderings = (str(error), repr(error.errors()), error.json())
    for rendering in renderings:
        assert credential not in rendering
        assert raw_url not in rendering


@pytest.mark.parametrize("construction", ["init", "model_validate", "model_copy"])
def test_request_url_structured_errors_redact_raw_credentials(construction: str) -> None:
    credential = "request-credential-must-not-leak"
    raw_url = f"https://example.org/data?api_key={credential}"

    with pytest.raises(ValidationError) as captured:
        if construction == "init":
            RequestRecord(method="GET", url=raw_url)
        elif construction == "model_validate":
            RequestRecord.model_validate({"method": "GET", "url": raw_url})
        else:
            RequestRecord(method="GET", url="https://example.org/data").model_copy(
                update={"url": raw_url}
            )

    assert captured.value.errors()[0]["loc"] == ("url",)
    assert_error_redacts_url(captured.value, raw_url, credential)


@pytest.mark.parametrize("field", ["landing_url", "documentation_url"])
def test_source_url_structured_errors_redact_raw_credentials(field: str) -> None:
    credential = "source-credential-must-not-leak"
    raw_url = f"https://example.org/data?API_KEY={credential}"

    with pytest.raises(ValidationError) as captured:
        valid_source_spec(**{field: raw_url})

    assert captured.value.errors()[0]["loc"] == (field,)
    assert_error_redacts_url(captured.value, raw_url, credential)


@pytest.mark.parametrize("field", ["headers", "query"])
@pytest.mark.parametrize("construction", ["init", "model_validate", "model_copy"])
def test_request_mapping_structured_errors_redact_credentials(
    field: str, construction: str
) -> None:
    credential = f"{field}-secret-must-not-leak"
    mapping = {"authorization": credential} if field == "headers" else {"api_key": credential}
    values = {"method": "GET", "url": "https://example.org/data", field: mapping}

    with pytest.raises(ValidationError) as captured:
        if construction == "init":
            RequestRecord(**values)
        elif construction == "model_validate":
            RequestRecord.model_validate(values)
        else:
            RequestRecord(method="GET", url="https://example.org/data").model_copy(
                update={field: mapping}
            )

    assert captured.value.errors()[0]["loc"] == (field,)
    assert_error_redacts_url(captured.value, repr(mapping), credential)


@pytest.mark.parametrize("construction", ["init", "model_validate", "model_copy"])
def test_malformed_request_url_structured_errors_redact_credentials(construction: str) -> None:
    credential = "malformed-secret-must-not-leak"
    raw_url = f"https://[invalid?token={credential}"
    values = {"method": "GET", "url": raw_url}

    with pytest.raises(ValidationError) as captured:
        if construction == "init":
            RequestRecord(**values)
        elif construction == "model_validate":
            RequestRecord.model_validate(values)
        else:
            RequestRecord(method="GET", url="https://example.org/data").model_copy(
                update={"url": raw_url}
            )

    assert captured.value.errors()[0]["loc"] == ("url",)
    assert_error_redacts_url(captured.value, raw_url, credential)


def test_request_record_metadata_cannot_be_mutated_after_validation() -> None:
    record = RequestRecord(
        method="GET",
        url="https://example.org/data",
        query={"year": "2024"},
        headers={"accept": "application/json"},
    )

    with pytest.raises(TypeError):
        record.query["key"] = "secret"
    with pytest.raises(TypeError):
        record.headers["authorization"] = "secret"


def test_request_record_rejects_dict_descriptor_mutation_bypass() -> None:
    record = RequestRecord(
        method="GET",
        url="https://example.org/data",
        headers={"accept": "application/json"},
    )

    with pytest.raises(TypeError):
        dict.__setitem__(record.headers, "authorization", "secret")


def test_request_record_rejects_mapping_backing_store_reassignment() -> None:
    record = RequestRecord(method="GET", url="https://example.org/data")

    with pytest.raises((AttributeError, TypeError)):
        setattr(record.headers, "_items", (("authorization", "secret"),))


def test_request_record_rejects_object_setattr_backing_store_attack() -> None:
    record = RequestRecord(method="GET", url="https://example.org/data")

    with pytest.raises((AttributeError, TypeError)):
        object.__setattr__(record.headers, "_items", (("authorization", "secret"),))


def test_request_record_model_copy_revalidates_updates() -> None:
    record = RequestRecord(method="GET", url="https://example.org/data")

    with pytest.raises(ValidationError, match="headers"):
        record.model_copy(update={"headers": {"authorization": "secret"}})
    with pytest.raises(ValidationError, match="url"):
        record.model_copy(update={"url": "https://example.org/data?token=secret"})


def test_request_record_immutable_mappings_serialize_as_objects() -> None:
    record = RequestRecord(
        method="GET",
        url="https://example.org/data?year=2024",
        query={"year": "2024"},
        headers={"accept": "application/json"},
    )

    assert record.model_dump(mode="json")["headers"] == {"accept": "application/json"}
    assert json.loads(record.model_dump_json())["query"] == {"year": "2024"}


def test_request_record_deep_copy_revalidates_independent_immutable_mappings() -> None:
    record = RequestRecord(
        method="GET",
        url="https://example.org/data",
        query={"year": "2024"},
        headers={"accept": "application/json"},
    )

    copied = record.model_copy(deep=True)

    assert copied == record
    assert copied is not record
    assert copied.query is not record.query
    assert copied.headers is not record.headers
    with pytest.raises(TypeError):
        copied.query["key"] = "secret"


@pytest.mark.parametrize(
    "snapshot_date", ["2024-1-02", "01/02/2024", "20240102", "2024-01-02T00:00:00Z"]
)
def test_snapshot_date_requires_iso_calendar_format(snapshot_date: str) -> None:
    with pytest.raises(ValidationError, match="snapshot_date"):
        valid_manifest(snapshot_date=snapshot_date)


def test_snapshot_manifest_contains_file_integrity_and_counts() -> None:
    manifest = valid_manifest()

    assert manifest.files == (
        SnapshotFile(
            path="response.json",
            sha256="a" * 64,
            byte_count=128,
            row_count=3,
            page_count=None,
        ),
    )
    assert manifest.validation_status is ValidationStatus.passed


@pytest.mark.parametrize(
    "sha256",
    ["a" * 63, "a" * 65, "A" * 64, "g" * 64, "sha256:" + "a" * 64],
)
def test_snapshot_file_requires_lowercase_sha256(sha256: str) -> None:
    with pytest.raises(ValidationError, match="sha256"):
        SnapshotFile(path="response.json", sha256=sha256, byte_count=1)


@pytest.mark.parametrize("path", ["/tmp/response.json", "../response.json", "raw/../../secret"])
def test_snapshot_file_path_must_be_repository_relative(path: str) -> None:
    with pytest.raises(ValidationError, match="path"):
        SnapshotFile(path=path, sha256="a" * 64, byte_count=1)


@pytest.mark.parametrize(
    "path",
    [r"..\secret", r"raw\..\secret", r"C:\raw\response.json", r"C:raw", r"raw\file.json"],
)
def test_repository_relative_paths_reject_windows_forms(path: str) -> None:
    with pytest.raises(ValidationError, match="snapshot_subdir"):
        valid_source_spec(snapshot_subdir=path)
    with pytest.raises(ValidationError, match="path"):
        SnapshotFile(path=path, sha256="a" * 64, byte_count=1)


def test_snapshot_manifest_rejects_completion_before_start() -> None:
    with pytest.raises(ValidationError, match="retrieval_completed_at"):
        valid_manifest(
            retrieval_started_at=datetime(2024, 12, 19, 14, 1, tzinfo=timezone.utc),
            retrieval_completed_at=datetime(2024, 12, 19, 14, 0, tzinfo=timezone.utc),
        )
