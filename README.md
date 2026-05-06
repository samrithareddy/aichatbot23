# AI Customer Support Chatbot

Production-ready project scaffold for an AI-powered customer support chatbot using
FastAPI, WebSocket streaming, LangChain, GPT-4, FAISS, React, Streamlit, Docker,
and AWS Lambda.

The repository contains:

- FastAPI backend with REST health/metrics endpoints and WebSocket chat streaming.
- Intent classification with GPT-4 function-calling support and deterministic local fallback.
- Retrieval-Augmented Generation service backed by FAISS when an index is present.
- React TypeScript chat UI with reconnecting WebSocket client and source drawer.
- Streamlit admin dashboard for query, latency, token, accuracy, and drift metrics.
- Docker and AWS Lambda adapter configuration for containerized deployment.
- Focused tests for intent routing, retrieval fallback, and WebSocket message protocol.

See the full setup and architecture guide in [docs/project-report.md](docs/project-report.md).
