from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.db import init_db
from app.routers import chat, prompts, evaluate, dashboard

app = FastAPI(
    title="AI Quality Engineer Platform",
    description="Automated testing platform for LLM applications: prompt-library evals, "
                 "LLM-as-judge scoring, hallucination detection, and prompt-injection security scanning.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(prompts.router)
app.include_router(evaluate.router)
app.include_router(dashboard.router)


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/api/health")
def health():
    return {"status": "ok"}
