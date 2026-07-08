# Architecture: Insight AI

## System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                       User Browser                               │
│              React 18 + Vite + TypeScript                        │
│                                                                  │
│  ┌──────────┐  ┌──────────────────┐  ┌───────────────────────┐  │
│  │  Session │  │  Session Detail  │  │      New Session      │  │
│  │   List   │  │  (SSE Streaming) │  │        Form           │  │
│  └──────────┘  └──────────────────┘  └───────────────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP + SSE
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                               │
│                   (Python 3.11)                                 │
│                                                                  │
│  ┌────────────────┐  ┌────────────────┐  ┌───────────────────┐  │
│  │  /api/sessions │  │ /api/sessions/ │  │  /api/sessions/   │  │
│  │  (CRUD)        │  │  {id}/stream   │  │  {id}/chat        │  │
│  │                │  │  (SSE + Graph) │  │  (LLM Q&A)        │  │
│  └────────────────┘  └───────┬────────┘  └───────────────────┘  │
└──────────────────────────────┼──────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                   LangGraph Workflow                             │
│                                                                  │
│  planner → researcher → analyzer → quality_check                 │
│                ↑ (retry)               │                         │
│                └───────────────────────┘                         │
│                                        ↓                         │
│                                   report_gen → END               │
│                                        ↓                         │
│                                  error_handler → END             │
└──────────────────────────────────────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────────┐
          ▼                    ▼                         ▼
┌─────────────────┐  ┌─────────────────┐   ┌───────────────────┐
│  Google Gemini  │  │  Tavily Search  │   │  SQLite Database  │
│  (LLM)          │  │  (Web Search)   │   │  (Persistence)    │
└─────────────────┘  └─────────────────┘   └───────────────────┘
```

---

## Layer Descriptions

### Frontend — React 18 + Vite + TypeScript

The frontend is a single-page application built with React 18 and Vite. I chose Vite over Create React App for its dramatically faster dev server and HMR. TypeScript provides type safety across API boundaries.

Key design choices:
- **Vanilla CSS with CSS Modules** — No CSS framework overhead. Each component has its own `.module.css` file providing encapsulated styles.
- **Server-Sent Events (SSE)** — The `useSSE` hook wraps the native `EventSource` API to stream workflow progress in real time. SSE was chosen over WebSockets because the communication is one-directional (server → client only during workflow execution), making SSE a simpler and more appropriate fit.
- **React Router v6** — Nested routes with a shared `Layout` component.
- **Optimistic updates** in chat — User messages appear instantly before the API response to reduce perceived latency.

### Backend — Python + FastAPI

FastAPI was chosen for its async-first design (critical for SSE streaming), automatic OpenAPI documentation, and Pydantic validation. The async SQLAlchemy engine with aiosqlite allows non-blocking database operations alongside streaming responses.

The backend is organized into:
- `routers/` — thin HTTP layer (no business logic)
- `workflow/` — all LangGraph logic isolated from HTTP concerns
- `services/` — shared infrastructure (LLM factory)

The LLM service uses `lru_cache` so the model is initialized only once and reused across requests.

### LangGraph Workflow — AI Research Engine

LangGraph was mandatory and is the core of the product. The workflow implements a stateful directed graph with 6 nodes:

1. **planner_node** — Given company + objective, the LLM generates 7 targeted search queries. Has a hardcoded fallback if LLM parsing fails.
2. **research_node** — Runs all queries concurrently (asyncio) with a semaphore limiting concurrency to 3 to avoid rate limits. Supports Tavily (primary) and DuckDuckGo (fallback).
3. **analysis_node** — Passes all raw research to the LLM with a strict JSON schema prompt covering all 9 report sections.
4. **quality_check_node** — Scores the analysis using a hybrid approach: a fast heuristic (word counts, list lengths) and an LLM judge. If the heuristic score is ≥ 0.85, the LLM call is skipped entirely to save tokens.
5. **report_gen_node** — Formats the analysis into polished Markdown, then uses a second LLM call to polish the language for professional quality.
6. **error_handler_node** — Captures any unhandled exceptions, preserves partial data, and sets status to `failed`.

**Conditional routing** at `quality_check_node` implements a retry loop:
- `score ≥ 0.65` OR `retry_count ≥ 2` → `report_gen`
- `score < 0.65` AND retries remaining → `increment_retry` → `researcher` (re-runs search)
- Hard error → `error_handler`

### Storage — SQLite + SQLAlchemy Async

SQLite was chosen for zero-infrastructure simplicity appropriate for an intern assignment. The schema has two tables: `research_sessions` (stores full report markdown + JSON) and `chat_messages` (stores conversation history). The async engine allows database operations to run without blocking the event loop during SSE streaming.

---

## Data Flow

1. **User submits** company name, website, and objective via the React form
2. **POST /api/sessions** creates a `ResearchSession` record in SQLite (status: `pending`)
3. **Frontend navigates** to `/sessions/{id}` and automatically opens an SSE connection to `GET /api/sessions/{id}/stream`
4. **FastAPI** starts the LangGraph graph via `graph.astream()` inside the SSE generator
5. **Each node** completes and emits its output; FastAPI serializes a progress event as `data: {...}\n\n`
6. **React `useSSE` hook** parses each event and updates the `WorkflowProgress` component in real time
7. **On completion**, FastAPI saves the final report to SQLite; frontend reloads the session and switches to the report tab
8. **Chat** sends `POST /api/sessions/{id}/chat` with the user's message; FastAPI calls the LLM with the full report as system context

---

## Notable Tradeoffs & Constraints

**SQLite vs. PostgreSQL** — SQLite provides zero-infrastructure convenience but would not work in a multi-process production deployment. For production, this should be swapped for PostgreSQL with an async adapter (asyncpg).

**SSE vs. WebSockets** — SSE is simpler for unidirectional streaming but does not support bidirectional communication. If real-time chat streaming (token-by-token) were required, WebSockets would be needed. Chat currently returns full responses.

**LLM quality vs. latency** — Running 3 sequential LLM calls (planner + analyzer + report_gen) plus an optional quality check adds significant latency (30–90 seconds depending on provider). The quality check heuristic optimization (skip LLM if heuristic ≥ 0.85) saves ~2–5 seconds on most runs.

**DuckDuckGo fallback** — The free DuckDuckGo search is less reliable and rate-limited compared to Tavily. It is only used when no Tavily key is configured and is not recommended for production.

**Retry loop** — The quality check retry loop can add significant latency. The default of `MAX_RETRIES=2` with a `QUALITY_THRESHOLD=0.65` was tuned to balance quality vs. speed.
