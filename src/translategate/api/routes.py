"""API routes: /check, /corpus/summary, /glossary/ask, /health."""

from __future__ import annotations

import functools
import logging
import pickle

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from translategate.models.train import QE_FEATURES, qe_features
from translategate.qa.checks import run_all
from translategate.rag.glossary import ask
from translategate.settings import get_config, resolve_path

logger = logging.getLogger(__name__)
router = APIRouter()


class CheckRequest(BaseModel):
    source: str = Field(min_length=3, max_length=2000)
    target: str = Field(min_length=1, max_length=4000)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@functools.lru_cache(maxsize=1)
def _artifacts():
    art = resolve_path(get_config()["data"]["artifacts_dir"])
    if not (art / "qe.pkl").exists():
        raise FileNotFoundError(
            "Artifacts missing; run make_corpus.py + translategate.models.train"
        )
    with open(art / "qe.pkl", "rb") as f:
        bundle = pickle.load(f)
    corpus = pd.read_parquet(art / "corpus_scored.parquet")
    return bundle, corpus


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/check")
def check(request: CheckRequest) -> dict:
    try:
        bundle, _ = _artifacts()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    findings = run_all(request.source, request.target)
    feats = pd.DataFrame([qe_features(request.source, request.target)])
    quality = 1 - float(bundle["model"].predict_proba(feats[QE_FEATURES])[0, 1])
    blockers = [f for f in findings if f["severity"] == "blocker"]
    return {
        "quality_score": round(quality, 4),
        "gate": "block" if blockers else ("review" if findings else "pass"),
        "findings": findings,
    }


@router.get("/corpus/summary")
def corpus_summary() -> dict:
    try:
        bundle, corpus = _artifacts()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    defect_counts = corpus["defect"].value_counts(dropna=True).to_dict()
    return {
        "metrics": bundle["metrics"],
        "n_strings": len(corpus),
        "planted_defects": {str(k): int(v) for k, v in defect_counts.items()},
    }


@router.post("/glossary/ask")
def glossary_ask(request: AskRequest) -> dict:
    return ask(request.question)
