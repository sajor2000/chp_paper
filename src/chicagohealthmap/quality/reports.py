"""Machine-readable, disclosure-safe quality findings."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    """Whether a finding blocks analysis or requires review."""

    fatal = "fatal"
    warning = "warning"


@dataclass(frozen=True, slots=True)
class QualityFinding:
    """A quality result containing no row values or protected identifiers."""

    code: str
    severity: Severity
    message: str
    affected_rows: tuple[int, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
            "affected_rows": list(self.affected_rows),
            "affected_row_count": len(self.affected_rows),
        }


@dataclass(frozen=True, slots=True)
class QualityReport:
    """Quality findings and the resulting Gate 3 state."""

    source_id: str
    snapshot_id: str
    findings: tuple[QualityFinding, ...]

    @property
    def has_fatal(self) -> bool:
        return any(finding.severity is Severity.fatal for finding in self.findings)

    def to_dict(self) -> dict[str, Any]:
        counts = {
            severity.value: sum(finding.severity is severity for finding in self.findings)
            for severity in Severity
        }
        return {
            "source_id": self.source_id,
            "snapshot_id": self.snapshot_id,
            "gate_3_status": "closed" if self.has_fatal else "eligible_for_review",
            "finding_counts": counts,
            "findings": [finding.to_dict() for finding in self.findings],
        }
