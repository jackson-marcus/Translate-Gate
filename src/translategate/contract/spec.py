"""Contract-First Schema-Driven Validation - Specifications & Contracts.

Defines formal TranslationContract models, validation invariants, and violation records.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class ValidationSeverity(StrEnum):
    BLOCKER = "BLOCKER"
    MAJOR = "MAJOR"
    MINOR = "MINOR"
    WARNING = "WARNING"


@dataclass(frozen=True)
class ContractViolation:
    """A single specification breach identified against the TranslationContract."""

    rule_id: str
    severity: ValidationSeverity
    field_name: str
    message: str
    expected_value: Any = None
    actual_value: Any = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "severity": str(self.severity),
            "field": self.field_name,
            "message": self.message,
            "expected": str(self.expected_value) if self.expected_value is not None else None,
            "actual": str(self.actual_value) if self.actual_value is not None else None,
        }


@dataclass(frozen=True)
class ContractValidationResult:
    """Consolidated outcome of contract-driven translation validation."""

    is_valid: bool
    has_blockers: bool
    violations: tuple[ContractViolation, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "has_blockers": self.has_blockers,
            "violations_count": len(self.violations),
            "violations": [v.as_dict() for v in self.violations],
        }


@dataclass(frozen=True)
class TranslationContract:
    """Formal contract specifying localization invariants for a language pair."""

    source_locale: str
    target_locale: str
    max_length_expansion_ratio: float = 2.5
    min_length_compression_ratio: float = 0.3
    glossary_mappings: dict[str, str] = field(default_factory=dict)
    forbidden_terms: tuple[str, ...] = field(default_factory=tuple)
    strict_placeholder_matching: bool = True
    preserve_numeric_tokens: bool = True
