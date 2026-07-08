# Engineering Decisions — ZyLabs AI Research Copilot

## Decision 1: LangGraph Graph Structure — Retry Loop vs. Simple Pipeline

### The Decision
Instead of building a simple linear pipeline (`planner → researcher → analyzer → report_gen`), I implemented a **quality gate with a conditional retry loop** at the `quality_check_node`.

### Alternatives Considered

**A) Simple linear pipeline (no retry):** The simplest possible LangGraph implementation — 4 nodes in sequence, always producing output regardless of quality. Fast, predictable, easy to debug.

**B) Parallel research branches:** Run multiple specialized research sub-graphs in parallel (one for product info, one for news, one for financials) and merge results. Maximum coverage, but complex state management and hard to implement with LangGraph's current graph API.

**C) Human-in-the-loop confirmation:** Add a checkpoint after `quality_check` where execution pauses and waits for user confirmation before proceeding. Technically possible with LangGraph's `interrupt_before` feature, but introduces latency and UX complexity.

### What I Chose and Why
Option A was rejected because quality variance in web search results is high — a well-planned search sometimes returns mostly irrelevant content, and blindly generating a report from poor research would produce unreliable output that damages user trust.

I implemented the retry loop (between A and B) because it provides meaningful quality improvement in cases where the first research pass underperforms, while keeping the graph complexity manageable. The hybrid quality scoring (heuristic + LLM) ensures the retry triggers only when truly needed, not on minor imperfections.

### Tradeoffs Made
- **Latency:** A retry adds 30–60 seconds to the workflow. Mitigated by capping retries at `MAX_RETRIES=2`.
- **Token cost:** Each retry re-runs the analyzer LLM call. Could be optimized by only re-running search for *specific missing sections* rather than the full analysis.
- **Complexity:** The conditional routing logic needed to correctly handle the `increment_retry` node between `quality_check` and `researcher` took careful graph edge definition.

---

## Decision 2: SSE vs. WebSockets for Real-Time Streaming

### The Decision
I used **Server-Sent Events (SSE)** via FastAPI's `StreamingResponse` to stream workflow progress from backend to frontend.

### Alternatives Considered

**A) Polling:** Frontend polls `/api/sessions/{id}` every 2–3 seconds. Simple to implement, works everywhere, no connection management. But introduces up to 3-second latency on node completion and hammers the server with requests.

**B) WebSockets:** Full-duplex real-time connection. Supports bidirectional communication, better suited if we needed to send control signals during workflow execution (e.g., "pause" or "cancel").

**C) SSE (chosen):** Unidirectional server-push over a standard HTTP connection. Automatically reconnects on disconnection, works through HTTP/2, supported natively in all modern browsers with the `EventSource` API.

### What I Chose and Why
SSE is the right fit here because:
1. The workflow communication is strictly server → client (we never need to send data mid-stream from client to server)
2. No WebSocket library overhead
3. Works through standard HTTP proxies and load balancers without configuration
4. The `EventSource` API is natively available in React without dependencies

### Tradeoffs Made
- **No cancellation:** Because SSE is unidirectional, there is no built-in mechanism to cancel a running workflow. The user must wait for completion or close the page. In a production version, I would add a cancel endpoint (`DELETE /api/sessions/{id}/stream`) that signals a stop via an asyncio `Event`.
- **Connection limits:** Browsers limit SSE connections to ~6 per origin. For a multi-tab user this could be an issue, though uncommon in practice.
- **Backpressure:** If the LangGraph graph emits state faster than the SSE generator can flush it, events could queue up. The `await asyncio.sleep(0.05)` between events mitigates this.

---

## Decision 3: Hybrid Quality Scoring — Heuristic + LLM Judge

### The Decision
The `quality_check_node` uses a **two-stage scoring approach**: a fast heuristic first, and an LLM judge only if the heuristic score is insufficient (< 0.85).

### Alternatives Considered

**A) LLM-only scoring:** Use the LLM to score every time. Most accurate but adds a full LLM call to every workflow run even when the analysis is already excellent. 5–10 extra seconds and additional token cost per run.

**B) Heuristic-only scoring:** Just count words and list lengths. Very fast and free, but crude — a verbose but low-quality analysis might score high, while a concise but accurate one might score low.

**C) Hybrid (chosen):** Heuristic first. If score ≥ 0.85, trust it and skip the LLM call. If score < 0.85, call the LLM for a more nuanced evaluation and blend the two scores (70% LLM, 30% heuristic).

**D) Embedding similarity:** Compare the analysis against a "gold standard" template using cosine similarity of embeddings. More principled, but adds the embedding model dependency and complexity.

### What I Chose and Why
The hybrid approach gives the best balance:
- Most runs have good-quality analysis (the LLM analyzer is well-prompted) → heuristic alone suffices for ~70% of runs, saving latency and cost
- When research is genuinely poor (few results, vague content), the heuristic catches it (very low word counts / list lengths)
- The LLM judge is reserved for borderline cases (score 0.5–0.85) where human-like judgment is most valuable

### Tradeoffs Made
- **Score calibration:** The 0.85 threshold for skipping LLM scoring was chosen empirically. A more rigorous approach would run both on a test set and tune the threshold to minimize LLM calls while maintaining accuracy.
- **Blending weights:** The 70/30 LLM/heuristic blend was chosen to trust LLM judgment more, but this means an LLM hallucinating a high score could override a low heuristic score. In practice, the LLM prompt is directive enough to prevent this.
- **Latency inconsistency:** Workflow runtime varies depending on whether the LLM quality check is triggered, making it hard to give users an ETA.

---

## What I Would Improve With 2 Additional Weeks

### Week 1
1. **Authentication** — Add JWT-based auth with `python-jose` + `passlib`. Create `users` table, add login/register pages. Gate all session endpoints with `current_user` dependency.
2. **PostgreSQL migration** — Replace SQLite with PostgreSQL via `asyncpg` + Alembic migrations. This unblocks horizontal scaling.
3. **Background task queue** — Move LangGraph workflow execution to Celery workers (with Redis broker) so web processes only handle HTTP, not long-running AI tasks. This also enables proper workflow cancellation.

### Week 2
4. **PDF export** — Add `weasyprint` or `playwright` PDF generation endpoint. This is the #1 requested feature from any sales team.
5. **Streaming token output** — Use LangChain's streaming callbacks to stream LLM tokens back through SSE as they're generated, rather than waiting for full node completion. This dramatically improves perceived performance.
6. **Comprehensive test suite** — Unit tests for each LangGraph node with mocked LLM/search responses. Integration tests for the SSE endpoint. This is the biggest missing engineering quality gap in the current submission.
