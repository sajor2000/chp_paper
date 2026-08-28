#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

# These modules verify frozen source snapshots that cannot be redistributed.
# They remain in the repository and run in the governed internal environment.
source_bound_tests=(
  tests/unit/analysis/test_raw_data_contract.py
  tests/unit/external/test_geography.py
  tests/unit/external/test_normalize.py
  tests/unit/ingest/test_schemas.py
  tests/unit/sources/adapters/test_catalog.py
  tests/unit/sources/adapters/test_socrata.py
  tests/unit/test_governance_readiness.py
  tests/unit/test_literature_artifacts.py
  tests/unit/test_literature_audit.py
  tests/unit/test_literature_screening.py
  tests/unit/test_s4_dictionary.py
)

pytest_args=(-q tests/unit)
for test_path in "${source_bound_tests[@]}"; do
  pytest_args+=(--ignore "$test_path")
done

uv run pytest "${pytest_args[@]}"
