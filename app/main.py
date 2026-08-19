from __future__ import annotations

from fastapi import FastAPI

from app.db.postgres import init_schema
from app.api.routes import compliance

app = FastAPI(title="License Compliance Graph Engine")


@app.on_event("startup")
def _startup() -> None:
    init_schema()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(compliance.router)
