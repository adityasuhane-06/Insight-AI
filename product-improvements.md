# Product Improvements — Insight AI

## Current Product Weaknesses

### 1. No Real-Time Web Access During Chat
The follow-up chat is grounded only in the static research report generated at session creation time. If a user asks "What did they announce last week?" the AI cannot retrieve fresh information — it can only reference the (potentially stale) research from the workflow run. The report becomes outdated as soon as business conditions change.

### 2. Single Research Depth — No Source Verification
The current workflow trusts web search snippets at face value. There is no source credibility scoring, deduplication, or cross-referencing. A single inaccurate news article can corrupt the entire analysis. There is also no ability to go deeper on specific sections (e.g., "I want more detail on their pricing model").

### 3. No Export or Sharing
After generating a high-quality briefing, there is no way to export it as a PDF, share it via link, or push it to a CRM (Salesforce, HubSpot). Sales reps cannot include the report in meeting prep emails or share it with colleagues without copy-pasting.

### 4. No Collaborative or Team Features
Research sessions are private to a single user's local instance. There is no concept of shared workspaces, team accounts, or the ability to annotate or comment on a briefing. Sales teams cannot build on each other's research.

### 5. Workflow Is a Black Box Until Complete
While SSE streams node names, the user cannot see intermediate outputs (e.g., the actual search queries planned, the raw research snippets collected). Users have no visibility into *why* the quality check failed or *what specific information* was missing. This reduces trust and makes debugging difficult.

### 6. No Scheduled Re-Research
There is no mechanism to automatically re-run research on a schedule (e.g., weekly) and notify the user when significant new business signals are detected. Users must manually trigger research each time.

### 7. LLM Provider Lock-In at Configuration Time
Switching between Gemini and OpenAI requires editing the `.env` file and restarting the server. There is no per-session model selection or A/B testing capability.

### 8. No Authentication or Multi-User Support
The application has no authentication layer. Any user with access to the URL can read, run, or delete any session. There is no concept of user accounts, ownership, or access control.

---

## Top 3 Improvements to Build Next

### Priority 1: Export & CRM Integration

**Why first:** This is the highest-impact feature for immediate user value. A research briefing is only useful if it can be acted upon. Right now, users generate a great report and then manually copy-paste it into emails or CRM notes — a frustrating workflow.

**What to build:**
- One-click PDF export (Puppeteer or WeasyPrint)
- Markdown copy-to-clipboard
- Native HubSpot and Salesforce integrations via OAuth — push the full report as a note or attachment on the contact/account record
- Shareable link with read-only view (no auth required for sharing)

**Success metric:** % of completed sessions that result in an export or CRM push action.

### Priority 2: Transparent Intermediate Outputs

**Why second:** Trust and control are prerequisites for widespread adoption. Sales teams need to trust the tool's output before betting a deal on it.

**What to build:**
- Expandable "Research Sources" panel showing the actual queries run and top 3 snippets per query
- Quality check breakdown: show which sections scored low and why
- "Dig deeper" button per report section: triggers a targeted follow-up search on that specific topic (e.g., "Tell me more about their pricing") and appends to the report
- Source quality score and link verification

**Success metric:** Session abandonment rate (proxy: sessions where user opens report but immediately navigates away without reading).

### Priority 3: Scheduled Research Alerts

**Why third:** Retention and stickiness. The product's value compounds over time if users can be notified when something changes about their target accounts.

**What to build:**
- "Monitor this company" toggle per session — re-runs research weekly
- AI-powered diff: compares new research vs. previous report and highlights significant changes
- Email digest (Resend or SendGrid) with a summary of changes across monitored accounts
- Push notification to browser and Slack integration

**Success metric:** 30-day retention rate and number of "monitoring" sessions per active user.

---

## Bonus: Business Thinking

### Who Buys, Who Uses, Why They Pay

**Buyer:** Sales VP or RevOps Manager at a B2B software company (50–500 employees). They purchase team licenses as part of the sales enablement budget.

**User:** Individual Account Executive or Business Development Rep. They use it before every first meeting and quarterly business review.

**Why they pay:** Preparing for a single enterprise sales meeting typically takes an AE 2–4 hours of manual research (LinkedIn, news, competitor sites, annual reports). This tool reduces that to 3 minutes. If a company closes a $100K deal 2x faster because their AE was better prepared, the $50/month per seat pays for itself in the first week.

### Success Metrics

| Metric | Target |
|--------|--------|
| Research sessions per user/week | ≥ 5 |
| Report completion rate | ≥ 85% |
| Chat messages per completed session | ≥ 3 |
| Time-to-first-report (p50) | < 90 seconds |
| 30-day user retention | ≥ 60% |
| NPS | ≥ 40 |

### Biggest Cost, Scaling, and Reliability Risks

**Cost:** LLM costs scale linearly with usage. Running 3 LLM calls per research session at ~10,000 tokens each = ~30,000 tokens/session. At Gemini pricing ($0.075/1M tokens), this is $0.002/session — very cheap now but will require token budgeting at scale. The report polish pass is the most expensive and could be made optional.

**Scaling:** The current SQLite database becomes a bottleneck above ~10 concurrent users. LangGraph workflow execution is CPU/memory-intensive. Horizontally scaling requires moving to PostgreSQL + a task queue (Celery + Redis or AWS SQS) to offload workflow execution from the web process.

**Reliability:** The workflow depends on three external APIs (LLM + search + optional Tavily). Any of these failing mid-run causes a partial failure. The current error_handler_node catches these, but the user experience degrades. Solution: add retry logic with exponential backoff at the HTTP client level for each external call.

### Feature to Remove

**Remove:** The DuckDuckGo fallback search. While useful for local development without a Tavily key, it produces significantly lower quality results and creates a false sense of security. A user without Tavily thinks the tool is working when it's actually producing lower-quality research. It's better to hard-fail with a clear "Please configure TAVILY_API_KEY" message than to silently produce mediocre output.

### Feature to Add

**Add:** **Meeting Recording Integration.** Allow users to upload a call recording (e.g., from Zoom or Gong) after the meeting. The AI transcribes it, extracts key insights and commitments, and automatically updates the session with a "post-meeting summary" section. This closes the research loop and makes the tool essential for both pre- and post-meeting workflows — dramatically increasing daily active use.

### If I Owned This Product

**First change:** Add authentication and team workspaces. Without auth, the product is a demo, not a product. Every other improvement (sharing, collaboration, CRM integration, billing) is blocked behind user identity. I would ship a simple email/password auth with team invites in week 1, even if rough around the edges.
