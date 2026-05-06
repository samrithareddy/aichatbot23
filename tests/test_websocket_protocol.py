from backend.models.schemas import ChatMetadata, Intent, WebSocketEvent


def dump_event(event: WebSocketEvent) -> dict:
    if hasattr(event, "model_dump"):
        return event.model_dump(mode="json", exclude_none=True)
    return event.dict(exclude_none=True)


def test_token_event_serializes_protocol_shape() -> None:
    payload = dump_event(WebSocketEvent(type="token", data="Hello "))

    assert payload == {"type": "token", "data": "Hello "}


def test_done_event_includes_metadata() -> None:
    event = WebSocketEvent(
        type="done",
        metadata=ChatMetadata(
            session_id="session-1",
            intent=Intent.RETURN_POLICY,
            intent_confidence=0.92,
            latency_ms=120,
            input_tokens=10,
            output_tokens=20,
            sources_count=2,
        ),
    )

    payload = dump_event(event)

    assert payload["type"] == "done"
    assert payload["metadata"]["intent"] == "return_policy"
    assert payload["metadata"]["latency_ms"] == 120
