import asyncio

from backend.models.schemas import Intent, IntentResult, SourceDocument
from backend.services.chain import ChatChain


def collect_response(chain: ChatChain, intent: IntentResult, sources: list[SourceDocument]) -> str:
    async def _collect() -> str:
        tokens: list[str] = []
        async for token in chain.stream_answer(
            session_id="test-session",
            message="Can I return this?",
            intent=intent,
            sources=sources,
        ):
            tokens.append(token)
        return "".join(tokens)

    return asyncio.run(_collect())


def test_fallback_chain_streams_grounded_response() -> None:
    chain = ChatChain()
    sources = [
        SourceDocument(
            source="docs/return-policy.md",
            title="Return policy",
            snippet="Returns are accepted within 30 days.",
        )
    ]

    response = collect_response(chain, IntentResult(intent=Intent.RETURN_POLICY, confidence=0.92), sources)

    assert "return policy" in response
    assert "Returns are accepted within 30 days" in response
    assert "docs/return-policy.md" in response


def test_fallback_chain_returns_clarifying_prompt() -> None:
    intent = IntentResult(
        intent=Intent.PRODUCT_INFO,
        confidence=0.72,
        needs_clarification=True,
        clarification_prompt="Which support topic do you need?",
    )

    response = collect_response(ChatChain(), intent, [])

    assert response.strip() == "Which support topic do you need?"
