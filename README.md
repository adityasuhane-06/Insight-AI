# ZyLabs AI Research Copilot

> AI-powered sales research assistant that prepares you for any business meeting with deep company intelligence and structured briefings.

[![Built with LangGraph](https://img.shields.io/badge/AI-LangGraph-purple)](https://langchain-ai.github.io/langgraph/)
[![FastAPI](https://img.shields.io/badge/Backend-FastAPI-green)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/Frontend-React-blue)](https://react.dev/)

---

## What It Does

1. **Create a Research Session** — Enter a company name, website, and your research objective
2. **Watch the AI Work** — A 6-node LangGraph workflow runs in real time, streaming progress to your browser via SSE
3. **Get a Structured Briefing** — 9-section report including Company Overview, Products & Services, Business Signals, Discovery Questions, and more
4. **Ask Follow-Up Questions** — AI chat grounded in the research report for instant Q&A

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 18 + TypeScript + Vite |
| Styling | Vanilla CSS (dark glassmorphism theme) |
| Backend | Python 3.11 + FastAPI |
| AI Workflow | **LangGraph** (mandatory, multi-node graph) |
| LLM | Google Gemini 2.0 Flash (or OpenAI GPT-4o-mini) |
| Web Search | Tavily API (DuckDuckGo fallback) |
| Database | SQLite + SQLAlchemy async |
| Streaming | Server-Sent Events (SSE) |

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Google Gemini API key ([free at aistudio.google.com](https://aistudio.google.com/))
- Tavily API key ([free tier at app.tavily.com](https://app.tavily.com/)) — *optional, falls back to DuckDuckGo*

### 1. Clone & Setup Backend

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:
```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=your_key_here
TAVILY_API_KEY=your_key_here   # optional
```

### 3. Start the Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

API docs available at: http://localhost:8000/docs

### 4. Setup & Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Open: http://localhost:5173

---

## Project Structure

```
ZyLabs/
├── backend/
│   ├── main.py                 # FastAPI application
│   ├── config.py               # Settings (pydantic-settings)
│   ├── database.py             # SQLAlchemy async models
│   ├── models.py               # Pydantic request/response schemas
│   ├── routers/
│   │   ├── sessions.py         # CRUD: /api/sessions
│   │   ├── workflow.py         # SSE: /api/sessions/{id}/stream
│   │   └── chat.py             # Chat: /api/sessions/{id}/chat
│   ├── workflow/
│   │   ├── graph.py            # LangGraph graph compilation
│   │   ├── state.py            # ResearchState TypedDict
│   │   └── nodes/
│   │       ├── planner.py      # Node 1: Generate search queries
│   │       ├── researcher.py   # Node 2: Execute web searches
│   │       ├── analyzer.py     # Node 3: Analyze into structured JSON
│   │       ├── quality_check.py# Node 4: Score + conditional routing
│   │       ├── report_gen.py   # Node 5: Generate polished report
│   │       └── error_handler.py# Node 6: Handle failures gracefully
│   ├── services/
│   │   └── llm.py              # LLM factory (Gemini / OpenAI)
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Home.tsx        # Session list + hero
│   │   │   ├── NewSession.tsx  # Create session form
│   │   │   └── SessionDetail.tsx # Workflow + report + chat
│   │   ├── components/
│   │   │   ├── Layout.tsx      # App shell with header
│   │   │   ├── WorkflowProgress.tsx # Animated node tracker
│   │   │   ├── ReportViewer.tsx     # Structured/markdown report
│   │   │   └── ChatPanel.tsx        # Follow-up chat UI
│   │   └── hooks/
│   │       └── useSSE.ts       # SSE event source hook
│   └── package.json
├── README.md
├── architecture.md
├── product-improvements.md
└── engineering-decisions.md
```

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/sessions` | Create new session |
| GET | `/api/sessions` | List all sessions |
| GET | `/api/sessions/{id}` | Get session + report |
| DELETE | `/api/sessions/{id}` | Delete session |
| GET | `/api/sessions/{id}/stream` | **SSE: Run workflow + stream** |
| GET | `/api/sessions/{id}/chat` | Get chat history |
| POST | `/api/sessions/{id}/chat` | Send chat message |

---

## LangGraph Workflow

```
planner → researcher → analyzer → quality_check
               ↑ (retry if quality < 0.65)  ↓
               └─────────────────────────────┘
                                              ↓
                                         report_gen → END
                                              ↓
                                        error_handler → END
```

- **6 nodes** with shared `ResearchState`
- **Conditional routing** at `quality_check` (retry loop up to 2x)
- **Real-time SSE streaming** of node progress

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `gemini` | `gemini` or `openai` |
| `GEMINI_API_KEY` | — | Required for Gemini |
| `OPENAI_API_KEY` | — | Required for OpenAI |
| `TAVILY_API_KEY` | — | Optional; uses DuckDuckGo if empty |
| `DEBUG` | `false` | Enable debug logging |
| `MAX_RETRIES` | `2` | Max quality check retries |
| `QUALITY_THRESHOLD` | `0.65` | Minimum quality score (0-1) |

---

## Demo

Run locally and navigate to `http://localhost:5173`.

Example research sessions:
- Company: **Salesforce** | Objective: *Prepare for an initial sales discovery call*
- Company: **Notion** | Objective: *Research for a partnership opportunity*
