"""Bounded, retry-aware HTTP acquisition into immutable raw snapshots."""

from __future__ import annotations

import json
import math
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import unquote, urlsplit, urlunsplit

import httpx

from chicagohealthmap.sources.adapters.base import AcquisitionPlan
from chicagohealthmap.sources.models import (
    RequestRecord,
    SnapshotManifest,
    _is_credential_name,
    _is_secret_header_name,
)
from chicagohealthmap.sources.registry import RegistrySource
from chicagohealthmap.sources.snapshot import SnapshotWriter

HTTP_TIMEOUT = httpx.Timeout(connect=20.0, read=120.0, write=120.0, pool=20.0)
RETRYABLE_STATUSES = frozenset({408, 425, 429, 500, 502, 503, 504})
MAX_ATTEMPTS = 5
MAX_BACKOFF_SECONDS = 60.0
DEFAULT_MAX_RESPONSE_BYTES = 512 * 1024 * 1024


class AcquisitionError(RuntimeError):
    """Disclosure-safe failure raised by public HTTP acquisition."""


@dataclass(frozen=True, slots=True)
class JsonPagination:
    """Offset pagination contract for a top-level JSON row sequence."""

    parameter: str
    page_size: int
    expected_total_rows: int | None = None
    page_size_parameter: str | None = None
    start: int = 0
    max_pages: int = 10_000

    def __post_init__(self) -> None:
        if (
            not self.parameter
            or self.page_size <= 0
            or self.start < 0
            or self.max_pages <= 0
            or (self.expected_total_rows is not None and self.expected_total_rows < 0)
        ):
            raise ValueError("invalid JSON pagination contract")


def redacted_request_record(
    *,
    method: str,
    url: str,
    query: Iterable[tuple[str, str]] = (),
    headers: Iterable[tuple[str, str]] = (),
) -> RequestRecord:
    """Return persistable request metadata after dropping every credential field."""
    parts = urlsplit(url)
    sanitized_url = urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    safe_query = {name: value for name, value in query if not _is_credential_name(name)}
    safe_headers = {name: value for name, value in headers if not _is_secret_header_name(name)}
    return RequestRecord.model_validate(
        {"method": method, "url": sanitized_url, "query": safe_query, "headers": safe_headers}
    )


def _destination_name(source: RegistrySource) -> str:
    name = unquote(Path(urlsplit(str(source.endpoint_url)).path).name)
    if not name or name in {".", ".."}:
        name = "download"
    return f"original/{name}"


def _content_type(response: httpx.Response) -> str:
    return response.headers.get("content-type", "").partition(";")[0].strip().casefold()


