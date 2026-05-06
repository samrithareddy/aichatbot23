# AI-Powered Customer Support Chatbot Project Report

## Executive summary

This project implements a production-oriented customer support chatbot that combines:

- FastAPI REST and WebSocket APIs.
- Multi-turn retrieval-augmented generation over product documentation.
- LangChain, GPT-4, and FAISS integration points.
- Deterministic local fallbacks for development and tests.
- A React TypeScript customer chat interface.
- A Streamlit operations dashboard.
- Docker and AWS Lambda packaging via Mangum.

The intended production target is a 25,000+ document product corpus indexed into FAISS, GPT-4-backed intent
classification, token streaming, analytics logging, and dashboarding for support operations.

## Architecture

```text
Browser WebSocket
  -> FastAPI /ws/chat
  -> IntentClassifier
  -> Retriever (FAISS when available, local corpus fallback otherwise)
  -> ChatChain streaming generator
  -> WebSocket token, sources, and done events
  -> React Chat UI
```

### Runtime layers

| Layer | Technology | Role |
| --- | --- | --- |
| Frontend | React, TypeScript, Vite | Customer-facing streaming chat UI |
| API | FastAPI, WebSocket | REST health/metrics and persistent chat sessions |
| RAG | LangChain, GPT-4, FAISS | Retrieval, prompt assembly, and generation |
| Intent | GPT-4 function calling | Intent classification and slot extraction |
| Analytics | Postgres fallback/in-memory store | Query, latency, token, source, and escalation metrics |
| Admin | Streamlit | Observability dashboard |
| Deployment | Docker, AWS Lambda, Mangum | Containerized local and serverless runtime |

## Repository layout

```text
backend/
  main.py
  routers/
    chat.py
    health.py
  services/
    analytics.py
    chain.py
    intent.py
    retriever.py
    streaming.py
  ingestion/
    chunker.py
    ingest.py
  models/
    schemas.py
frontend/
  src/
    components/
    hooks/
    App.tsx
admin/
  dashboard.py
infrastructure/
  Dockerfile
  docker-compose.yml
  lambda_handler.py
tests/
```

## WebSocket protocol

Client to server:

```json
{"type": "query", "session_id": "session-123", "message": "Can I return this after 30 days?"}
```

Server events:

```json
{"type": "token", "data": "I "}
{"type": "sources", "data": [{"source": "docs/return-policy.md", "snippet": "..."}]}
{"type": "done", "metadata": {"session_id": "session-123", "intent": "return_policy", "latency_ms": 120}}
{"type": "error", "message": "Invalid chat payload"}
```

## Local development

### Backend

```bash
python -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Admin dashboard

```bash
streamlit run admin/dashboard.py
```

### Docker compose

```bash
docker compose -f infrastructure/docker-compose.yml up --build
```

## Building the FAISS index

Place product documentation under `data/` and run:

```bash
python -m backend.ingestion.ingest --data-dir data --output-dir faiss_index
```

The backend loads `FAISS_INDEX_PATH` at startup when the index exists. Without an index, it uses a small local
fallback corpus so developers can exercise the chat flow without external dependencies.

## AWS deployment notes

- Build the backend container from `infrastructure/Dockerfile` and push it to ECR.
- Use `infrastructure/lambda_handler.handler` as the Lambda entrypoint when deploying with Mangum.
- Store OpenAI and database credentials in AWS Secrets Manager.
- Mount the FAISS index through EFS for large indexes to reduce cold-start index loading time.
- API Gateway HTTP APIs can route REST traffic to the Lambda function.
- API Gateway WebSocket APIs should persist connection metadata in DynamoDB for production fan-out.

## Target metrics from the project brief

| Metric | Target |
| --- | --- |
| Product docs | 25,000+ |
| Intent accuracy | 92% |
| FAISS retrieval and prompt assembly P95 | <300 ms |
| End-to-end response P95 | 2.8 s |
| RAG faithfulness | 88% |
| WebSocket uptime | 99.7% |

