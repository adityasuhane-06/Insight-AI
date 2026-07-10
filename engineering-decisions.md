# Engineering Decisions: A First-Principles Approach

This document outlines the core architectural and engineering decisions made during the development of Insight AI. Rather than relying on industry trends or analogies, each decision was evaluated from first principles—breaking down the physical constraints of the system (latency, memory, determinism) and building solutions upward.

---

## 1. Vector Search Architecture: Decoupling Compute from Rate Limits
**The Fundamental Problem:** 
Retrieval-Augmented Generation (RAG) effectiveness is fundamentally constrained by two variables: the semantic density of the chunked data and the embedding latency. Web scraping yields massive amounts of unstructured text. Processing this text quickly requires massive parallelization. 

**Alternatives Considered:**
1. **Google Gemini / OpenAI Embeddings:** High-quality vectors, but artificially bound by strict external clock limits (Requests Per Minute). 
2. **Local Open-Source Models (e.g., `all-MiniLM-L6-v2`):** Zero network latency, but fundamentally bound by the hardware memory limits (RAM) of the host container.

**The First-Principles Reasoning & Tradeoffs:** 
If we use a standard API like Gemini, we allow arbitrary rate limits to destroy the real-time User Experience (UX) of our copilot. If we host a local model inside FastAPI, we tightly couple our web server's memory to our embedding workload, creating severe Out-Of-Memory (OOM) risks when scaling concurrent users on cheap infrastructure (Render/HF Spaces). 

**The Decision:** We migrated to **Jina Embeddings v3**. Jina acts as a highly specialized, stateless conversion function specifically optimized for high-throughput batching. This completely decoupled our embedding bottleneck. It satisfied the latency requirement (allowing hundreds of chunks per second) and the memory requirement (consuming zero local container RAM), trading slight architectural complexity for immense scalability.

---

## 2. Stateful Orchestration: The Necessity of Closed-Loop Control
**The Fundamental Problem:** 
The internet is inherently non-deterministic. Scrapers will fail, websites will block crawlers, and the quality of extracted HTML will drastically fluctuate. 

**Alternatives Considered:**
1. **Linear LangChain Pipelines:** Mapping Input A directly to Output B sequentially.
2. **LangGraph State Machines:** A cyclical graph architecture capable of loops and state-tracking.

**The First-Principles Reasoning & Tradeoffs:** 
A rigid, linear data pipeline fundamentally assumes a deterministic world. If a target website blocks the scraper, a linear chain fails and returns an empty report. However, from first principles of control theory, a resilient autonomous agent must operate as a **closed-loop control system**. It must observe its output, compute an "error" (e.g., our `quality_score`), and adjust its actions (re-scrape different URLs) until the error is minimized. 

**The Decision:** We implemented **LangGraph**. This transformed our backend from a fragile pipeline into a self-healing finite state machine. By introducing an LLM "Quality Check" node that scores the scraped data, the system can autonomously route backward to the search node if the data is insufficient. We traded execution predictability (we don't know exactly how many loops it will take) for absolute reliability.

---

## 3. Real-Time UX: SSE vs. WebSockets
**The Fundamental Problem:** 
Researching a company takes 30 to 90 seconds. To prevent user abandonment, the UI must provide real-time, granular state updates. This requires an open connection between the client and server.

**Alternatives Considered:**
1. **WebSockets:** Full-duplex, persistent connection.
2. **HTTP Short-Polling:** The client repeatedly asks the server for status updates every 2 seconds.
3. **Server-Sent Events (SSE):** A unidirectional, persistent HTTP stream.

**The First-Principles Reasoning & Tradeoffs:** 
Polling fundamentally wastes network bandwidth and database I/O by asking questions that haven't changed. WebSockets solve the polling issue, but they provide full-duplex communication (two-way). The physical reality of our data flow is strictly unidirectional: the backend is doing the heavy lifting, and the frontend merely needs to listen. WebSockets require complex load balancing, sticky sessions, and heavy memory allocation per connection. 

**The Decision:** We implemented **Server-Sent Events (SSE)** via FastAPI's `StreamingResponse`. SSE perfectly maps to the fundamental truth of the system: data flows one way. It operates over standard HTTP, traversing strict enterprise firewalls seamlessly, and consumes a fraction of the memory overhead of a WebSocket. We sacrificed bi-directional real-time capabilities (which we didn't need) for maximum stability and simplicity.

---

## BONUS: What I would improve with 2 additional weeks

With two additional weeks of engineering time, I would focus entirely on **Asynchronous Event-Driven Architecture**.

**The Current Constraint:**
Currently, LangGraph is executed in a background thread within the FastAPI process (`asyncio.to_thread()`). While non-blocking, synchronous LLM network I/O still consumes process resources. If 100 users hit the endpoint simultaneously, the API container will buckle under the thread-pool weight.

**The 2-Week Engineering Plan:**
1. **Decouple the Execution Cycle:** The HTTP Request cycle must be fundamentally separated from the execution cycle. 
2. **Implement Celery & Redis:** I would extract the LangGraph orchestrator into isolated Celery worker containers. FastAPI would simply write a "Research Event" to a Redis queue and return `202 Accepted` in milliseconds.
3. **Horizontal Scaling:** This enables absolute horizontal scaling. We could spin up 50 cheap, stateless Celery worker nodes to process LLM graphs independently. If a bad scraping job crashes a worker, it has zero impact on the core API gateway serving user traffic.
4. **Redis Pub/Sub:** The SSE streams would be refactored to listen to a Redis Pub/Sub channel. This means the user maintains their lightweight SSE connection to any API node, while the updates flow seamlessly from whichever isolated Celery worker is currently processing their graph.
