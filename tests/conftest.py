"""Offline fixtures: generated corpus evaluated into tmp artifacts."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from make_corpus import generate  # noqa: E402

from translategate.settings import get_config, get_settings  # noqa: E402


@pytest.fixture(scope="session")
def corpus():
    return generate(n=800, defect_rate=0.35, seed=7)


@pytest.fixture(scope="session")
def trained(tmp_path_factory, corpus):
    tmp = tmp_path_factory.mktemp("translategate")
    (tmp / "processed").mkdir()
    corpus.to_parquet(tmp / "processed" / "corpus.parquet", index=False)

    cfg = get_config()
    originals = (cfg["data"]["processed_dir"], cfg["data"]["artifacts_dir"])
    cfg["data"]["processed_dir"] = str(tmp / "processed")
    cfg["data"]["artifacts_dir"] = str(tmp / "artifacts")

    old_uri = os.environ.get("MLFLOW_TRACKING_URI")
    os.environ["MLFLOW_TRACKING_URI"] = f"sqlite:///{tmp / 'mlflow.db'}"
    get_settings.cache_clear()

    from translategate.models.train import train

    metrics = train()
    yield {"metrics": metrics, "artifacts": tmp / "artifacts"}

    cfg["data"]["processed_dir"], cfg["data"]["artifacts_dir"] = originals
    if old_uri is None:
        os.environ.pop("MLFLOW_TRACKING_URI", None)
    else:
        os.environ["MLFLOW_TRACKING_URI"] = old_uri
    get_settings.cache_clear()


@pytest.fixture
def api_client(trained):
    from fastapi.testclient import TestClient

    from translategate.api import routes
    from translategate.api.main import app

    routes._artifacts.cache_clear()
    try:
        yield TestClient(app)
    finally:
        routes._artifacts.cache_clear()
