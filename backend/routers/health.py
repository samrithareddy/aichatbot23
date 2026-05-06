"""Health and metrics routes."""

from __future__ import annotations

from fastapi import APIRouter

from backend.dependencies import analytics_store

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "ai-customer-support-chatbot"}


@router.get("/metrics")
async def metrics() -> dict[str, object]:
    snapshot = analytics_store.snapshot()
    if hasattr(snapshot, "model_dump"):
        return snapshot.model_dump()
    return snapshot.dict()
