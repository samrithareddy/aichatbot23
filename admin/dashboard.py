"""Streamlit admin dashboard for chatbot observability."""

from __future__ import annotations

import os
from dataclasses import dataclass

import pandas as pd
import requests
import streamlit as st


API_BASE_URL = os.getenv("API_BASE_URL", "http://backend:8000")


@dataclass(frozen=True)
class Metrics:
    query_count: int
    intent_distribution: dict[str, int]
    average_latency_ms: float
    p95_latency_ms: float
    total_tokens: int
    escalation_rate: float


def fetch_metrics() -> Metrics:
    try:
        response = requests.get(f"{API_BASE_URL}/metrics", timeout=3)
        response.raise_for_status()
        payload = response.json()
    except Exception:
        payload = {
            "query_count": 0,
            "intent_distribution": {},
            "average_latency_ms": 0,
            "p95_latency_ms": 0,
            "total_tokens": 0,
            "escalation_rate": 0,
        }

    return Metrics(
        query_count=int(payload.get("query_count", 0)),
        intent_distribution=dict(payload.get("intent_distribution", {})),
        average_latency_ms=float(payload.get("average_latency_ms", 0)),
        p95_latency_ms=float(payload.get("p95_latency_ms", 0)),
        total_tokens=int(payload.get("total_tokens", 0)),
        escalation_rate=float(payload.get("escalation_rate", 0)),
    )


def main() -> None:
    st.set_page_config(page_title="Support AI Admin", page_icon=":bar_chart:", layout="wide")
    st.title("AI Customer Support Chatbot Admin")
    st.caption("Query analytics, token usage, latency, and retrieval health")

    metrics = fetch_metrics()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Queries", f"{metrics.query_count:,}")
    col2.metric("P95 latency", f"{metrics.p95_latency_ms:.0f} ms")
    col3.metric("Token usage", f"{metrics.total_tokens:,}")
    col4.metric("Escalation rate", f"{metrics.escalation_rate * 100:.1f}%")

    left, right = st.columns(2)
    with left:
        st.subheader("Intent distribution")
        if metrics.intent_distribution:
            intent_df = pd.DataFrame(
                [{"intent": intent, "queries": count} for intent, count in metrics.intent_distribution.items()]
            )
            st.bar_chart(intent_df, x="intent", y="queries")
        else:
            st.info("No completed queries have been logged yet.")

    with right:
        st.subheader("Latency percentiles")
        latency_df = pd.DataFrame(
            [
                {"percentile": "Average", "latency_ms": metrics.average_latency_ms},
                {"percentile": "P95", "latency_ms": metrics.p95_latency_ms},
            ]
        )
        st.bar_chart(latency_df, x="percentile", y="latency_ms")

    st.subheader("Model drift monitor")
    st.write(
        "Production deployments can write weekly embedding samples to Postgres/S3 and render PCA centroid "
        "movement here. Alert thresholds should trigger retriever evaluation when centroid shift exceeds policy."
    )

    st.subheader("Accuracy tracker")
    st.write(
        "Connect labeled review data to display rolling intent accuracy and RAG faithfulness. The target from "
        "the project report is 92% intent accuracy and 88% faithfulness."
    )


if __name__ == "__main__":
    main()
