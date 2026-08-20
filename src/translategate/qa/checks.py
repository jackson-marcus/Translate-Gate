"""Localization QA checks: each returns findings with glossary rule citations."""

from __future__ import annotations

import re

from translategate.qa.pseudo import FORBIDDEN, GLOSSARY
from translategate.settings import get_config

PLACEHOLDER_RE = re.compile(r"\{[a-z_]+\}|%[sd]")
NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")
ENGLISH_HINTS = {
    "the",
    "and",
    "your",
    "please",
    "with",
    "click",
    "here",
    "now",
    "free",
    "view",
    "update",
    "delete",
    "cancel",
    "confirm",
    "continue",
    "manage",
}


def check_placeholders(source: str, target: str) -> list[dict]:
    src = sorted(PLACEHOLDER_RE.findall(source))
    tgt = sorted(PLACEHOLDER_RE.findall(target))
    if src != tgt:
        return [
            {
                "check": "placeholder",
                "severity": "blocker",
                "rule_id": "placeholders",
                "detail": f"source has {src or 'none'}, target has {tgt or 'none'}",
            }
        ]
    return []


def check_terminology(source: str, target: str) -> list[dict]:
    findings = []
    source_lower, target_lower = source.lower(), target.lower()
    for term, required in GLOSSARY.items():
        if re.search(rf"\b{term}\b", source_lower):
            if required not in target_lower:
                findings.append(
                    {
                        "check": "terminology",
                        "severity": "major",
                        "rule_id": f"term-{term}",
                        "detail": f"'{term}' must become '{required}' — not found in target",
                    }
                )
            for bad in FORBIDDEN.get(term, []):
                if bad in target_lower:
                    findings.append(
                        {
                            "check": "terminology",
                            "severity": "major",
                            "rule_id": f"term-{term}",
                            "detail": f"forbidden variant '{bad}' used for '{term}'",
                        }
                    )
    return findings


def check_untranslated(source: str, target: str) -> list[dict]:
    cfg = get_config()["checks"]
    allowed = set(cfg["allowed_english"])
    leftovers = [
        w for w in re.findall(r"[a-z]+", target.lower()) if w in ENGLISH_HINTS and w not in allowed
    ]
    if leftovers:
        return [
            {
                "check": "untranslated",
                "severity": "major",
                "rule_id": "term-settings",
                "detail": f"english left in target: {sorted(set(leftovers))}",
            }
        ]
    return []


def check_length(source: str, target: str) -> list[dict]:
    cfg = get_config()["checks"]
    lo, hi = cfg["length_ratio_band"]
    ratio = len(target) / max(len(source), 1)
    if not lo <= ratio <= hi:
        return [
            {
                "check": "length",
                "severity": "minor",
                "rule_id": "length-budget",
                "detail": f"length ratio {ratio:.2f} outside [{lo}, {hi}]",
            }
        ]
    return []


def check_numbers(source: str, target: str) -> list[dict]:
    src = sorted(NUMBER_RE.findall(source))
    tgt = sorted(NUMBER_RE.findall(target))
    if src != tgt:
        return [
            {
                "check": "numbers",
                "severity": "major",
                "rule_id": "tone",
                "detail": f"numbers differ: source {src or 'none'} vs target {tgt or 'none'}",
            }
        ]
    return []


ALL_CHECKS = [
    check_placeholders,
    check_terminology,
    check_untranslated,
    check_length,
    check_numbers,
]


def run_all(source: str, target: str) -> list[dict]:
    findings = []
    for check in ALL_CHECKS:
        findings.extend(check(source, target))
    return findings
