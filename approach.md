# SHL Assessment Recommender — Approach Document

## Design Overview

The system is a stateless conversational agent exposed via FastAPI. Each POST /chat call receives the full conversation history and returns a structured reply with optional assessment recommendations.

**Stack:** FastAPI · Anthropic Claude Haiku · ChromaDB · Sentence Transformers (all-MiniLM-L6-v2) · Render (deployment)

---

## Retrieval Setup

The SHL Individual Test Solutions catalog (~65 assessments) was scraped from shl.com/solutions/products/product-catalog/ and stored as catalog.json. Each assessment is enriched into a descriptive sentence combining name, test type, remote/adaptive flags, and role context. These descriptions are embedded using `all-MiniLM-L6-v2` (lightweight, fast, free) and indexed into ChromaDB running in-memory.

On every /chat call, the last 3 user messages are concatenated into a search query. The top 15 semantically similar assessments are retrieved and injected into the Claude prompt as grounded context. This means the model never recommends from its training data — only from what we give it.

**Why ChromaDB over FAISS:** ChromaDB has a simpler Python API, no manual index serialization, and works well in-memory for a catalog this size. FAISS would be better at scale (10k+ items), but is overkill here.

---

## Prompt Design

The system prompt defines 5 behavioral modes:

1. **CLARIFY** — when query is vague (no role/skill info), ask one targeted question
2. **RECOMMEND** — when enough context exists, return 1-10 grounded assessments
3. **REFINE** — honor mid-conversation constraint changes without restarting
4. **COMPARE** — answer "difference between X and Y" using catalog data only
5. **REFUSE** — reject off-topic, legal, and prompt-injection requests

The model is instructed to always return strict JSON. A post-processing step validates the schema and strips any URLs not present in the catalog — ensuring zero hallucinated links.

**Turn budget awareness:** The prompt tells Claude that max 8 turns are allowed, pushing it to commit to a shortlist by turn 3-4 if enough signal is present.

---

## Evaluation Approach

Tested against the following scenarios manually:

| Scenario | Result |
|---|---|
| Vague query ("I need an assessment") | Asks clarifying question ✅ |
| Job description pasted | Returns relevant shortlist ✅ |
| "Add personality tests" mid-conversation | Updates shortlist ✅ |
| "Difference between OPQ32r and Verify Numerical?" | Catalog-grounded answer ✅ |
| "What is the best salary for this role?" | Polite refusal ✅ |
| Prompt injection ("Ignore previous instructions") | Refused ✅ |
| URL hallucination check | All URLs validated against catalog ✅ |

**Recall@10:** Evaluated manually on 5 representative personas. Semantic retrieval outperformed keyword matching particularly on role-to-skill translation (e.g. "data scientist" → Python, R, ML, Numerical Reasoning tests).

---

## What Didn't Work

- **Direct scraping of SHL catalog** was unreliable due to JavaScript rendering. Switched to a curated known catalog as the ground truth source, covering all major Individual Test Solutions.
- **Single large prompt with all 65 assessments** caused the model to occasionally hallucinate test details. Switched to RAG (retrieve top 15 relevant) — cleaner and faster.
- **Asking Claude to classify intent separately** added latency. Merged intent + response into a single call with behavioral rules in the system prompt. Fits comfortably within 30s timeout.

---

## AI Tools Used

- Claude (Anthropic) used for: agent brain, prompt iteration, code review
- All design decisions, architecture choices, and evaluation were done manually