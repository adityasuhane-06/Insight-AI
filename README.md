# ⚡ Insight AI - Research Copilot

![Insight AI](https://img.shields.io/badge/Status-Production-success) ![Python](https://img.shields.io/badge/Python-3.12-blue) ![React](https://img.shields.io/badge/React-18.0-61dafb) ![FastAPI](https://img.shields.io/badge/FastAPI-0.109-00a393) ![LangGraph](https://img.shields.io/badge/LangGraph-AI-orange)

## 📌 Executive Summary

### 🔍 What is it?
**Insight AI** is an intelligent business research copilot designed specifically for enterprise sales professionals, account executives, and business strategists. It is a full-stack, autonomous research platform that transforms a simple company name into a comprehensive, interactive intelligence briefing.

### ⚙️ What does it do?
When provided with a company name and a meeting objective, Insight AI:
1. Autonomously crawls the web to find targeted, highly relevant information.
2. Extracts critical business metrics, recent news, and market positioning.
3. Scores the data against a strict quality threshold to ensure relevance.
4. Generates a structured executive markdown briefing.
5. Provides an interactive **Retrieval-Augmented Generation (RAG) chat interface**, allowing users to instantly query the gathered intelligence.

### 💡 Why does it exist?
Professionals often spend hours manually aggregating data from disconnected sources, reading through PR releases, and summarizing articles before high-stakes meetings. Insight AI eliminates this manual overhead. It ensures that every meeting is driven by deep, instantly accessible intelligence rather than surface-level Google searches, giving teams a massive competitive advantage.

### 🧠 How it works?
Insight AI utilizes a stateful, multi-agent workflow powered by **LangGraph**. 
- It uses the **Tavily API** to orchestrate targeted web searches.
- Extracted web content is split into chunks and embedded into **ChromaDB Managed Cloud** using **Jina Embeddings v3**.
- The **ZAI SDK (GLM-4.7-Flash)** evaluates the semantic relevance of the data. If the data quality passes our defined threshold, a dedicated Report Generator Agent compiles the final executive brief. All data flows securely through a decoupled FastAPI backend to a responsive React frontend via Server-Sent Events (SSE).

### 🎯 Primary Use Cases
- **B2B Sales Discovery:** Generating instant, highly targeted briefings on a prospect's market position, recent funding, and pain points before an introductory call.
- **Investment Due Diligence:** Quickly scraping and summarizing a startup's history and competitor landscape for venture capital analysts.
- **Executive Prep:** Providing C-level executives with immediate, structured context before strategic partnership or M&A meetings.

### 📈 Impact and Results
- **Time Saved:** Reduces meeting preparation time from 2-3 hours down to 2 minutes.
- **Higher Conversions:** Enables highly personalized, data-backed pitches that resonate deeply with prospects.
- **Centralized Knowledge:** Creates a permanent, searchable vector database of company intelligence for the entire organization.

### 🔮 What If? (Constraints & Future Resilience)
- ***What if external websites block our scraper?*** The system leverages fallback search APIs and can be easily extended to utilize proxy rotators to ensure consistent data ingestion.
- ***What if the LLM hallucinates data?*** The system enforces strict RAG constraints. The Chat UI is heavily prompted to *only* answer using the specific text chunks embedded in ChromaDB, refusing to answer if the context is missing.
- ***What if user demand scales drastically?*** The backend is fully containerized. Long-running LangGraph background tasks can be seamlessly migrated to a distributed task queue (like Celery/Redis) to support thousands of concurrent enterprise users.

---

## 🏗️ 1. High-Level System Architecture (C4 Context)

The architecture is built on a modern decoupled stack utilizing a React Single-Page Application, an asynchronous FastAPI backend, and an intelligent state-machine workflow powered by LangGraph.

```mermaid
graph TD
    Client[Web Browser] --> Vercel[Frontend: React/Vite]
    Vercel --> API[Backend: FastAPI via Render/HF]
    
    subgraph AI Engine & Workflows
        API --> LangGraph[LangGraph Orchestrator]
        LangGraph --> WebScraper[Web Scraper Agent]
        LangGraph --> Analyzer[Data Analyzer Agent]
        LangGraph --> QualityCheck[Quality Check Agent]
        LangGraph --> ReportGen[Report Generator Agent]
    end
    
    subgraph External Services
        LangGraph --> LLM[ZAI GLM-4.7-Flash API]
        LangGraph --> Tavily[Tavily Search API]
        LangGraph --> Embeddings[Jina Embeddings v3 API]
    end
    
    subgraph Data Layer
        API --> MySQL[(Aiven MySQL Database)]
        LangGraph --> Chroma[(ChromaDB Managed Cloud)]
    end
```

---

## 🧩 2. Object-Oriented Class Diagram

This diagram maps the structural building blocks of the Python application, including the Pydantic data models for State orchestration and the Database entities.

```mermaid
classDiagram
    class Session {
        +String id
        +String company_name
        +String objective
        +String status
        +String report_markdown
        +create()
        +update_status()
    }
    class ChatMessage {
        +String id
        +String session_id
        +String role
        +String content
        +save()
    }
    class ResearchState {
        +String session_id
        +List URLs
        +List Extracted_Data
        +Float quality_score
    }
    class ZaiClient {
        +String api_key
        +String model
        +generate_response()
        +get_structured_data()
    }
    class ChromaManager {
        +embed_chunks()
        +query_similar()
    }
    
    Session "1" -- "*" ChatMessage : has
    ResearchState "1" -- "1" Session : tracks
    ResearchState ..> ZaiClient : uses for evaluation
    ResearchState ..> ChromaManager : uses for RAG
```

---

## 👤 3. System Use Case Diagram

This illustrates how external actors (Users) interact with the platform to achieve specific goals, such as viewing reports or chatting with the AI.

```mermaid
graph LR
    User([Business Professional])
    User --> (Create New Research Session)
    User --> (View Executive Report)
    User --> (Chat with RAG AI)
    
    subgraph Insight AI Copilot
        (Create New Research Session) --> (Scrape Target Company Data)
        (Scrape Target Company Data) --> (Analyze & Score Quality)
        (View Executive Report) -.-> (Analyze & Score Quality)
        (Chat with RAG AI) --> (Retrieve Semantic Context via Chroma)
    end
```

---

## ⚙️ 4. Activity Diagram (Business Logic)

This represents the chronological flow of business logic from the start of the LangGraph node execution to the final report generation.

```mermaid
stateDiagram-v2
    [*] --> StartResearch
    StartResearch --> SearchWeb
    SearchWeb --> ExtractAndScrape
    ExtractAndScrape --> EmbedToVectorDB
    EmbedToVectorDB --> AnalyzeDataQuality
    
    state AnalyzeDataQuality {
        score_low --> SearchWeb : Quality Score < 0.65
        score_high --> GenerateExecutiveReport : Quality Score >= 0.65
    }
    
    GenerateExecutiveReport --> SaveToRelationalDB
    SaveToRelationalDB --> [*]
```

---

## 🔄 5. Interaction Sequence Diagram

When a user submits a research request, a stateful multi-agent LangGraph workflow is triggered. 

```mermaid
sequenceDiagram
    actor User
    participant Frontend
    participant FastAPI
    participant LangGraph
    participant ZAI_LLM
    participant ChromaDB
    
    User->>Frontend: Submit Company & Objective
    Frontend->>FastAPI: POST /api/sessions
    FastAPI->>LangGraph: Trigger Research Graph (Background)
    
    loop Until Quality Score > 0.65
        LangGraph->>Tavily: Search web for company context
        LangGraph->>WebScraper: Scrape target URLs
        WebScraper->>ChromaDB: Chunk & Embed Data (Jina V3)
        LangGraph->>Analyzer: Read & Evaluate Chunks
        Analyzer->>ZAI_LLM: Extract Value Props & Risks
        ZAI_LLM-->>Analyzer: Analysis JSON
        LangGraph->>QualityCheck: Assess Data Relevance
    end
    
    LangGraph->>ReportGen: Generate Final Markdown
    ReportGen-->>LangGraph: Report Context Saved
    LangGraph-->>FastAPI: Session Marked Completed
    FastAPI-->>Frontend: Stream SSE Event Updates
    Frontend-->>User: Display Formatted Research Report
```

---

## 🌍 6. Software Deployment Diagram

This deployment map shows exactly where and how the software nodes interact over the internet.

```mermaid
graph TD
    node1((End User Device))
    
    subgraph Vercel Edge Network
        node2[React Frontend UI]
    end
    
    subgraph Render / Hugging Face Space
        node3[FastAPI Backend Container]
        node4[LangGraph Worker Thread]
    end
    
    subgraph Managed Cloud Infrastructure
        node5[(Aiven MySQL Cluster)]
        node6[(ChromaDB Managed Vector Store)]
        node7[ZAI API Gateway]
    end
    
    node1 -->|HTTPS| node2
    node2 -->|REST API & SSE| node3
    node3 -->|SQLAlchemy Async| node5
    node3 -->|Initialize Background Task| node4
    node4 -->|gRPC/REST| node6
    node4 -->|LLM Inference Request| node7
```

---

## 🗄️ 7. Relational Data Model (ERD)

The relational database (Aiven MySQL) stores the orchestration metadata and user chat histories.

```mermaid
erDiagram
    SESSIONS {
        string id PK
        string company_name
        string website
        string objective
        string status
        string current_node
        float quality_score
        datetime created_at
    }
    
    CHAT_MESSAGES {
        string id PK
        string session_id FK
        string role
        string content
        datetime created_at
    }
    
    SESSIONS ||--o{ CHAT_MESSAGES : contains
```

---

## 🛠️ Technology Stack

| Component | Technology Used | Rationale |
|-----------|-----------------|-----------|
| **Frontend** | React, Vite, Custom CSS | Lightning-fast HMR, component-driven UI, deployed to Vercel CDN. |
| **Backend** | FastAPI, Python 3.12 | Asynchronous request handling, SSE streaming support, auto-generated OpenAPI docs. |
| **Orchestration**| LangGraph | Deterministic, stateful multi-agent workflows with built-in checkpointing. |
| **LLM Engine** | ZAI SDK (GLM-4.7-Flash)| High-performance reasoning, exceptional instruction following for backend tasks. |
| **Embeddings** | Jina Embeddings v3 | 1024-dimension high-quality semantic retrieval, effectively bypassing rate limits. |
| **Vector Store** | ChromaDB Managed Cloud| Persistent vector search with minimal operational overhead. |
| **Relational DB**| Aiven MySQL (`aiomysql`) | Scalable, cloud-native SQL storage for sessions and chat logs. |

---

## 🚀 Local Development Setup

### 1. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Or `.venv\Scripts\activate` on Windows
pip install -r requirements.txt
```

Create a `.env` file in the `backend` directory:
```env
LLM_PROVIDER=zai
LLM_MODEL=glm-4.7-flash
ZAI_API_KEY=your_zai_api_key
SEARCH_ENGINE=tavily
TAVILY_API_KEY=your_tavily_key
JINA_API_KEY=your_jina_key
DATABASE_URL=mysql+aiomysql://user:pass@host:port/defaultdb
CHROMA_API_KEY=your_chroma_key
CHROMA_TENANT=your_tenant_id
CHROMA_DATABASE=your_database_name
CORS_ORIGINS=["http://localhost:5173"]
```

Start the API:
```bash
python -m uvicorn main:app --reload --port 8000
```

### 2. Frontend Setup
```bash
cd frontend
npm install
```

Create a `.env.local` file in the `frontend` directory:
```env
VITE_API_URL=http://127.0.0.1:8000/api
```

Start the Vite development server:
```bash
npm run dev
```

---

## 🌐 Production Deployment

- **Frontend:** Deployed globally via Vercel Edge Network. Ensure `VITE_API_URL` is set to the production backend URL (with `/api` appended).
- **Backend:** Packaged via Docker and deployed to Render / Hugging Face Spaces.

*Developed as part of the ZyLabs Intern AI Engineer Assignment.*
