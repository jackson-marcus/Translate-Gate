"""Parallel corpus with planted localization defects.

Sources are templated product strings; correct targets come from the
deterministic pseudo-translator; ~35% of pairs get one injected defect with a
ground-truth label (which check should fire).

Usage:
    uv run python scripts/make_corpus.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from translategate.qa.pseudo import FORBIDDEN, GLOSSARY, translate
from translategate.settings import get_config, resolve_path

TEMPLATES = [
    "Your cart has {count} items ready for checkout",
    "Manage your subscription in account settings",
    "Your order {order_id} shipped with free shipping",
    "Request a refund within 30 days",
    "Welcome back {name}, view your account",
    "Update your shipping address before checkout",
    "Your subscription renews on {date} for 12 months",
    "Cancel your order in settings",
    "BrandCo Premium includes priority shipping",
    "Confirm your refund of 49.99 now",
    "Please continue to checkout with {count} items",
    "Delete your account permanently in settings",
]


def inject_defect(source: str, target: str, kind: str, rng) -> str:
    if kind == "placeholder":
        return re.sub(r"\{[a-z_]+\}|%[sd]", "", target, count=1).strip()
    if kind == "terminology":
        terms = [t for t in GLOSSARY if re.search(rf"\b{t}\b", source.lower()) and FORBIDDEN.get(t)]
        if terms:
            term = str(rng.choice(terms))
            return target.replace(GLOSSARY[term], str(rng.choice(FORBIDDEN[term])))
        return target.replace(next(iter(GLOSSARY.values())), "xxx")
    if kind == "untranslated":
        words = source.split()
        english = " ".join(words[: max(2, len(words) // 3)]).lower()
        return english + " " + " ".join(target.split()[len(words) // 3 :])
    if kind == "length":
        return target + " " + " ".join(["blabla"] * max(6, len(target.split())))
    if kind == "numbers":
        return re.sub(
            r"\d+(?:\.\d+)?", lambda m: str(int(float(m.group()) * 2 + 1)), target, count=1
        )
    return target


def applicable_kinds(target: str) -> list[str]:
    """A defect label must correspond to an injectable defect for THIS pair."""
    kinds = ["terminology", "untranslated", "length"]
    if re.search(r"\{[a-z_]+\}|%[sd]", target):
        kinds.append("placeholder")
    if re.search(r"\d", target):
        kinds.append("numbers")
    return kinds


def generate(n: int, defect_rate: float, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for i in range(n):
        template = str(rng.choice(TEMPLATES))
        source = (
            template.replace("{count}", str(rng.integers(1, 30)))
            if rng.random() < 0.4
            else template
        )
        target = translate(source)
        defect = str(rng.choice(applicable_kinds(target))) if rng.random() < defect_rate else None
        if defect:
            target = inject_defect(source, target, defect, rng)
        rows.append({"string_id": i + 1, "source": source, "target": target, "defect": defect})
    return pd.DataFrame(rows)


def main() -> None:
    cfg = get_config()["data"]
    df = generate(cfg["n_strings"], cfg["defect_rate"], cfg["seed"])
    out = resolve_path(cfg["processed_dir"])
    out.mkdir(parents=True, exist_ok=True)
    df.to_parquet(out / "corpus.parquet", index=False)
    print(json.dumps({"n": len(df), "defects": int(df["defect"].notna().sum())}))


if __name__ == "__main__":
    main()
