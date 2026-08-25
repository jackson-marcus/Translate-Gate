"""Contract-First Schema-Driven Validator.

Executes schema-driven contract validation and exports JSON Schema definitions.
"""

from __future__ import annotations

import re
from typing import Any

from translategate.contract.spec import (
    ContractValidationResult,
    ContractViolation,
    TranslationContract,
    ValidationSeverity,
)

PLACEHOLDER_PATTERN = re.compile(r"\{[a-zA-Z0-9_]+\}|%[sd]")
NUMBER_PATTERN = re.compile(r"\b\d+(?:\.\d+)?\b")


class ContractValidator:
    """Schema-driven validator compiling TranslationContract invariants into validation sweeps."""

    def __init__(self, contract: TranslationContract) -> None:
        self.contract = contract

    def validate(self, source_text: str, target_text: str) -> ContractValidationResult:
        """Validates source and target string pairs against all contract rules."""
        violations: list[ContractViolation] = []

        # 1. Placeholder Invariant
        if self.contract.strict_placeholder_matching:
            src_ph = sorted(PLACEHOLDER_PATTERN.findall(source_text))
            tgt_ph = sorted(PLACEHOLDER_PATTERN.findall(target_text))
            if src_ph != tgt_ph:
                violations.append(
                    ContractViolation(
                        rule_id="RULE-PH-001",
                        severity=ValidationSeverity.BLOCKER,
                        field_name="placeholders",
                        message=f"Placeholders corrupted or missing. Source: {src_ph}, Target: {tgt_ph}",
                        expected_value=src_ph,
                        actual_value=tgt_ph,
                    )
                )

        # 2. Number Preservation Invariant
        if self.contract.preserve_numeric_tokens:
            src_nums = sorted(NUMBER_PATTERN.findall(source_text))
            tgt_nums = sorted(NUMBER_PATTERN.findall(target_text))
            if src_nums != tgt_nums:
                violations.append(
                    ContractViolation(
                        rule_id="RULE-NUM-002",
                        severity=ValidationSeverity.MAJOR,
                        field_name="numeric_tokens",
                        message=f"Numeric tokens mismatch. Source: {src_nums}, Target: {tgt_nums}",
                        expected_value=src_nums,
                        actual_value=tgt_nums,
                    )
                )

        # 3. Expansion / Compression Ratio Invariant
        len_src = max(1, len(source_text))
        len_tgt = len(target_text)
        ratio = len_tgt / len_src

        if ratio > self.contract.max_length_expansion_ratio:
            violations.append(
                ContractViolation(
                    rule_id="RULE-LEN-003",
                    severity=ValidationSeverity.MAJOR,
                    field_name="expansion_ratio",
                    message=f"Translation expanded by {ratio:.2f}x (limit: {self.contract.max_length_expansion_ratio}x)",
                    expected_value=f"<= {self.contract.max_length_expansion_ratio}",
                    actual_value=ratio,
                )
            )
        elif ratio < self.contract.min_length_compression_ratio and len_tgt > 0:
            violations.append(
                ContractViolation(
                    rule_id="RULE-LEN-004",
                    severity=ValidationSeverity.MAJOR,
                    field_name="compression_ratio",
                    message=f"Translation overly compressed to {ratio:.2f}x (minimum: {self.contract.min_length_compression_ratio}x)",
                    expected_value=f">= {self.contract.min_length_compression_ratio}",
                    actual_value=ratio,
                )
            )

        # 4. Glossary Consistency Invariant
        src_lower = source_text.lower()
        tgt_lower = target_text.lower()
        for term, expected_target in self.contract.glossary_mappings.items():
            if re.search(rf"\b{re.escape(term.lower())}\b", src_lower):
                if expected_target.lower() not in tgt_lower:
                    violations.append(
                        ContractViolation(
                            rule_id=f"RULE-GLOSS-{term.lower()}",
                            severity=ValidationSeverity.MAJOR,
                            field_name="glossary",
                            message=f"Glossary term '{term}' must translate to '{expected_target}'",
                            expected_value=expected_target,
                            actual_value="MISSING",
                        )
                    )

        # 5. Forbidden Terms Invariant
        for forbidden in self.contract.forbidden_terms:
            if re.search(rf"\b{re.escape(forbidden.lower())}\b", tgt_lower):
                violations.append(
                    ContractViolation(
                        rule_id=f"RULE-FORBID-{forbidden.lower()}",
                        severity=ValidationSeverity.BLOCKER,
                        field_name="forbidden_terms",
                        message=f"Forbidden / offensive term '{forbidden}' detected in target translation",
                        expected_value="ABSENT",
                        actual_value=forbidden,
                    )
                )

        has_blockers = any(v.severity == ValidationSeverity.BLOCKER for v in violations)
        is_valid = len(violations) == 0

        return ContractValidationResult(
            is_valid=is_valid,
            has_blockers=has_blockers,
            violations=tuple(violations),
        )

    def to_json_schema(self) -> dict[str, Any]:
        """Generates standard JSON Schema specification for this TranslationContract."""
        return {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": f"TranslationContract_{self.contract.source_locale}_{self.contract.target_locale}",
            "type": "object",
            "properties": {
                "source_text": {"type": "string", "minLength": 1},
                "target_text": {"type": "string", "minLength": 1},
                "source_locale": {"type": "string", "const": self.contract.source_locale},
                "target_locale": {"type": "string", "const": self.contract.target_locale},
            },
            "required": ["source_text", "target_text", "source_locale", "target_locale"],
        }
