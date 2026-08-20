"""Pseudo-translator properties, per-check detection, QE quality, API contract."""

from __future__ import annotations

from translategate.qa.checks import (
    check_numbers,
    check_placeholders,
    check_terminology,
    run_all,
)
from translategate.qa.pseudo import translate
from translategate.rag.glossary import ask


def test_pseudo_translator_preserves_invariants():
    source = "Your cart has {count} items ready for checkout costing 49.99"
    target = translate(source)
    assert "{count}" in target and "49.99" in target
    assert "korv" in target and "kassa" in target  # glossary terms enforced
    assert translate(source) == target  # deterministic


def test_checks_fire_on_crafted_defects():
    source = "Your cart has {count} items ready for checkout"
    clean = translate(source)
    assert run_all(source, clean) == []

    assert check_placeholders(source, clean.replace("{count}", ""))
    assert check_terminology(source, clean.replace("kassa", "zahlung"))
    assert check_numbers("Pay 49.99 now", "yapa 99.99 wona")


def test_detection_and_qe_quality(trained):
    m = trained["metrics"]
    assert m["recall_placeholder"] >= 0.95
    assert m["recall_terminology"] >= 0.85
    assert m["recall_untranslated"] >= 0.7
    assert m["recall_length"] >= 0.9
    assert m["qe_auc"] >= 0.8
    assert m["precision_placeholder"] >= 0.9


def test_glossary_assistant_cites_and_rejects_junk():
    hit = ask("How do I translate checkout?")
    assert hit["matched"] and hit["rules"][0]["rule_id"] == "term-checkout"
    junk = ask("quantum zebra espresso")
    assert not junk["matched"]


def test_api_contract(api_client):
    assert api_client.get("/health").json() == {"status": "ok"}

    source = "Your cart has {count} items ready for checkout"
    bad = "rauya korv seh items ydeara rofa zahlung"
    checked = api_client.post("/check", json={"source": source, "target": bad}).json()
    assert checked["gate"] in {"review", "block"}
    assert any(f["check"] == "placeholder" for f in checked["findings"])
    assert any(f["check"] == "terminology" for f in checked["findings"])

    clean = api_client.post(
        "/check",
        json={"source": source, "target": "rauya korv seh {count} items ydeara rofa kassa"},
    ).json()
    assert clean["gate"] == "pass"

    summary = api_client.get("/corpus/summary").json()
    assert summary["n_strings"] == 800

    answer = api_client.post(
        "/glossary/ask", json={"question": "can I use abo for subscription"}
    ).json()
    assert answer["matched"]
