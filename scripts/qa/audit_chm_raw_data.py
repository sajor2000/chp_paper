#!/usr/bin/env python3
"""Run the study-specific ChicagoHealthMap raw-data contract."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from chicagohealthmap.analysis.raw_data_contract import assert_primary_tract_contract


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    audit = assert_primary_tract_contract(args.root)
    print(json.dumps(audit.to_jsonable(), indent=2, sort_keys=True))
    return 0 if audit.primary_tract_contract_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
