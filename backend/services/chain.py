"""Conversational RAG response generation.

The class streams responses token-by-token. It uses OpenAI/LangChain when an API
key is configured and otherwise generates a deterministic grounded response from
retrieved snippets for local development and tests.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass, field

from backend.models.schemas import IntentResult, SourceDocument


def _estimate_tokens(text: str) -> int:
    return max(1, len(text.split()))


@dataclass(slots=True)
class ChatChain:
    model: str = "gpt-4"
    max_history_turns: int = 8
    _history: dict[str, list[tuple[str, str]]] = field(default_factory=dict)

    async def stream_answer(
        self,
        *,
        session_id: str,
        message: str,
        intent: IntentResult,
        sources: list[SourceDocument],
    ):
        if os.getenv("OPENAI_API_KEY"):
            try:
                async for token in self._stream_openai(session_id, message, intent, sources):
                    yield token
                return
            except Exception:
                for token in self._fallback_tokens(message, intent, sources):
                    yield token
                return

        for token in self._fallback_tokens(message, intent, sources):
            await asyncio.sleep(0)
            yield token

    async def _stream_openai(
        self,
        session_id: str,
        message: str,
        intent: IntentResult,
        sources: list[SourceDocument],
    ):
        try:
            from langchain_core.messages import HumanMessage, SystemMessage
            from langchain_openai import ChatOpenAI
        except ImportError:
            for token in self._fallback_tokens(message, intent, sources):
                yield token
            return

        context = "\n\n".join(f"[{idx + 1}] {source.snippet}" for idx, source in enumerate(sources))
        history = self._history.get(session_id, [])[-self.max_history_turns :]
        history_text = "\n".join(f"User: {user}\nAssistant: {assistant}" for user, assistant in history)
        prompt = (
            "You are a customer support assistant. Answer only from the supplied product and policy context. "
            "If the answer is unavailable, say so and offer escalation.\n\n"
            f"Intent: {intent.intent.value}\nHistory:\n{history_text}\n\nContext:\n{context}\n\nQuery: {message}"
        )

        llm = ChatOpenAI(model=self.model, temperature=0.2, streaming=True)
        async for chunk in llm.astream([SystemMessage(content="You are a grounded support bot."), HumanMessage(content=prompt)]):
            content = getattr(chunk, "content", "")
            if content:
                yield str(content)

    def _fallback_tokens(self, message: str, intent: IntentResult, sources: list[SourceDocument]):
        if intent.needs_clarification and intent.clarification_prompt:
            response = intent.clarification_prompt
        elif intent.intent.value == "out_of_scope":
            response = "I can help with product, order, return, billing, and technical support questions."
        else:
            lead = f"I found support guidance for {intent.intent.value.replace('_', ' ')}."
            evidence = " ".join(source.snippet for source in sources[:2])
            response = f"{lead} {evidence}".strip()
            if sources:
                response += f" Source: {sources[0].source}."
        for token in response.split(" "):
            yield token + " "

    def remember(self, session_id: str, user_message: str, assistant_message: str) -> None:
        turns = self._history.setdefault(session_id, [])
        turns.append((user_message, assistant_message))
        del turns[:-self.max_history_turns]

    @staticmethod
    def token_usage(message: str, response: str, sources: list[SourceDocument]) -> tuple[int, int]:
        source_text = " ".join(source.snippet for source in sources)
        return _estimate_tokens(message + " " + source_text), _estimate_tokens(response)
