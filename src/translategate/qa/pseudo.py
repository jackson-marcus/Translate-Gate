"""Deterministic pseudo-locale translator (the 'correct' reference behavior).

Glossary terms map to their mandated target terms; other words get a
deterministic consonant/vowel transform; placeholders and numbers pass through
untouched. Corpus defects are injected as deviations from this reference.
"""

from __future__ import annotations

import re

GLOSSARY = {
    "checkout": "kassa",
    "cart": "korv",
    "account": "konto",
    "subscription": "abonnemang",
    "order": "beställning",
    "refund": "återbetalning",
    "shipping": "frakt",
    "settings": "inställningar",
}
FORBIDDEN = {
    "checkout": ["zahlung", "bezahlung"],
    "cart": ["wagen"],
    "account": ["profil"],
    "refund": ["retur"],
    "order": ["kommando"],
}
BRANDS = {"brandco", "premium", "pro", "app"}
TOKEN_RE = re.compile(r"(\{[a-z_]+\}|%[sd]|\d+(?:\.\d+)?|[A-Za-z]+|\S)")
VOWEL_MAP = str.maketrans("aeiou", "eioua")


def pseudo_word(word: str) -> str:
    lower = word.lower()
    if lower in GLOSSARY:
        return GLOSSARY[lower]
    if lower in BRANDS:
        return word
    return (lower[::-1] + "a").translate(VOWEL_MAP) if len(lower) > 2 else lower


def translate(source: str) -> str:
    out = []
    for token in TOKEN_RE.findall(source):
        if token.startswith("{") or token.startswith("%") or token[0].isdigit():
            out.append(token)
        elif token.isalpha():
            out.append(pseudo_word(token))
        else:
            out.append(token)
    return " ".join(out)
