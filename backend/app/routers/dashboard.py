from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.db import get_db, TestRun

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    total = db.query(func.count(TestRun.id)).scalar() or 0
    if total == 0:
        return {"total_runs": 0, "message": "No test runs yet. POST /api/evaluate/run to generate data."}

    by_type = dict(db.query(TestRun.run_type, func.count(TestRun.id)).group_by(TestRun.run_type).all())
    avg_latency = db.query(func.avg(TestRun.latency_ms)).scalar()
    passed_count = db.query(func.count(TestRun.id)).filter(TestRun.passed.is_(True)).scalar() or 0
    pass_rate = passed_count / total if total else 0

    by_category = db.query(
        TestRun.category, func.count(TestRun.id), func.avg(TestRun.score)
    ).group_by(TestRun.category).all()

    flags = db.query(TestRun.flag, func.count(TestRun.id)).filter(TestRun.flag.isnot(None)).group_by(TestRun.flag).all()

    return {
        "total_runs": total,
        "by_run_type": by_type,
        "avg_latency_ms": round(avg_latency, 1) if avg_latency else None,
        "overall_pass_rate_pct": round(100 * pass_rate, 1) if pass_rate else None,
        "by_category": [{"category": c, "count": n, "avg_score": round(s, 2) if s else None} for c, n, s in by_category],
        "flags": dict(flags),
    }
