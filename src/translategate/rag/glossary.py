"""Glossary assistant: BM25 over parsed glossary/style rules, with citations."""

from __future__ import annotations

import functools
import re

from rank_bm25 import BM25Plus

from translategate.settings import get_config, resolve_path


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zåäö0-9]+", text.lower())


def parse_glossary(markdown: str) -> list[dict]:
    rules = []
    for block in re.split(r"^## ", markdown, flags=re.MULTILINE)[1:]:
        head, _, body = block.partition("\n")
        rules.append({"rule_id": head.strip(), "body": body.strip()})
    return rules


@functools.lru_cache(maxsize=1)
def _index():
    cfg = get_config()["rag"]
    markdown = resolve_path(cfg["glossary_path"]).read_text(encoding="utf-8")
    rules = parse_glossary(markdown)
    docs = [_tokenize(f"{r['rule_id']} {r['body']}") for r in rules]
    vocab = {token for doc in docs for token in doc}
    return rules, BM25Plus(docs), vocab


def ask(question: str, top_k: int | None = None) -> dict:
    cfg = get_config()["rag"]
    top_k = top_k or cfg["top_k"]
    rules, bm25, vocab = _index()
    tokens = [t for t in _tokenize(question) if t in vocab]
    if not tokens:
        return {"question": question, "matched": False, "rules": []}
    scores = bm25.get_scores(tokens)
    order = scores.argsort()[::-1][:top_k]
    hits = [
        {
            "rule_id": rules[i]["rule_id"],
            "score": round(float(scores[i]), 2),
            "body": rules[i]["body"],
        }
        for i in order
        if scores[i] >= cfg["min_score"]
    ]
    return {"question": question, "matched": bool(hits), "rules": hits}
