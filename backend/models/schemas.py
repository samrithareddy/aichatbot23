"""Shared Pydantic models for chat, retrieval, intent, and analytics payloads."""

from __future__ import annotations

from enum import Enum
from time import time
from typing import Any, Literal

from pydantic import BaseModel, Field


class Intent(str, Enum):
    PRODUCT_INFO = "product_info"
    ORDER_STATUS = "order_status"
    RETURN_POLICY = "return_policy"
    TECHNICAL_SUPPORT = "technical_support"
    BILLING_INQUIRY = "billing_inquiry"
    GENERAL_FAQ = "general_faq"
    OUT_OF_SCOPE = "out_of_scope"


class IntentResult(BaseModel):
    intent: Intent
    confidence: float = Field(ge=0.0, le=1.0)
    slots: dict[str, Any] = Field(default_factory=dict)
    needs_clarification: bool = False
    clarification_prompt: str | None = None


class SourceDocument(BaseModel):
    source: str
    title: str | None = None
    snippet: str
    score: float | None = None


class ChatRequest(BaseModel):
    type: Literal["query"] = "query"
    session_id: str
    message: str


class ChatMetadata(BaseModel):
    session_id: str
    intent: Intent
    intent_confidence: float
    latency_ms: int
    input_tokens: int = 0
    output_tokens: int = 0
    sources_count: int = 0


class WebSocketEvent(BaseModel):
    type: Literal["token", "sources", "done", "error"]
    data: str | list[SourceDocument] | None = None
    metadata: ChatMetadata | dict[str, Any] | None = None
    message: str | None = None


class QueryLog(BaseModel):
    session_id: str
    message: str
    response: str
    intent: Intent
    intent_confidence: float
    latency_ms: int
    input_tokens: int
    output_tokens: int
    sources: list[SourceDocument] = Field(default_factory=list)
    created_at: float = Field(default_factory=time)


class MetricSnapshot(BaseModel):
    query_count: int
    intent_distribution: dict[str, int]
    average_latency_ms: float
    p95_latency_ms: float
    total_tokens: int
    escalation_rate: float
