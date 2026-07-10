# Architecture Documentation

## 1. System Architecture Sketch

```text
       [ Web Browser (React / Vite) ]
                    |
              (REST / SSE)
                    |
                    v
       [ FastAPI Backend Server ] <============> [ Aiven MySQL Database ]
                    |
            (Background Task)
                    |
                    v
       [ LangGraph Orchestrator ]
                    |
    +---------------+---------------+
    |               |               |
[ Tavily API ]  [ ZAI LLM ]    [ ChromaDB ]
```

## 2. Layer Descriptions & Technology Choices

### Frontend Layer: React + Vite + Vanilla CSS
**What it does:** Provides a responsive, dynamic user interface where users can submit research targets, watch real-time progress updates via Server-Sent Events (SSE), and seamlessly chat with the finalized intelligence report.
**Why we chose it:** React enables highly interactive state-driven components. Vite provides blazing-fast Hot Module Replacement (HMR) during development. We opted for Vanilla CSS to achieve a deeply customized, premium "Copilot" aesthetic without the prescriptive constraints of utility frameworks like Tailwind.

### Backend API Layer: FastAPI (Python 3.12)
**What it does:** Acts as the primary API gateway. It receives user requests, writes initial states to the SQL database, kicks off long-running AI tasks in the background, and streams real-time updates back to the client.
**Why we chose it:** FastAPI is built from the ground up for asynchronous programming (`asyncio`). This is absolutely critical for this application, as it allows the server to maintain open SSE connections with multiple clients and run heavy scraping tasks without blocking the main event loop.

### AI Orchestration Layer: LangGraph + ZAI SDK (GLM-4.7-Flash)
**What it does:** Manages the complex, multi-step workflow. It controls a state machine where different "nodes" (Agents) handle web scraping, data chunking, LLM evaluation, and final report generation. 
**Why we chose it:** Traditional linear AI pipelines break down when web scraping fails or returns poor data. LangGraph provides deterministic state management, allowing our workflow to loop backward and try again if the data quality is too low. The ZAI SDK (GLM-4.7-Flash) was selected for the "brain" because of its extremely fast inference and superior instruction-following, which is crucial for reliably parsing unstructured web data into structured JSON.

### Storage Layer: Aiven MySQL + ChromaDB Managed Cloud
**What it does:** MySQL acts as the persistent system of record, storing session metadata, status flags, and user chat histories. ChromaDB acts as our high-dimensional vector store for semantic search.
**Why we chose it:** We needed a strict separation of concerns. MySQL provides ACID compliance and robust relational schemas to track application state securely. ChromaDB was chosen for the AI layer because it is purpose-built for storing text embeddings and allows for ultra-fast, nearest-neighbor semantic search during the RAG (Retrieval-Augmented Generation) chat phase.

## 3. Data Flow: From Input to Final Report

1. **Input:** The user enters a target company and a meeting objective in the React UI.
2. **Initialization:** The Frontend sends a `POST` request to FastAPI. FastAPI creates a `Session` row in MySQL, triggers the LangGraph workflow in a background thread, and immediately returns the `session_id`.
3. **Streaming State:** The Frontend opens an SSE connection (`/api/sessions/{id}/stream`), listening for live progress updates.
4. **Data Gathering:** LangGraph queries the Tavily API to find relevant URLs, scrapes the raw HTML, and uses Jina Embeddings v3 to convert the text into vectors, streaming them into ChromaDB.
5. **Quality Evaluation:** The Analyzer agent reads the newly embedded vectors and asks the ZAI LLM to evaluate if the data successfully answers the user's objective. If the data is poor, the graph loops back to step 4 to scrape different sources.
6. **Report Generation:** Once the data passes the quality threshold, the Report Generator agent pulls the aggregated context, synthesizes a final Markdown report, and saves it to MySQL.
7. **Completion:** LangGraph marks the session as "completed" and closes the SSE stream. The React UI updates instantly, displaying the report and enabling the RAG Chat interface.

## 4. Notable Tradeoffs & Constraints

* **Rate Limits vs. Throughput (Embeddings):** Initially, we attempted to embed hundreds of scraped web chunks using standard provider APIs, which resulted in severe `429 Too Many Requests` bottlenecks. **Tradeoff:** We migrated the entire embedding pipeline to *Jina Embeddings v3*, which allowed for high-throughput batch processing. This solved the crash but introduced an additional third-party API dependency to manage.
* **Synchronous Bottlenecks in Async Frameworks:** Many Python SDKs (and parts of LangChain/LangGraph) are historically synchronous. **Constraint:** To prevent these blocking calls from freezing FastAPI's asynchronous event loop (which would kill the SSE streams for the user), we had to carefully dispatch the LangGraph execution to isolated threadpools using `asyncio.to_thread`.
* **Scraper Fragility vs. Breadth:** Web scraping is inherently unpredictable due to CAPTCHAs, paywalls, and JavaScript-heavy DOMs. **Tradeoff:** Instead of building a heavy, slow Puppeteer/Selenium implementation to deeply render a single page, we opted for broad, shallow scraping via Tavily. This guarantees we get *some* relevant context quickly, prioritizing speed and stability over deep extraction.
