"""FastAPI application factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI

from translategate import __version__
from translategate.api.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")


def create_app() -> FastAPI:
    app = FastAPI(
        title="translategate",
        description="Localization QA gate: terminology-compliance and placeholder-integrity checks, feature-based MT quality estimation, corpus-level defect dashboards, and a cited glossary assistant.",
        version=__version__,
    )
    app.include_router(router)
    return app


app = create_app()