def _json_rows(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("results", "data"):
            rows = value.get(key)
            if isinstance(rows, list):
                return rows
    raise AcquisitionError("JSON response does not contain a supported row sequence")


class HttpAcquirer:
    """Acquire one validated registry source without buffering response bytes in memory."""

    def __init__(
        self,
        *,
        client: httpx.Client | None = None,
        expected_content_types: Sequence[str] = (),
        pagination: JsonPagination | None = None,
        required_environment_variables: Sequence[str] = (),
        credential_headers: Mapping[str, str] | None = None,
        credential_query: Mapping[str, str] | None = None,
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
        sleep: Callable[[float], None] = time.sleep,
        now: Callable[[], datetime] = lambda: datetime.now(timezone.utc),
    ) -> None:
        if max_response_bytes <= 0:
            raise ValueError("max_response_bytes must be positive")
        if credential_query is not None and any(
            not _is_credential_name(name) for name in credential_query
        ):
            raise ValueError("credential_query accepts only credential-named fields")
        if credential_headers is not None and any(
            not _is_secret_header_name(name) for name in credential_headers
        ):
            raise ValueError("credential_headers accepts only credential header fields")
        self._client = client
        self._expected_content_types = tuple(item.casefold() for item in expected_content_types)
        self._pagination = pagination
        self._required_environment_variables = tuple(required_environment_variables)
        self._credential_headers = dict(credential_headers or {})
        self._credential_query = dict(credential_query or {})
        self._max_response_bytes = max_response_bytes
        self._sleep = sleep
        self._now = now

    def plan(self, source: RegistrySource) -> AcquisitionPlan:
        """Build display-safe deterministic metadata without resolving credentials."""
        destination = (
            "original/page-0001.json" if self._pagination is not None else _destination_name(source)
        )
        request_count = None
        if self._pagination is None:
            request_count = 1
        elif self._pagination.expected_total_rows is not None:
            request_count = max(
                1,
                math.ceil(self._pagination.expected_total_rows / self._pagination.page_size),
            )
        return AcquisitionPlan(
            source_id=source.source_id,
            url=source.endpoint_url,
            parameters=tuple(source.request.parameters.items()),
            transport=source.transport,
            destination_paths=(destination,),
            required_environment_variables=self._required_environment_variables,
            estimated_request_count=request_count,
            fallback_status=source.fallback.status,
        )

    def _retry_delay(self, response: httpx.Response | None, attempt: int) -> float:
        fallback = min(float(2 ** (attempt - 1)), MAX_BACKOFF_SECONDS)
        if response is None:
            return fallback
        value = response.headers.get("retry-after")
        if value is None:
            return fallback
        try:
            numeric = float(value)
            if not math.isfinite(numeric) or numeric < 0:
                return fallback
            return min(numeric, MAX_BACKOFF_SECONDS)
        except ValueError:
            try:
                target = parsedate_to_datetime(value)
                if target.tzinfo is None:
                    target = target.replace(tzinfo=timezone.utc)
                seconds = (target - self._now()).total_seconds()
                if not math.isfinite(seconds):
                    return fallback
                return min(max(seconds, 0.0), MAX_BACKOFF_SECONDS)
            except (TypeError, ValueError, OverflowError):
                return fallback

    def _bounded_chunks(self, response: httpx.Response) -> Iterable[bytes]:
        raw_length = response.headers.get("content-length")
        if raw_length is not None:
            try:
                content_length = int(raw_length)
            except ValueError as error:
                raise AcquisitionError("response has an invalid Content-Length") from error
            if content_length < 0 or content_length > self._max_response_bytes:
                raise AcquisitionError("response exceeds configured byte limit")
        observed = 0
        for chunk in response.iter_bytes():
            observed += len(chunk)
            if observed > self._max_response_bytes:
                raise AcquisitionError("response exceeds configured byte limit")
            yield chunk

    def request_bytes(
        self,
        *,
        method: str,
        url: str,
        query: Sequence[tuple[str, str]] = (),
        headers: Mapping[str, str] | None = None,
        response_metadata: dict[str, str] | None = None,
    ) -> bytes:
        """Return one bounded response using the canonical retry and timeout contract.

        This is the shared JSON/API boundary for adapters that must validate a complete
        response before writing source-faithful bytes to a snapshot.
        """
        runtime_headers = {**self._credential_headers, **dict(headers or {})}
        owns_client = self._client is None
        client = self._client or httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=False)
        transport_exhausted = False
        try:
            for attempt in range(1, MAX_ATTEMPTS + 1):
                response: httpx.Response | None = None
                try:
                    with client.stream(
                        method,
                        url,
                        params=dict(query),
                        headers=runtime_headers,
                        timeout=HTTP_TIMEOUT,
                        follow_redirects=False,
                    ) as response:
                        if response.status_code in RETRYABLE_STATUSES:
                            if attempt == MAX_ATTEMPTS:
                                raise AcquisitionError(
                                    f"HTTP {response.status_code} after {MAX_ATTEMPTS} attempts"
                                )
                            delay = self._retry_delay(response, attempt)
                        elif 300 <= response.status_code < 400:
                            raise AcquisitionError(
                                f"HTTP {response.status_code}; redirects are disabled"
                            )
                        elif 400 <= response.status_code < 500:
                            raise AcquisitionError(
                                f"HTTP {response.status_code}; request not retried"
                            )
                        elif response.status_code >= 400:
                            raise AcquisitionError(f"HTTP {response.status_code}; request failed")
                        else:
                            observed_type = _content_type(response)
                            if (
                                self._expected_content_types
                                and observed_type not in self._expected_content_types
                            ):
                                raise AcquisitionError(
                                    "unexpected response content type "
                                    f"{observed_type or '<missing>'}"
                                )
                            content = b"".join(self._bounded_chunks(response))
                            if not content:
                                raise AcquisitionError("zero-byte response is not publishable")
                            if response_metadata is not None:
                                response_metadata.clear()
                                response_metadata.update(
                                    {
                                        "resolved_url": str(response.url),
                                        "content_type": observed_type,
                                        "content_length": response.headers.get(
                                            "content-length", ""
                                        ),
                                        "etag": response.headers.get("etag", ""),
                                        "last_modified": response.headers.get("last-modified", ""),
                                    }
                                )
                            return content
                except httpx.RequestError:
                    if attempt == MAX_ATTEMPTS:
                        transport_exhausted = True
                        break
                    delay = self._retry_delay(None, attempt)
                self._sleep(delay)
            if transport_exhausted:
                raise AcquisitionError(
                    f"HTTP transport failed after {MAX_ATTEMPTS} attempts"
                ) from None
            raise AcquisitionError("HTTP request failed")
        finally:
            if owns_client:
                client.close()

    def _request_to_file(
        self,
        source: RegistrySource,
        writer: SnapshotWriter,
        relative_path: str,
        extra_query: Sequence[tuple[str, str]],
    ) -> None:
        query = [*source.request.parameters.items(), *extra_query, *self._credential_query.items()]
        headers = list(self._credential_headers.items())
        owns_client = self._client is None
        client = self._client or httpx.Client(timeout=HTTP_TIMEOUT)
        transport_exhausted = False
        try:
            for attempt in range(1, MAX_ATTEMPTS + 1):
                response: httpx.Response | None = None
                try:
                    with client.stream(
                        source.request.method,
                        str(source.request.url),
                        params=dict(query),
                        headers=headers,
                        timeout=HTTP_TIMEOUT,
                        follow_redirects=False,
                    ) as response:
                        if response.status_code in RETRYABLE_STATUSES:
                            if attempt == MAX_ATTEMPTS:
                                raise AcquisitionError(
                                    f"HTTP {response.status_code} after {MAX_ATTEMPTS} attempts"
                                )
                            delay = self._retry_delay(response, attempt)
                        elif 300 <= response.status_code < 400:
                            raise AcquisitionError(
                                f"HTTP {response.status_code}; redirects are disabled"
                            )
                        elif 400 <= response.status_code < 500:
                            raise AcquisitionError(
                                f"HTTP {response.status_code}; request not retried"
                            )
                        elif response.status_code >= 400:
                            raise AcquisitionError(f"HTTP {response.status_code}; request failed")
                        else:
                            observed_type = _content_type(response)
                            if (
                                self._expected_content_types
                                and observed_type not in self._expected_content_types
                            ):
                                raise AcquisitionError(
                                    f"unexpected response content type {observed_type or '<missing>'}"
                                )
                            record = writer.write_chunks(
                                relative_path, self._bounded_chunks(response)
                            )
                            if record.byte_count == 0:
                                raise AcquisitionError("zero-byte response is not publishable")
                            return
                except httpx.RequestError:
                    if attempt == MAX_ATTEMPTS:
                        transport_exhausted = True
                        break
                    delay = self._retry_delay(None, attempt)
                self._sleep(delay)
            if transport_exhausted:
                raise AcquisitionError(f"HTTP transport failed after {MAX_ATTEMPTS} attempts")
        finally:
            if owns_client:
                client.close()

    def fetch(self, source: RegistrySource, writer: SnapshotWriter) -> SnapshotManifest:
        """Fetch, validate, and atomically finalize one source snapshot."""
        try:
            if self._pagination is None:
                self._request_to_file(source, writer, _destination_name(source), ())
                return writer.finalize()

            total_rows = 0
            for page_number in range(1, self._pagination.max_pages + 1):
                offset = self._pagination.start + total_rows
                extra_query = [(self._pagination.parameter, str(offset))]
                if self._pagination.page_size_parameter is not None:
                    extra_query.append(
                        (self._pagination.page_size_parameter, str(self._pagination.page_size))
                    )
                relative_path = f"original/page-{page_number:04d}.json"
                self._request_to_file(source, writer, relative_path, extra_query)
                try:
                    payload = json.loads((writer.staging_path / relative_path).read_text("utf-8"))
                except (OSError, UnicodeError, json.JSONDecodeError) as error:
                    raise AcquisitionError("malformed JSON response") from error
                rows = _json_rows(payload)
                writer.annotate_file(relative_path, row_count=len(rows), page_count=1)
                total_rows += len(rows)
                if (
                    len(rows) < self._pagination.page_size
                    or self._pagination.expected_total_rows is not None
                    and total_rows >= self._pagination.expected_total_rows
                ):
                    break
            else:
                raise AcquisitionError("JSON pagination exceeded configured page limit")

            expected = self._pagination.expected_total_rows
            if expected is not None and total_rows != expected:
                raise AcquisitionError(f"expected {expected} rows; received {total_rows}")
            return writer.finalize()
        except BaseException:
            writer.cleanup()
            raise
