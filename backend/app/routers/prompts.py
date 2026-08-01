import json
from pathlib import Path
from fastapi import APIRouter

router = APIRouter(prefix="/api/prompts", tags=["prompts"])

LIBRARY_PATH = Path(__file__).resolve().parents[3] / "prompt_library" / "prompts.json"
INJECTIONS_PATH = Path(__file__).resolve().parents[3] / "prompt_library" / "injection_attacks.json"


def load_prompts() -> list[dict]:
    return json.loads(LIBRARY_PATH.read_text())


def load_injections() -> list[dict]:
    return json.loads(INJECTIONS_PATH.read_text())


@router.get("")
def list_prompts(category: str | None = None):
    prompts = load_prompts()
    if category:
        prompts = [p for p in prompts if p["category"] == category]
    return {"count": len(prompts), "prompts": prompts}


@router.get("/categories")
def categories():
    prompts = load_prompts()
    cats = sorted({p["category"] for p in prompts})
    return {"categories": cats}


@router.get("/injections")
def list_injections():
    return {"attacks": load_injections()}
