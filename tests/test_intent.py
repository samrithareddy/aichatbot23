import asyncio

from backend.models.schemas import Intent
from backend.services.intent import IntentClassifier


def classify(message: str):
    return asyncio.run(IntentClassifier().classify(message))


def test_extracts_order_status_and_order_id() -> None:
    result = classify("Where is my order #12345?")

    assert result.intent == Intent.ORDER_STATUS
    assert result.confidence >= 0.9
    assert result.slots["order_id"] == "12345"


def test_low_confidence_purchase_query_requests_clarification() -> None:
    result = classify("I need help with my purchase")

    assert result.needs_clarification is True
    assert result.clarification_prompt


def test_out_of_scope_query_is_classified() -> None:
    result = classify("What is the weather today?")

    assert result.intent == Intent.OUT_OF_SCOPE
