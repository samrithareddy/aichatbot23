"""WebSocket chat endpoint."""

from __future__ import annotations

import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from backend.dependencies import analytics_store, chat_chain, intent_classifier, retriever
from backend.models.schemas import ChatMetadata, ChatRequest, QueryLog
from backend.services.streaming import WebSocketStreamer

router = APIRouter(tags=["chat"])


@router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket) -> None:
    await websocket.accept()
    streamer = WebSocketStreamer(websocket)

    while True:
        try:
            payload = await websocket.receive_json()
            request = ChatRequest(**payload)
            started_at = time.perf_counter()

            intent = await intent_classifier.classify(request.message)
            sources = [] if intent.needs_clarification else await retriever.retrieve(request.message)

            tokens: list[str] = []
            async for token in chat_chain.stream_answer(
                session_id=request.session_id,
                message=request.message,
                intent=intent,
                sources=sources,
            ):
                tokens.append(token)
                await streamer.token(token)

            response = "".join(tokens).strip()
            latency_ms = int((time.perf_counter() - started_at) * 1000)
            input_tokens, output_tokens = chat_chain.token_usage(request.message, response, sources)
            metadata = ChatMetadata(
                session_id=request.session_id,
                intent=intent.intent,
                intent_confidence=intent.confidence,
                latency_ms=latency_ms,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                sources_count=len(sources),
            )

            if sources:
                await streamer.sources(sources)
            await streamer.done(metadata)

            chat_chain.remember(request.session_id, request.message, response)
            await analytics_store.log_query(
                QueryLog(
                    session_id=request.session_id,
                    message=request.message,
                    response=response,
                    intent=intent.intent,
                    intent_confidence=intent.confidence,
                    latency_ms=latency_ms,
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    sources=sources,
                )
            )
        except WebSocketDisconnect:
            return
        except ValidationError as exc:
            await streamer.error(f"Invalid chat payload: {exc.errors()}")
        except Exception as exc:
            await streamer.error(f"Chat generation failed: {exc}")
