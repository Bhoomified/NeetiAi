# NeetiAi

NeetiAi is an AI-powered personal finance assistant that ingests transaction
data, automatically categorizes spending, and (eventually) helps with
budgeting, investment tracking, and conversational financial insights.

This repo is a work in progress, built incrementally and in public —
this README reflects the current state of the build, not the final vision.

---

## Vision

Most finance apps ask *you* to categorize your own spending. NeetiAi flips
that: it learns to read messy, real-world transaction data (inconsistent
merchant names, missing fields, noisy formatting — the way actual bank
statements look) and categorize it automatically, then layers budgeting,
investment tracking, and a chat assistant on top of that foundation.

---

## Tech stack

**Backend**
- FastAPI — API layer
- SQLModel — ORM + schema definitions
- SQLite (dev) → Postgres (planned) — database
- Alembic — migrations
- Uvicorn — ASGI server

**Frontend**
- Next.js 14 (App Router) + TypeScript
- Tailwind CSS

**ML**
- Prototyped in Google Colab notebooks
- Trained models wrapped as FastAPI endpoints once validated
- Synthetic data generation used to simulate realistic, noisy bank
  transaction data for training

---

## Architecture

The project is built in layers, each depending on the one below it:

```
Database schema (tables)
        ↓
Synthetic / real transaction data
        ↓
ML models (categorization, and future modules)
        ↓
FastAPI endpoints wrapping those models
        ↓
Next.js frontend calling those endpoints
```

ML models are always prototyped in a notebook first, validated on metrics,
and only then wrapped into a FastAPI router — model code never gets written
directly inside the app.

---

## Current data model

| Table                  | Purpose                                         |
|-------------------------|--------------------------------------------------|
| `User`                  | App users                                         |
| `Transaction`            | Raw + categorized spending records                |
| `Budget`                 | Per-category monthly limits                       |
| `ChatLog`                | Conversation history with the AI assistant        |
| `InvestmentWatchlist`    | Tracked investment symbols                        |
| `ModelMetadata`          | Versioning/accuracy tracking for trained models   |

---

## Project structure

```
neetiai/
├── backend/
│   ├── app/
│   │   ├── models/       # SQLModel table definitions
│   │   ├── routers/      # API endpoints
│   │   ├── schemas/      # Pydantic request/response models
│   │   ├── ml_stub.py    # Placeholder categorization logic
│   │   ├── database.py   # DB engine + session
│   │   └── main.py       # FastAPI entrypoint
│   └── venv/
├── frontend/
│   └── app/
│       └── page.tsx       # Minimal transaction UI
└── README.md
```

---

## How the ML loop works

For every ML module (categorization, and future ones):

1. **Prototype in a Colab notebook first** — get the model working, check
   metrics, before any of it touches the app.
2. **Wrap as a FastAPI endpoint** — once validated, the model logic is
   wrapped in a router with a Pydantic request/response schema.
3. **Wire to frontend** — a simple fetch call + display component, no UI
   polish at this stage, just confirming data flows end to end.
4. **Commit** — one commit per working module, not one giant commit at
   the end.

Categorization specifically depends on the synthetic data generator first
producing *realistic, noisy* data (messy merchant names, inconsistent
categories, missing values). Clean synthetic data would let the model
cheat its way to artificially high accuracy and defeat the point of the
exercise.

---

## Status

✅ Repo + backend + frontend scaffolded

✅ Database schema defined (SQLite, dev mode)

✅ Categorization stub live (rule-based, temporary)

✅ Full loop working: add transaction → auto-categorize → display

✅ CORS configured for local dev

✅ Categorization model v2 live in production: tuned XGBoost + amount feature (F1 0.9459)

✅ Resolved model deployment issues: pickled class resolution, dependency mismatch, sklearn version drift between Colab training and local serving

✅ Weekly spend forecasting live (Random Forest, beats naive baseline 8-33% across categories)

✅ Budget optimizer live (SLSQP, priority-weighted, user-set savings target per request)

✅ Full pipeline tested end-to-end: transaction → categorization → forecast → optimized budget

✅ Chatbot live: DistilBERT intent classifier (F1 0.9707) + spaCy/regex entity extraction + template engine + optional HuggingFace rephrase layer (Qwen2.5-7B) with number-integrity safety checks
🔜 Investment tracking module


---

## Running locally

**Backend**
```bash
cd backend
source venv/bin/activate
uvicorn app.main:app --reload
```
API docs available at `http://localhost:8000/docs`

**Frontend**
```bash
cd frontend
npm run dev
```
App available at `http://localhost:3000`

---

## Roadmap (high level)

1. Synthetic data generator — realistic noisy bank transaction data
2. Categorization model — trained on that noisy data, replacing the
   rule-based stub
3. Budgeting module — spend vs. limit tracking per category
4. Investment watchlist — tracked symbols + notes
5. Chat assistant — conversational layer reasoning over a user's
   categorized spending and budgets

Each module follows the same loop: notebook → endpoint → frontend wiring →
commit.
