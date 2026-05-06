import asyncio

from backend.services.retriever import Retriever


def test_fallback_retriever_ranks_relevant_return_policy_source() -> None:
    results = asyncio.run(Retriever(top_k=2).retrieve("Can I return this after 30 days?"))

    assert results
    assert results[0].source == "docs/return-policy.md"
    assert results[0].score is not None


def test_fallback_retriever_respects_top_k() -> None:
    results = asyncio.run(Retriever(top_k=3).retrieve("product billing return troubleshooting"))

    assert len(results) == 3
