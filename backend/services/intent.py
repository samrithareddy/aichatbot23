"""Intent classification service.

The service uses GPT function-calling when an OpenAI key and LangChain integration
are available. A deterministic rules fallback keeps local development, tests, and
CI runnable without network access.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

from backend.models.schemas import Intent, IntentResult


ORDER_PATTERN = re.compile(r"(?:order|#)\s*#?\s*(?P<order_id>[A-Z0-9-]{5,})", re.IGNORECASE)


@dataclass(slots=True)
class IntentClassifier:
    """Classify incoming support queries and extract lightweight slots."""

    confidence_threshold: float = 0.80
    model: str = "gpt-4"

    async def classify(self, message: str) -> IntentResult:
        if os.getenv("OPENAI_API_KEY"):
            try:
                result = await self._classify_with_gpt(message)
                if result is not None:
                    return self._with_clarification(result, message)
            except Exception:
                # Keep the support path available when the model provider is down.
                pass

        return self._with_clarification(self._classify_with_rules(message), message)

    async def _classify_with_gpt(self, message: str) -> IntentResult | None:
        """Use GPT function calling via LangChain when dependencies are installed."""

        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            return None

        schema: dict[str, Any] = {
            "name": "classify_customer_support_intent",
            "description": "Classify customer support query intent and extract slots.",
            "parameters": {
                "type": "object",
                "properties": {
                    "intent": {"type": "string", "enum": [intent.value for intent in Intent]},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                    "slots": {"type": "object", "additionalProperties": True},
                },
                "required": ["intent", "confidence", "slots"],
            },
        }

        llm = ChatOpenAI(model=self.model, temperature=0)
        response = await llm.ainvoke(
            [
                (
                    "system",
                    "Classify customer support queries for an ecommerce/SaaS support bot. "
                    "Return only the provided function call.",
                ),
                ("human", message),
            ],
            functions=[schema],
            function_call={"name": schema["name"]},
        )
        call = response.additional_kwargs.get("function_call")
        if not call:
            return None

        import json

        payload = json.loads(call.get("arguments", "{}"))
        return IntentResult(
            intent=Intent(payload["intent"]),
            confidence=float(payload["confidence"]),
            slots=dict(payload.get("slots") or {}),
        )

    def _classify_with_rules(self, message: str) -> IntentResult:
        text = message.lower()
        slots: dict[str, Any] = {}
        if match := ORDER_PATTERN.search(message):
            slots["order_id"] = match.group("order_id")

        patterns: list[tuple[Intent, float, tuple[str, ...]]] = [
            (Intent.ORDER_STATUS, 0.93, ("order", "tracking", "shipment", "delivered", "where is")),
            (Intent.RETURN_POLICY, 0.92, ("return", "refund", "exchange", "30 days", "policy")),
            (Intent.TECHNICAL_SUPPORT, 0.88, ("broken", "wont", "won't", "error", "device", "turn on", "install")),
            (Intent.BILLING_INQUIRY, 0.90, ("charged", "invoice", "billing", "payment", "subscription")),
            (Intent.GENERAL_FAQ, 0.86, ("hours", "contact", "location", "shipping cost", "faq")),
            (Intent.PRODUCT_INFO, 0.85, ("spec", "feature", "compatible", "product", "manual")),
            (Intent.OUT_OF_SCOPE, 0.91, ("weather", "sports", "recipe", "movie")),
        ]
        for intent, confidence, keywords in patterns:
            if any(keyword in text for keyword in keywords):
                return IntentResult(intent=intent, confidence=confidence, slots=slots)

        return IntentResult(
            intent=Intent.PRODUCT_INFO,
            confidence=0.72,
            slots=slots,
        )

    def _with_clarification(self, result: IntentResult, message: str) -> IntentResult:
        ambiguous_purchase = "purchase" in message.lower() and result.intent in {
            Intent.PRODUCT_INFO,
            Intent.ORDER_STATUS,
        }
        if result.confidence < self.confidence_threshold or ambiguous_purchase:
            result.needs_clarification = True
            result.clarification_prompt = (
                "I can help with product details, order status, returns, billing, or technical support. "
                "Which one do you need?"
            )
        return result
