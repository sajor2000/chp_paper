#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
artifact_dir="$repo_root/outputs/notebooks/chicago_healthmap_master"
archive_path="$artifact_dir/00_master_analytic_dataset.csv.gz"
output_path="$artifact_dir/00_master_analytic_dataset.csv"
expected_sha256="dc59dd5cef6a0671046b7666264084b8e4840165da67fee1e4b19091c4971dcf"

sha256_file() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  elif command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1" | awk '{print $1}'
  else
    echo "A SHA-256 utility is required." >&2
    return 1
  fi
}

if [[ ! -f "$archive_path" ]]; then
  echo "Missing release archive: $archive_path" >&2
  exit 1
fi

if [[ -f "$output_path" ]]; then
  observed_sha256="$(sha256_file "$output_path")"
  if [[ "$observed_sha256" == "$expected_sha256" ]]; then
    echo "Aggregate analytic CSV is already materialized and verified."
    exit 0
  fi
  echo "Existing analytic CSV has an unexpected SHA-256 digest. It was not overwritten." >&2
  exit 1
fi

temporary_path="$(mktemp "$artifact_dir/.00_master_analytic_dataset.csv.XXXXXX")"
cleanup() {
  rm -f -- "$temporary_path"
}
trap cleanup EXIT

gzip -dc -- "$archive_path" > "$temporary_path"
observed_sha256="$(sha256_file "$temporary_path")"
if [[ "$observed_sha256" != "$expected_sha256" ]]; then
  echo "Decompressed analytic CSV failed SHA-256 verification." >&2
  exit 1
fi

mv -- "$temporary_path" "$output_path"
trap - EXIT
echo "Materialized verified aggregate analytic CSV: $output_path"
