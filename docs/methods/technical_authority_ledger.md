# Technical authority ledger

## 2026-07-14 — ArcGIS registered-ID acquisition and catalog bulk-file integrity

- **Ref MCP result:** Ref returned Esri's official
  [Query features paging example](https://developers.arcgis.com/documentation/portal-and-data-services/data-services/feature-services/query-features/#sql-parameters#query-features-with-paging),
  accessed 2026-07-14. The floating Esri Developer page documents a layer URL/ID,
  `resultRecordCount`, `resultOffset`, and explicit object-ID ordering. It does not declare a
  numbered REST API release on the returned page.
- **Official and installed fallback:** the Task 11 registry retains the exact official HRSA
  layer identity
  `PrimaryHealthCareFacilities_FS/MapServer/0`; the frozen registry evidence recorded layer 0's
  `maxRecordCount` as 2000. HTTP behavior uses installed HTTPX 0.28.1 and the repository's
  shared `HttpAcquirer` boundary: bounded streaming, fixed timeout policy, five-attempt
  transient retry allowlist, and redirects disabled.
- **Decision supported:** bind the adapter to the exact registry source, catalog ID, fallback
  service URL, authoritative domains, layer 0, layer name `Health Care Service Delivery Sites`,
  OID field `OBJECTID`, and `maxRecordCount` 2000. Request layer metadata before data and the complete object-ID
  universe with `where=1=1`; then request at most `maxRecordCount` sorted IDs per page with
  `outFields=*`, explicit object-ID order, and geometry only when registered. Duplicate, missing,
  extra, malformed, non-finite-geometry, over-limit, or out-of-order results are fatal. A response
  that remains transfer-limited is accepted only when that page contains the complete exact
  registered-ID slice; otherwise it is fatal.
- **Official bulk rule:** only the registry's exact HTTPS endpoint and authoritative hostname are
  accepted. Redirects and resolved-URL drift are fatal. The registry declares exact media types
  and required response headers; generic octet-stream is not accepted. A syntactically valid
  strong quoted `ETag` is mandatory and weak `W/` validators are rejected. Parseable
  timezone-aware HTTP-date `Last-Modified`, positive bounded `Content-Length`, observed byte length, and
  SHA-256 are written to `requests/acquisition.json`, which is itself included in the immutable
  snapshot manifest. `SnapshotWriter` publishes by atomic no-replace; changed bytes at the same
  URL therefore require a new snapshot date and cannot overwrite a finalized date.
- **Frozen compatibility:** the 2026-07-13 public artifacts predate canonical per-source snapshot
  directories. The verifier maps the four Task 15 source IDs to the historical
  `chicago_health_atlas`, `cdc_atsdr_svi`, and `hrsa_health_centers` family directories, checks the
  repository-wide checksum inventory against hardcoded exact family counts/digests and rejects
  symlinks at every checked component before reads. It binds Atlas periods and the 77-ID universe,
  corrected SVI schema/3,263-ID universe, and HRSA schema/18,940 composite-ID universe to compact
  tracked hashes, then performs field semantics validation without freezing analytical values. This compatibility
  mapping is deliberate and does not authorize inferred endpoints or mutation of legacy files.
- **Affected code:** `src/chicagohealthmap/sources/adapters/catalog.py`,
  `src/chicagohealthmap/cli.py`, `tests/unit/sources/adapters/test_catalog.py`,
  `tests/integration/sources/test_catalog_snapshot.py`, and
  `tests/integration/sources/test_acquisition_cli.py`.

## 2026-07-14 — Socrata SODA paging, counting, and application-token handling

- **Ref MCP result:** Ref was queried for official Socrata SODA documentation covering
  `/api/views/<id>`, `$limit`, `$offset`, `$order`, `count(*)`, and `X-App-Token`. It returned
  only the `socrata/socrata-py` repository's library-output-schema pages, which do not define
  the consumer API contract used here. The result was therefore insufficient and was not used
  as authority.
- **Official fallback:** Socrata's [Paging through Data](https://dev.socrata.com/docs/paging.html),
  [LIMIT clause](https://dev.socrata.com/docs/queries/limit.html),
  [`count(...)`](https://dev.socrata.com/docs/functions/count), and
  [consumer API introduction](https://dev.socrata.com/consumers/getting-started) were accessed
  2026-07-14. These are floating official Tyler/Socrata pages rather than a numbered release.
  They document `$limit`/`$offset` paging, the need for explicit `$order` to keep pages stable,
  the 50,000-row SODA 2.0 page maximum, count aggregation, and lower anonymous rate limits with
  an optional application token.
- **Installed runtime:** HTTPX 0.28.1 and Shapely 2.1.2. The adapter delegates to the shared
  `HttpAcquirer.request_bytes` boundary: fixed 20/120/120/20-second timeouts, exact transient
  retries (at most five attempts), bounded `Retry-After`, redirects disabled even on injected
  clients, streaming byte limits before buffering, and exact content-type allowlists. Shapely
  parses GeoJSON before publication; geometry must be valid, nonempty, polygonal, and finite.
- **Decision supported:** fetch and validate `/api/views/<id>` before rows; require the exact
  registered ID, title, selected schema, primary key, update timestamp, license, department,
  and geometry type; issue a separate filtered `count(*) AS count`; fetch pages with
  `$limit=50000`, offsets `0, 50000, ...`, and the registered primary-key order; require the
  count to equal both fetched rows and unique keys. PLACES rows require the exact selected fields,
  Cook County/Illinois-consistent 11-digit tract GEOIDs, and finite registered model estimates;
  Chicago requires the exact properties and area IDs 1 through 77. `SOCRATA_APP_TOKEN` is sent
  only as `X-App-Token` at runtime and is absent from plans, requests manifests, exceptions, and
  snapshot bytes.
- **Affected code:** `config/source_registry.yml`,
  `src/chicagohealthmap/sources/adapters/socrata.py`, `src/chicagohealthmap/cli.py`,
  `tests/unit/sources/adapters/test_socrata.py`,
  `tests/integration/sources/test_socrata_snapshot.py`, and
  `tests/integration/sources/test_acquisition_cli.py`.

## 2026-07-14 — bounded HTTP acquisition and retry behavior

- **Ref MCP result:** one combined HTTPX/Tenacity documentation search returned official HTTPX
  project documentation for the four timeout classes and streaming responses. The adopted pages
  were the HTTPX repository's `docs/advanced/timeouts.md` fine-tuning section,
  <https://github.com/encode/httpx/blob/master/docs/advanced/timeouts.md#fine-tuning-the-configuration>,
  and `docs/compatibility.md` streaming-response section,
  <https://github.com/encode/httpx/blob/master/docs/compatibility.md#streaming-responses>, both
  accessed 2026-07-14. Ref returned no Tenacity document for the combined query; that absence is
  retained rather than silently presented as a successful Tenacity lookup.
- **Installed-version fallback:** local installed API help was inspected for `httpx.Timeout` and
  `tenacity.Retrying` on 2026-07-14. Installed versions were HTTPX 0.28.1 and Tenacity 9.1.4.
  HTTPX's installed signature accepts separate `connect`, `read`, `write`, and `pool` values.
  Tenacity's installed controller accepts configurable sleep, stop, wait, and retry strategies.
- **Decision supported:** use `httpx.Client.stream()` and `Response.iter_bytes()` with fixed
  connect/read/write/pool timeouts of 20/120/120/20 seconds. Retry transport failures and exactly
  HTTP 408, 425, 429, 500, 502, 503, and 504 for no more than five total attempts; cap exponential
  delay and numeric or HTTP-date `Retry-After` at 60 seconds. Other 4xx responses are terminal.
- **Tenacity adoption decision:** the generic retry library is retained in the locked environment
  but is not used by this engine. An explicit five-attempt response loop makes the exact status
  allowlist, safe `Retry-After` parsing, response-context closure, and injected no-sleep tests
  directly auditable. This is narrower than Tenacity's default exception retry behavior.
- **Affected code:** `src/chicagohealthmap/sources/http.py`,
  `src/chicagohealthmap/sources/snapshot.py`, `src/chicagohealthmap/cli.py`,
  `tests/unit/sources/test_http.py`, and
  `tests/integration/sources/test_acquisition_cli.py`.

## 2026-07-14 — strict pipe ingestion and Parquet publication

- **Authority attempt:** Ref MCP was queried for version-specific pandas and PyArrow
  documentation. The request failed with `OAuth authorization required`; no Ref result
  was used.
- **Official fallback:** pandas `read_csv` API documentation,
  <https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html>, accessed
  2026-07-14, when the page identified itself as pandas 3.0.4. This `/docs/` URL is the
  official current-release location and therefore floats. The attempted exact-version
  path
  `https://pandas.pydata.org/pandas-docs/version/3.0.3/reference/api/pandas.read_csv.html`
  returned HTTP 404 on 2026-07-14, so a nonexistent version URL is not recorded as an
  authority. The relevant contract is explicit header/name handling, declared dtypes,
  a literal missing-value vocabulary with default NA recognition disabled, strict UTF-8
  decoding, and errors for malformed rows. The implementation uses a smaller standard-
  library parser with those same fail-closed rules because it must attach exact one-based
  source-row provenance before dataframe construction.
- **Official fallback:** Apache Arrow Python Parquet guide,
  <https://arrow.apache.org/docs/python/parquet.html>, accessed 2026-07-14. The adopted
  contract is `Table.from_pandas(..., preserve_index=False)` followed by
  `pyarrow.parquet.write_table`, only after complete parsing and key validation. The
  page identified itself as v24.0.0 and is the official current-release URL; it floats.
  The attempted installed-version path
  `https://arrow.apache.org/docs/25.0/python/parquet.html` returned HTTP 404 on
  2026-07-14 because installed PyArrow 25.0.0 was ahead of the published stable guide.
- **Installed runtime:** pandas 3.0.3 and PyArrow 25.0.0. The official pages available
  during the fallback lookup did not exactly match both installed versions, so adopted
  calls are limited to stable documented interfaces and are exercised against the
  installed versions by unit tests.
- **Decision supported:** preserve string identifiers, accept only literal `\N` as
  missing, reject malformed UTF-8/rows/typed values, add source provenance, and publish
  Parquet only after validation.
- **Local lexical contract:** floats use finite decimal/scientific notation only;
  timestamps require
  `YYYY-MM-DDTHH:MM:SS[.1-6 fractional digits](Z|±HH:MM)` and are normalized to UTC.
  This deliberately excludes Python numeric extensions, nonfinite values, date-only or
  locale-dependent timestamps, relative time words, and timestamps without a zone.
- **Affected code:** `src/chicagohealthmap/ingest/pipe.py`,
  `tests/unit/ingest/test_pipe.py`.

The Ref failure is retained as research-tool provenance rather than silently replacing
the requested authority source.

## 2026-07-14 — Census TIGER inspection and source-faithful GeoParquet

- **Authority attempt:** Ref MCP was queried for version-specific Pyogrio 0.13
  `read_info`, ZIP/Shapefile inspection, and Arrow-backed reads. It returned no results.
  This failed lookup is retained; it is not represented as a successful Ref citation.
- **Official fallback:** the Pyogrio
  [API reference](https://pyogrio.readthedocs.io/en/latest/api.html), accessed
  2026-07-14, documents `read_info(..., force_feature_count=True)` returning the CRS,
  fields, geometry type, and feature count and `read_dataframe(..., use_arrow=True)`
  returning a GeoDataFrame. The floating page identified itself as a development build,
  so adoption was checked against installed Pyogrio 0.13.0 signatures and synthetic
  Shapefile/ZIP tests rather than assuming unreleased behavior.
- **Official fallback:** GeoPandas
  [`GeoDataFrame.to_parquet`](https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoDataFrame.to_parquet.html),
  accessed 2026-07-14, identified itself as GeoPandas 1.1.4 and documents GeoParquet
  output with WKB geometry by default. The Apache Arrow
  [Parquet guide](https://arrow.apache.org/docs/python/parquet.html), accessed
  2026-07-14, documents schema and file-metadata inspection; that floating guide was
  v24.0.0 while installed PyArrow is 25.0.0.
- **Installed runtime:** Pyogrio 0.13.0, GeoPandas 1.1.4, PyArrow 25.0.0, and Shapely
  2.1.2. Local signatures for `pyogrio.read_info`, `pyogrio.read_dataframe`,
  `pyogrio.write_dataframe`, and `GeoDataFrame.to_parquet` were inspected.
- **Decision supported:** inspect a CRC-clean, bounded, traversal/link/duplicate-safe
  official ZIP through GDAL's `/vsizip/` interface; require `STATEFP`, `COUNTYFP`,
  `TRACTCE`, `GEOID`, geometry, and CRS; validate statewide Illinois identifiers before
  filtering Cook County; and write an interim GeoParquet in the original CRS with only
  source identifiers and release provenance added. Reprojection, crosswalking, and
  analytical derivation remain outside the adapter.
- **Affected code:** `src/chicagohealthmap/sources/adapters/census.py`,
  `tests/unit/sources/adapters/test_census.py`, and
  `tests/integration/sources/test_census_snapshot.py`.

## 2026-07-14 — deterministic marimo Gate 3 review

- **Authority attempt:** Ref MCP remained unavailable because it required OAuth
  authorization; no Ref result was used.
- **Local fallback:** the installed marimo 0.23.14 CLI help and the bundled
  `marimo-notebook` and `marimo-batch` skill instructions were consulted on 2026-07-14.
  The adopted rules are a Python notebook with explicit reactive dependencies,
  `mo.app_meta().mode == "script"` for deterministic batch defaults, `mo.cli_args()` for
  optional path overrides, and `marimo check` before acceptance. The skill path was
  the locally configured `marimo-notebook` skill; batch conventions were
  read from the locally configured `marimo-batch` skill.
- **Decision supported:** use a thin presentation notebook that reads only the frozen
  disclosure-safe JSON checkpoint, writes a byte-stable Gate 3 decision, and runs
  unattended with repository-local defaults.
- **Documented plan/skill deviation:** Task 10 and the notebook skill recommend PEP 723
  metadata. This notebook intentionally omits it because an isolated dependency block
  listing marimo and pandas would be incomplete and misleading: the notebook imports the
  local `chicagohealthmap` package and must run against the repository code under review.
  The authoritative reproducibility contract is therefore `pyproject.toml` plus `uv.lock`,
  executed as `uv run notebooks/01_data_review.py` from the project environment. A future
  standalone distribution would require packaging the project itself, not duplicating a
  partial dependency list in the notebook.
- **I/O confinement:** both the checkpoint and decision paths must resolve strictly below
  the repository's real `outputs/quality` directory, and that directory must resolve to its
  canonical lexical absolute location. Direct external paths, the directory itself,
  repository source/raw paths, and quality-root or descendant symlink escapes fail before
  a decision is written.
- **Affected code:** `notebooks/01_data_review.py`,
  `src/chicagohealthmap/quality/views.py`,
  `tests/integration/test_data_review_notebook.py`.
