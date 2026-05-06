"""Application service singletons.

FastAPI dependency injection imports these objects so tests can override them
without constructing a full container framework.
"""

from __future__ import annotations

from backend.services.analytics import AnalyticsStore
from backend.services.chain import ChatChain
from backend.services.intent import IntentClassifier
from backend.services.retriever import Retriever


intent_classifier = IntentClassifier()
retriever = Retriever()
chat_chain = ChatChain()
analytics_store = AnalyticsStore()
