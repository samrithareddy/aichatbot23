"""Helpers for WebSocket event serialization."""

from __future__ import annotations

from fastapi import WebSocket

from backend.models.schemas import ChatMetadata, SourceDocument, WebSocketEvent


class WebSocketStreamer:
    """Send typed JSON events to a connected client."""

    def __init__(self, websocket: WebSocket) -> None:
        self.websocket = websocket

    async def token(self, data: str) -> None:
        await self._send(WebSocketEvent(type="token", data=data))

    async def sources(self, data: list[SourceDocument]) -> None:
        await self._send(WebSocketEvent(type="sources", data=data))

    async def done(self, metadata: ChatMetadata) -> None:
        await self._send(WebSocketEvent(type="done", metadata=metadata))

    async def error(self, message: str) -> None:
        await self._send(WebSocketEvent(type="error", message=message))

    async def _send(self, event: WebSocketEvent) -> None:
        if hasattr(event, "model_dump"):
            payload = event.model_dump(mode="json", exclude_none=True)
        else:
            payload = event.dict(exclude_none=True)
        await self.websocket.send_json(payload)
