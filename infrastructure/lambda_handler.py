"""AWS Lambda ASGI adapter for the FastAPI backend."""

from __future__ import annotations

from mangum import Mangum

from backend.main import app


handler = Mangum(app, lifespan="off")
