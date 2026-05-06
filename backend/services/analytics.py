"""Query analytics store with Postgres and in-memory fallback implementations."""

from __future__ import annotations

import os
import json
from collections import Counter
from dataclasses import dataclass, field

from backend.models.schemas import MetricSnapshot, QueryLog


@dataclass(slots=True)
class AnalyticsStore:
    """Persist completed query telemetry and expose dashboard metrics."""

    postgres_dsn: str | None = field(default_factory=lambda: os.getenv("DATABASE_URL"))
    _events: list[QueryLog] = field(default_factory=list)

    async def log_query(self, event: QueryLog) -> None:
        if self.postgres_dsn:
            try:
                await self._log_postgres(event)
                return
            except Exception:
                # Keep serving support traffic if analytics storage is unavailable.
                pass
        self._events.append(event)

    async def _log_postgres(self, event: QueryLog) -> None:
        try:
            import psycopg
        except ImportError:
            self._events.append(event)
            return

        async with await psycopg.AsyncConnection.connect(self.postgres_dsn) as conn:
            sources_json = json.dumps(
                [
                    source.model_dump(mode="json") if hasattr(source, "model_dump") else source.dict()
                    for source in event.sources
                ]
            )
            await conn.execute(
                """
                CREATE TABLE IF NOT EXISTS query_logs (
                    id BIGSERIAL PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    message TEXT NOT NULL,
                    response TEXT NOT NULL,
                    intent TEXT NOT NULL,
                    intent_confidence DOUBLE PRECISION NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    input_tokens INTEGER NOT NULL,
                    output_tokens INTEGER NOT NULL,
                    sources JSONB NOT NULL,
                    created_at DOUBLE PRECISION NOT NULL
                )
                """
            )
            await conn.execute(
                """
                INSERT INTO query_logs (
                    session_id, message, response, intent, intent_confidence,
                    latency_ms, input_tokens, output_tokens, sources, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                """,
                (
                    event.session_id,
                    event.message,
                    event.response,
                    event.intent.value,
                    event.intent_confidence,
                    event.latency_ms,
                    event.input_tokens,
                    event.output_tokens,
                    sources_json,
                    event.created_at,
                ),
            )

    def snapshot(self) -> MetricSnapshot:
        if not self._events:
            return MetricSnapshot(
                query_count=0,
                intent_distribution={},
                average_latency_ms=0,
                p95_latency_ms=0,
                total_tokens=0,
                escalation_rate=0,
            )

        latencies = sorted(event.latency_ms for event in self._events)
        percentile_index = min(len(latencies) - 1, int(round(0.95 * (len(latencies) - 1))))
        intents = Counter(event.intent.value for event in self._events)
        escalations = sum(1 for event in self._events if event.intent.value in {"technical_support", "out_of_scope"})
        total_tokens = sum(event.input_tokens + event.output_tokens for event in self._events)
        return MetricSnapshot(
            query_count=len(self._events),
            intent_distribution=dict(intents),
            average_latency_ms=sum(latencies) / len(latencies),
            p95_latency_ms=latencies[percentile_index],
            total_tokens=total_tokens,
            escalation_rate=escalations / len(self._events),
        )
