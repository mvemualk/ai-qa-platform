from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.db import get_db, TestRun
from app.core.config import settings
from app.routers.prompts import load_prompts, load_injections
from app.services.llm_client import complete
from app.services.judge import judge_response
from app.services.hallucination import check_hallucination
from app.services.security_scanner import run_attack

router = APIRouter(prefix="/api/evaluate", tags=["evaluate"])


@router.post("/run")
def run_full_suite(db: Session = Depends(get_db)):
    """Runs prompt-library eval + hallucination checks + security scan in one
    pass and persists every result as a TestRun row. This is what the
    dashboard and GitHub Action both call."""
    prompts = load_prompts()
    attacks = load_injections()
    results = {"eval": [], "hallucination": [], "security": []}

    for p in prompts:
        model_result = complete(p["prompt"], model=settings.MODEL_UNDER_TEST)

        if p["category"] == "hallucination" or p.get("tolerance") == "refusal_expected":
            h = check_hallucination(p["prompt"], model_result.text)
            row = TestRun(
                run_type="hallucination",
                prompt_id=p["id"], category=p["category"], prompt_text=p["prompt"],
                expected=p.get("expected"), model_response=model_result.text,
                score=1.0 - h.get("confidence", 0) if h.get("hallucinated") else 1.0,
                passed=not h.get("hallucinated", True),
                latency_ms=model_result.latency_ms,
                input_tokens=model_result.input_tokens, output_tokens=model_result.output_tokens,
                judge_reasoning=h.get("reasoning"),
                flag="hallucination" if h.get("hallucinated") else None,
                model_name=settings.MODEL_UNDER_TEST,
            )
            db.add(row)
            results["hallucination"].append({"id": p["id"], **h})
        else:
            j = judge_response(p["prompt"], p.get("expected", ""), p.get("tolerance", "semantic"), model_result.text)
            row = TestRun(
                run_type="eval",
                prompt_id=p["id"], category=p["category"], prompt_text=p["prompt"],
                expected=p.get("expected"), model_response=model_result.text,
                score=j.get("overall", 0), passed=bool(j.get("passed", False)),
                latency_ms=model_result.latency_ms,
                input_tokens=model_result.input_tokens, output_tokens=model_result.output_tokens,
                judge_reasoning=j.get("reasoning"),
                flag=None if j.get("passed") else "eval_failed",
                model_name=settings.MODEL_UNDER_TEST,
            )
            db.add(row)
            results["eval"].append({"id": p["id"], **j})

    for a in attacks:
        s = run_attack(a["attack"])
        row = TestRun(
            run_type="security",
            prompt_id=a["id"], category=a["category"], prompt_text=a["attack"],
            expected="BLOCKED", model_response=s["model_answer"],
            score=1.0 if s["status"] == "BLOCKED" else 0.0,
            passed=s["status"] == "BLOCKED",
            latency_ms=s["latency_ms"],
            flag=f"injection_{s['status'].lower()}",
            model_name=settings.MODEL_UNDER_TEST,
        )
        db.add(row)
        results["security"].append({"id": a["id"], "category": a["category"], "status": s["status"]})

    db.commit()
    return {
        "summary": _summarize(results),
        "results": results,
    }


def _summarize(results: dict) -> dict:
    eval_total = len(results["eval"])
    eval_passed = sum(1 for r in results["eval"] if r.get("passed"))
    hall_total = len(results["hallucination"])
    hall_flagged = sum(1 for r in results["hallucination"] if r.get("hallucinated"))
    sec_total = len(results["security"])
    sec_blocked = sum(1 for r in results["security"] if r["status"] == "BLOCKED")
    sec_failed = sum(1 for r in results["security"] if r["status"] == "FAIL")

    return {
        "accuracy_pct": round(100 * eval_passed / eval_total, 1) if eval_total else None,
        "hallucination_rate_pct": round(100 * hall_flagged / hall_total, 1) if hall_total else None,
        "security_blocked_pct": round(100 * sec_blocked / sec_total, 1) if sec_total else None,
        "security_attacks_succeeded": sec_failed,
        "eval_total": eval_total,
        "hallucination_total": hall_total,
        "security_total": sec_total,
    }


@router.get("/history")
def history(limit: int = 200, db: Session = Depends(get_db)):
    rows = db.query(TestRun).order_by(TestRun.created_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id, "run_type": r.run_type, "prompt_id": r.prompt_id, "category": r.category,
            "score": r.score, "passed": r.passed, "latency_ms": r.latency_ms, "flag": r.flag,
            "model_name": r.model_name, "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]
