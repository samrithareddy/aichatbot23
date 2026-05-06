"""Document retrieval service with FAISS support and a local fallback corpus."""

from __future__ import annotations

import math
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from backend.models.schemas import SourceDocument


DEFAULT_CORPUS = [
    SourceDocument(
        source="docs/product-specs.md",
        title="Product specifications",
        snippet="SmartHub X supports Wi-Fi 6, Bluetooth LE, USB-C power, and a two-year warranty.",
    ),
    SourceDocument(
        source="docs/return-policy.md",
        title="Return policy",
        snippet="Most products can be returned within 30 days when they are undamaged and include the receipt.",
    ),
    SourceDocument(
        source="docs/billing.md",
        title="Billing support",
        snippet="Duplicate charges are automatically reversed when payment retries settle within 24 hours.",
    ),
    SourceDocument(
        source="docs/troubleshooting.md",
        title="Troubleshooting guide",
        snippet="If the device will not turn on, hold power for 10 seconds and verify the USB-C adapter output.",
    ),
    SourceDocument(
        source="docs/faq.md",
        title="General FAQ",
        snippet="Support is available Monday through Friday from 8 AM to 6 PM Pacific time.",
    ),
]


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 1}


@dataclass(slots=True)
class Retriever:
    """Retrieve source snippets from FAISS when configured, otherwise from memory."""

    index_path: Path = Path(os.getenv("FAISS_INDEX_PATH", "faiss_index"))
    top_k: int = 5
    fallback_corpus: list[SourceDocument] = field(default_factory=lambda: list(DEFAULT_CORPUS))
    _vectorstore: object | None = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        self._vectorstore = self._load_vectorstore()

    def _load_vectorstore(self) -> object | None:
        if not self.index_path.exists():
            return None

        try:
            from langchain_community.vectorstores import FAISS
            from langchain_openai import OpenAIEmbeddings
        except ImportError:
            return None

        embeddings = OpenAIEmbeddings(model=os.getenv("EMBEDDING_MODEL", "text-embedding-ada-002"))
        return FAISS.load_local(
            str(self.index_path),
            embeddings,
            allow_dangerous_deserialization=True,
        )

    async def retrieve(self, query: str) -> list[SourceDocument]:
        if self._vectorstore is not None:
            return self._retrieve_faiss(query)
        return self._retrieve_fallback(query)

    def _retrieve_faiss(self, query: str) -> list[SourceDocument]:
        results = self._vectorstore.similarity_search_with_score(query, k=self.top_k)  # type: ignore[attr-defined]
        sources: list[SourceDocument] = []
        for document, score in results:
            metadata = dict(document.metadata or {})
            sources.append(
                SourceDocument(
                    source=str(metadata.get("source", "faiss_index")),
                    title=metadata.get("title"),
                    snippet=document.page_content[:700],
                    score=float(score),
                )
            )
        return sources

    def _retrieve_fallback(self, query: str) -> list[SourceDocument]:
        query_terms = _tokenize(query)
        scored: list[SourceDocument] = []
        for document in self.fallback_corpus:
            doc_terms = _tokenize(" ".join(part for part in [document.title, document.snippet] if part))
            overlap = len(query_terms & doc_terms)
            denominator = math.sqrt(max(len(query_terms), 1) * max(len(doc_terms), 1))
            score = overlap / denominator
            if hasattr(document, "model_copy"):
                scored.append(document.model_copy(update={"score": round(score, 4)}))
            else:
                scored.append(document.copy(update={"score": round(score, 4)}))

        scored.sort(key=lambda source: source.score or 0, reverse=True)
        return scored[: self.top_k]
