"""Check evaluation + feature-based MT quality estimation (QE).

Usage:
    python -m translategate.models.train
"""

from __future__ import annotations

import logging
import pickle
import re

import mlflow
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from translategate.qa.checks import PLACEHOLDER_RE, run_all
from translategate.settings import get_config, get_settings, resolve_path

logger = logging.getLogger(__name__)

QE_FEATURES = ["placeholder_diff", "n_findings", "length_ratio", "english_hits", "copy_rate"]


def qe_features(source: str, target: str) -> dict:
    findings = run_all(source, target)
    src_tokens = set(re.findall(r"[a-z]+", source.lower()))
    tgt_tokens = re.findall(r"[a-z]+", target.lower())
    copied = sum(1 for t in tgt_tokens if t in src_tokens)
    return {
        "placeholder_diff": float(
            len(PLACEHOLDER_RE.findall(source)) != len(PLACEHOLDER_RE.findall(target))
        ),
        "n_findings": float(len(findings)),
        "length_ratio": len(target) / max(len(source), 1),
        "english_hits": float(sum(1 for f in findings if f["check"] == "untranslated")),
        "copy_rate": copied / max(len(tgt_tokens), 1),
    }


def train() -> dict:
    cfg = get_config()
    df = pd.read_parquet(resolve_path(cfg["data"]["processed_dir"]) / "corpus.parquet")

    # per-check detection quality vs planted defects
    check_hits = {
        k: {"tp": 0, "fp": 0, "fn": 0}
        for k in ["placeholder", "terminology", "untranslated", "length", "numbers"]
    }
    features = []
    for row in df.itertuples():
        findings = run_all(row.source, row.target)
        fired = {f["check"] for f in findings}
        for kind, counts in check_hits.items():
            planted = row.defect == kind
            if planted and kind in fired:
                counts["tp"] += 1
            elif planted:
                counts["fn"] += 1
            elif kind in fired:
                counts["fp"] += 1
        features.append(qe_features(row.source, row.target))

    metrics = {}
    for kind, c in check_hits.items():
        precision = c["tp"] / max(c["tp"] + c["fp"], 1)
        recall = c["tp"] / max(c["tp"] + c["fn"], 1)
        metrics[f"recall_{kind}"] = round(recall, 4)
        metrics[f"precision_{kind}"] = round(precision, 4)

    feats = pd.DataFrame(features)
    label = df["defect"].notna().astype(int)
    x_train, x_test, y_train, y_test = train_test_split(
        feats, label, test_size=0.3, random_state=42, stratify=label
    )
    qe = Pipeline([("scale", StandardScaler()), ("clf", LogisticRegression(max_iter=1000))])
    qe.fit(x_train[QE_FEATURES], y_train)
    prob = qe.predict_proba(x_test[QE_FEATURES])[:, 1]
    metrics["qe_auc"] = round(float(roc_auc_score(y_test, prob)), 4)
    metrics["defect_rate"] = round(float(label.mean()), 4)

    mlflow.set_tracking_uri(get_settings().mlflow_tracking_uri)
    mlflow.set_experiment(cfg["eval"]["experiment_name"])
    with mlflow.start_run(run_name="qa-gate"):
        mlflow.log_params({"n_strings": len(df)})
        mlflow.log_metrics(metrics)
    logger.info("qa-gate %s", metrics)

    artifacts = resolve_path(cfg["data"]["artifacts_dir"])
    artifacts.mkdir(parents=True, exist_ok=True)
    with open(artifacts / "qe.pkl", "wb") as f:
        pickle.dump({"model": qe, "features": QE_FEATURES, "metrics": metrics}, f)
    df.to_parquet(artifacts / "corpus_scored.parquet", index=False)
    return metrics


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    train()
