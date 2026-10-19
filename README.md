# Knowledge AI — RAG Assistant

> **Grounded answers over fluent guesses.**  
> A production-oriented Retrieval-Augmented Generation (RAG) web application that answers questions using uploaded documents, retrieves relevant evidence via PostgreSQL pgvector, and cites exact sources supporting its answers.

---

## 1. Project Overview & Core Principles

Knowledge AI is built around the fundamental rule that **an AI assistant must never fabricate or invent facts that are absent from source documents**. 

### Key Capabilities
- **Authentication & User Isolation**: Supabase Auth / JWT verification with hard database and repository scoping ensuring zero cross-tenant access.
- **Multi-Format Ingestion**: Full text extraction and normalization for **PDF**, **DOCX**, **TXT**, and **Markdown** documents.
- **Smart Chunking & Metadata**: Token-aware recursive text splitting preserving exact page numbers, section titles, and source filenames.
- **pgvector Vector Database**: Embeddings stored in Supabase PostgreSQL with HNSW cosine distance indexing (`vector_cosine_ops`) and custom `match_document_chunks` search procedure.
- **LangGraph Orchestrated Workflow**: Explicit typed state graph (`RAGState`) with validation, retrieval, evidence evaluation, single query refinement retry, grounded answer generation, and citation validation.
- **Verifiable Source Citations**: Every claim cites actual retrieved chunks. Clicking a citation opens a slide-over Source Drawer with exact excerpts, page numbers, and similarity metrics.
- **Honest Abstention**: If documents do not contain sufficient evidence, the assistant honestly informs the user instead of hallucinating.
- **Asynchronous Ingestion**: Long-running parsing and embedding tasks run in a decoupled background worker without blocking chat requests.
- **Streaming & Non-Streaming Chat**: Standard JSON endpoint and Server-Sent Events (SSE) streaming with citation validation.

---

## 2. Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | React 18, TypeScript (strict), Vite, Tailwind CSS, TanStack Query, React Router DOM, React Markdown, Lucide Icons |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, Pydantic v2, `pydantic-settings`, SQLAlchemy 2.0 (async), Alembic, PyPDF, python-docx |
| **AI & RAG** | Google Gemini (`gemini-2.5-flash`), `text-embedding-004` (768 dimensions), LangChain, LangGraph StateGraph |
| **Database & Vectors** | Supabase PostgreSQL 16 with `pgvector` extension (HNSW index) + isolated SQLite fallback for offline tests |
| **Deployment** | Docker, Docker Compose, Render / Railway (backend), Vercel (frontend), Supabase (database + auth) |

---

## 3. Project Structure

```
knowledge-ai/
├── frontend/                     # React + TypeScript + Vite SPA
│   ├── src/
│   │   ├── api/client.ts         # Typed API client
│   │   ├── components/           # UI components, layout, chat, citations, documents
│   │   ├── features/             # Auth & Collections context providers
│   │   ├── pages/                # Landing, Auth, Dashboard, KnowledgeBase, Chat, Settings
│   │   └── types/index.ts        # TypeScript domain models
│   ├── tests/                    # Vitest component test suites
│   ├── Dockerfile                # Multi-stage production build (node + nginx SPA)
│   ├── package.json
│   └── vite.config.ts
├── backend/                      # FastAPI + SQLAlchemy + LangGraph backend
│   ├── app/
│   │   ├── api/routes/           # system, collections, documents, chat endpoints
│   │   ├── core/                 # config (pydantic-settings), logging, security (JWT)
│   │   ├── db/session.py         # async sessionmaker & pgvector setup
│   │   ├── models/               # Profile, Collection, Document, Chunk, Conversation, Message
│   │   ├── repositories/         # Scoped database CRUD & vector similarity search
│   │   ├── services/             # Ingestion, Embeddings, Generation
│   │   ├── rag/                  # LangGraph state, nodes, graph, and grounded prompts
│   │   ├── workers/              # Background ingestion worker
│   │   └── main.py               # ASGI application entrypoint
│   ├── migrations/               # Alembic versioned migrations
│   ├── tests/                    # Unit, integration, and fixture test suites
│   ├── Dockerfile                # Production Python container
│   └── requirements.txt
├── docs/                         # Architecture, API, RAG Pipeline, Database, Security, Deployment
├── scripts/
│   ├── evaluate_rag.py           # Repeatable RAG quality benchmark
│   ├── run_local.sh              # Local development startup script
│   └── run_tests.sh              # Automated test runner script
├── docker-compose.yml            # Complete multi-container environment (pgvector, backend, frontend)
└── README.md
```

---

## 4. Local Setup & Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- (Optional) Docker & Docker Compose

### Option A: Running with Docker Compose
To launch the entire stack (PostgreSQL with pgvector, FastAPI Backend, and React Frontend):
```bash
# 1. Clone the repository and enter the directory
cd knowledge-ai

# 2. Launch all services
docker-compose up --build
```
The application will be available at:
- **Frontend**: `http://localhost:5173`
- **Backend API**: `http://localhost:8000`
- **API Documentation**: `http://localhost:8000/docs`

---

### Option B: Running Natively

#### 1. Backend Setup
```bash
cd backend

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY and SUPABASE credentials (or leave defaults for local dev mode)

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

#### 2. Frontend Setup
In a new terminal:
```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env

# Start frontend development server
npm run dev
```

Visit `http://localhost:5173` in your browser. Click **Try Demo Instant** to log in immediately without needing external cloud credentials.

---

## 5. Running Automated Tests & Benchmark

### Run All Tests via Script
```bash
./scripts/run_tests.sh
```

### Run Backend Tests (Pytest)
```bash
cd backend
.venv/bin/pytest tests/ -v
```

### Run Frontend Tests (Vitest)
```bash
cd frontend
npm test
```

### Run RAG Quality Benchmark
```bash
.venv/bin/python scripts/evaluate_rag.py
```

### Benchmark Results
| Metric | Result | Target |
|---|---|---|
| **Retrieval Hit Rate (Answerable)** | **100.0%** | > 85% |
| **Abstention Accuracy (Unanswerable)** | **100.0%** | > 95% |
| **Citation Validity Rate** | **100.0%** | 100% |
| **Average End-to-End Latency** | **29.2ms** | < 1500ms |

---

## 6. Deployment Guide

Refer to [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for step-by-step instructions:
1. **Database & Vectors**: Hosted on **Supabase** with the `vector` extension enabled.
2. **Backend**: Deployed to **Render** or **Railway** using `backend/Dockerfile`.
3. **Frontend**: Deployed to **Vercel** with SPA fallback.

---

## 7. Documentation
- [Architecture & Data Flow](docs/ARCHITECTURE.md)
- [API Endpoints Specification](docs/API.md)
- [RAG Pipeline & Grounding Rules](docs/RAG_PIPELINE.md)
- [Database Schema & Migrations](docs/DATABASE.md)
- [Security & Threat Model](docs/SECURITY.md)
- [Production Deployment](docs/DEPLOYMENT.md)

---

## License
MIT License. See [LICENSE](LICENSE) for details.
