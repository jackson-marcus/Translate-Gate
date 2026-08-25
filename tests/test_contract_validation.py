"""Unit tests for Contract-First Schema-Driven Validation in TranslateGate."""

from __future__ import annotations

import pytest

from translategate.contract import (
    ContractValidationResult,
    ContractValidator,
    ContractViolation,
    TranslationContract,
    ValidationSeverity,
)


@pytest.fixture
def standard_en_de_contract() -> TranslationContract:
    return TranslationContract(
        source_locale="en",
        target_locale="de",
        max_length_expansion_ratio=2.0,
        min_length_compression_ratio=0.4,
        glossary_mappings={"checkout": "Kasse", "shipping": "Versand"},
        forbidden_terms=("untranslated_mock", "forbidden_vulgarity"),
        strict_placeholder_matching=True,
        preserve_numeric_tokens=True,
    )


def test_contract_validation_clean_pass(standard_en_de_contract):
    validator = ContractValidator(standard_en_de_contract)
    src = "Your shipping cost for 3 items is {price_total} at checkout."
    tgt = "Ihre Versandkosten für 3 Artikel an der Kasse betragen {price_total}."

    res: ContractValidationResult = validator.validate(src, tgt)
    assert res.is_valid is True
    assert res.has_blockers is False
    assert len(res.violations) == 0


def test_contract_validation_placeholder_corruption(standard_en_de_contract):
    validator = ContractValidator(standard_en_de_contract)
    src = "Hello {user_name}, you have {count} messages."
    tgt = "Hallo {user_name}, Sie haben 5 Nachrichten."  # Missing {count} placeholder

    res = validator.validate(src, tgt)
    assert res.is_valid is False
    assert res.has_blockers is True

    rule_ids = {v.rule_id for v in res.violations}
    assert "RULE-PH-001" in rule_ids


def test_contract_validation_glossary_breach(standard_en_de_contract):
    validator = ContractValidator(standard_en_de_contract)
    src = "Proceed to checkout now."
    tgt = "Gehen Sie jetzt weiter."  # Missing glossary term 'Kasse'

    res = validator.validate(src, tgt)
    assert res.is_valid is False
    glossary_violations = [v for v in res.violations if v.field_name == "glossary"]
    assert len(glossary_violations) == 1
    assert glossary_violations[0].expected_value == "Kasse"


def test_contract_json_schema_export(standard_en_de_contract):
    validator = ContractValidator(standard_en_de_contract)
    schema = validator.to_json_schema()

    assert schema["type"] == "object"
    assert "source_text" in schema["properties"]
    assert "target_text" in schema["properties"]
    assert schema["properties"]["source_locale"]["const"] == "en"
    assert schema["properties"]["target_locale"]["const"] == "de"
