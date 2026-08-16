# SentinelIQ — AI-Powered Threat Intelligence Platform

> Ask your SOC questions in plain English. Get answers grounded in live CVE and SIEM data.

[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow)](LICENSE)

## What it does

SentinelIQ ingests CVE/NVD feeds, MITRE ATT&CK reports, and Elastic SIEM logs, embeds them into a vector store, and exposes a RAG pipeline so security analysts can ask natural language questions and get grounded, cited answers.

**Example query:** *"Are there any critical CVEs affecting our Docker stack in the last 14 days?"*

**Example answer:** *"Yes — CVE-2024-21626 (CVSS 8.6) allows container breakout via runc. Remediation: upgrade runc to ≥1.1.12. Source: NVD 2024-02-01."*

---

## Architecture

```
NVD/CVE Feeds ─┐
MITRE ATT&CK  ─┼─▶ Loaders ─▶ Normaliser ─▶ Chunker ─▶ Embeddings ─▶ Vector Store
Elastic SIEM  ─┘                                                                            │
                                                                                            ▼
React Dashboard ◀── FastAPI (/query /alerts /cve) ◀── RAG Chain (GPT-4o) ◀── Retriever
```

## Tech Stack

| Layer | Tool |
|---|---|
| Ingestion | httpx + custom loaders |
| Scheduling | APScheduler |
| Embeddings | OpenAI `text-embedding-3-small` (with deterministic fallback) |
| Vector store | In-memory / Pinecone / FAISS |
| LLM | GPT-4o via `openai` SDK (with offline fallback) |
| SIEM | Elasticsearch Python client (with offline sample fallback) |
| Backend | FastAPI + Pydantic v2 |
| Frontend | React 18 + Vite |
| Infra | Docker Compose |

---

## Quickstart

### 1. Clone & configure

```bash
git clone https://github.com/YOUR_USERNAME/sentineliq.git
cd sentineliq
copy .env.example .env
# Edit .env with your API keys (OpenAI, Pinecone, etc.)
```

### 2. Run locally

```bash
# Backend
python -m venv .zzzzzzzzzzz
.venv\Scripts\Activate.ps1  # or: source .venv/bin/activate
pip install zzz-r requirements.txt
pip install -e .
pytest -q
python -m uvicorn main:app --reload

# Frontend (in a separate terminal)
cd frontend
npm install
npm run dev
```

- **API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Frontend:** http://localhost:5173

### 3. Trigger initial ingestion

```bash
python scripts/ingest_now.py
```

### 4. Run with Docker Compose

```bash
docker-compose up --build
```

This starts PostgreSQL, Redis, Elasticsearch, the FastAPI backend, and the React frontend.

---

## Project Structure

```
sentineliq/
├── ingestion/          # Data loaders & normaliser
│   ├── nvd_loader.py    # NVD CVE REST API v2 fetch + normalize
│   ├── mitre_loader.py  # MITRE ATT&CK STIX fetch
│   └── normaliser.py    # CVE and technique to document
├── rag/                # Embedding, vector store, RAG chain
│   ├── chunker.py       # Text splitting
│   ├── embedder.py      # OpenAI + fallback embeddings
│   ├── vectorstore.py   # In-memory / Pinecone / FAISS backends
│   ├── llm.py           # OpenAI chat completion wrapper
│   ├── prompts.py       # Prompt templates
│   ├── chain.py         # RAG answer + correlation (offline capable)
│   └── retriever.py     # (optional) semantic retrieval
├── siem/               # Elastic SIEM integration
│   ├── client.py        # Elasticsearch client with sample fallback
│   ├── log_parser.py    # (optional) Log parsing utilities
│   └── correlator.py    # CVE correlation + persistence
├── api/                # FastAPI application
│   ├── auth.py          # Token auth + require_auth dependency
│   ├── schemas.py       # Pydantic models
│   └── routes/
│       ├── auth.py      # POST /token
│       ├── query.py     # POST /query
│       ├── stream.py    # POST /query/stream (SSE)
│       ├── alerts.py    # GET /alerts, POST /alerts/correlate, POST /alerts/persist
│       ├── dashboard.py # GET /alerts, GET /cves
│       └── ingest.py    # POST /ingest
├── frontend/           # React + Vite dashboard
│   ├── src/main.jsx     # Chat, alerts, CVE explorer, dark/light mode
│   ├── vite.config.js   # Dev server proxy to backend
│   ├── Dockerfile       # Multi-stage build
│   └── package.json
├── scripts/            # One-off utilities
│   ├── init_db.py      # SQLAlchemy async models + DB helpers
│   └── ingest_now.py   # Run an ingestion cycle
├── tests/              # 16 tests, all passing
├── docker-compose.yml
├── Dockerfile
├── Makefile
├── .env.example
├── .gitignore
├── .dockerignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## Environment Variables

See `.env.example` for all required variables.

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | OpenAI API key (required for LLM + real embeddings) |
| `PINECONE_API_KEY` | Pinecone API key (optional — falls back to in-memory store) |
| `PINECONE_ENVIRONMENT` | Pinecone environment (optional) |
| `ELASTIC_URL` | Elasticsearch URL |
| `ELASTIC_USERNAME` | Elastic username (optional) |
| `ELASTIC_PASSWORD` | Elastic password (optional) |
| `SECRET_KEY` | Secret for auth token validation |
| `ENV` | `development` (dev, auth bypass) or `production` (auth enforced) |
| `VECTORSTORE` | `pinecone`, `faiss`, or `in-memory` |
| `LLM_MODEL` | OpenAI model name (default: `gpt-4o-mini`) |

---

## API Endpoints

| Method | Path | Description | Auth |
|---|---|---|---|
| GET | `/health` | Live service health checks (API, DB, Redis, ES, vectorstore) | Public |
| POST | `/token` | Issue bearer token (uses `SECRET_KEY`) | Public |
| POST | `/query` | RAG answer (non-streamed) | Bearer* |
| POST | `/query/stream` | RAG answer as Server-Sent Events (SSE) stream | Bearer* |
| GET | `/alerts` | Recent SIEM/security alerts | Bearer* |
| POST | `/alerts/correlate` | Correlate a log event to CVEs | Bearer* |
| POST | `/alerts/persist` | Correlate + persist an alert to DB | Bearer* |
| POST | `/ingest` | Trigger ingestion cycle | Public |
| GET | `/cves` | Recent CVEs (DB or sample) | Public |

\* Auth is bypassed in development (`ENV=development`); in production it is enforced.

---

## Roadmap

- [x] Phase 1: NVD + MITRE ATT&CK ingestion
- [x] Phase 2: OpenAI embeddings + vector store (Pinecone, FAISS, in-memory fallback)
- [x] Phase 3: RAG pipeline (GPT-4o with offline fallback)
- [x] Phase 4: Elastic SIEM correlation engine (offline sample fallback included)
- [x] Phase 5: FastAPI backend (query, stream, alerts, token auth, health)
- [x] Phase 6: React dashboard (Vite proxy + SSE streaming)
- [x] Phase 7: Docker Compose with all services

---

## Certifications Applied

- **Google Cybersecurity** — SIEM integration, log analysis
- **IBM AI Engineering** — RAG pipeline, embeddings
- **Elastic SIEM** — Elasticsearch integration
- **Fortinet NSE** — Threat categorisation logic

---

## License

MIT
