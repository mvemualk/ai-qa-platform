# AI Quality Engineer Platform

**"GitHub Copilot for QA" — a system that automatically tests AI applications.**

Most companies now ship LLM features. Very few know how to test them systematically.
This platform runs a model-under-test through a prompt library, scores it with an
LLM-as-judge, checks for hallucinations, fires known prompt-injection attacks at it,
and reports everything on a dashboard and in CI.

![CI](https://github.com/mvemualk/ai-qa-platform/actions/workflows/ci.yml/badge.svg)

## Pipeline

```
User uploads → Prompt Library → LLM (model under test) → AI Test Engine
   → Judge LLM → Security Scanner → Hallucination Detector → Dashboard → GitHub Report
```

| Stage | What it does | Code |
|---|---|---|
| Chatbot | Streaming chat against the model under test | `backend/app/routers/chat.py` |
| Prompt Library | Categorized test cases (finance, medical, travel, coding, math, support) | `prompt_library/prompts.json` |
| AI Test Engine | Runs every prompt against the model, records latency/tokens | `backend/app/routers/evaluate.py` |
| Judge LLM | Second Claude call scores correctness/completeness/tone/safety | `backend/app/services/judge.py` |
| Hallucination Detector | Flags confident, fabricated answers to unknowable/fake-source questions | `backend/app/services/hallucination.py` |
| Security Scanner | Fires prompt-injection / jailbreak / secret-exfiltration attacks | `backend/app/services/security_scanner.py` + `prompt_library/injection_attacks.json` |
| Dashboard | React + Recharts view of pass rate, latency, flags, category scores | `dashboard/` |
| GitHub Report | CI runs the full suite on every push and uploads an HTML report artifact | `.github/workflows/ci.yml`, `scripts/render_report.py` |

## Tech stack

Python · FastAPI · Anthropic SDK · SQLAlchemy (SQLite by default) · React (Vite) · Recharts · Docker · GitHub Actions · Pytest

## Local setup

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add your ANTHROPIC_API_KEY
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

### Dashboard

```bash
cd dashboard
npm install
npm run dev
```

Dashboard: http://localhost:5173

### Run the full test suite

```bash
curl -X POST http://localhost:8000/api/evaluate/run
```

This runs every prompt in the library through the model, scores it with the judge,
runs hallucination checks on the unknowable/fake-source prompts, and fires every
injection attack — then persists results to SQLite. Refresh the dashboard (or hit
`GET /api/dashboard/summary`) to see the results.

### Run unit tests

```bash
cd backend
pytest -v
```

Unit tests mock the LLM client, so they run without an API key and are what CI
runs on every PR. The full AI eval suite (which does call the real API) runs on
`push` to `main` if `ANTHROPIC_API_KEY` is set as a repo secret.

### Docker

```bash
cp backend/.env.example backend/.env   # add your key
docker compose up --build
```

Backend on `:8000`, dashboard on `:4173`.

## API reference (core endpoints)

- `POST /api/chat` — single-turn chat completion
- `POST /api/chat/stream` — streaming chat
- `GET /api/prompts` — list prompt library test cases (optional `?category=`)
- `GET /api/prompts/injections` — list security attack payloads
- `POST /api/evaluate/run` — run the full eval + hallucination + security suite
- `GET /api/evaluate/history` — recent test run rows
- `GET /api/dashboard/summary` — aggregated metrics for the dashboard

## Roadmap / bonus features

These are deliberately out of scope for the MVP but the architecture is built to
support them without rewrites:

- **Ground-truth hallucination checks** via a search API or RAG corpus (the
  `check_hallucination` interface in `hallucination.py` is a drop-in swap point)
- **Multi-model leaderboard** — `llm_client.py` is provider-agnostic by design;
  add OpenAI/Gemini clients and compare accuracy/latency/cost side by side
- **AI Bug Reporter** — auto-file a GitHub issue via the GitHub API for any
  `flag != null` row in `evaluate/history`
- **Toxicity testing** against a moderation API + HuggingFace toxic-prompt datasets
- **Performance leaderboard** — `latency_ms`/token counts are already captured per
  run; just needs a cost-per-model lookup table and a comparison view

## Project structure

```
ai-qa-platform/
├── backend/
│   ├── app/
│   │   ├── routers/       chat, prompts, evaluate, dashboard
│   │   ├── services/      llm_client, judge, hallucination, security_scanner
│   │   └── core/          config, db
│   └── tests/             pytest suite (mocked LLM calls)
├── prompt_library/         prompts.json, injection_attacks.json
├── dashboard/               React + Vite + Recharts UI
├── scripts/                 render_report.py (CI HTML report)
├── docker/                  Dockerfile.backend, Dockerfile.dashboard
├── .github/workflows/       ci.yml
└── docker-compose.yml
```
