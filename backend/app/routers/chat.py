from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.llm_client import complete, stream

router = APIRouter(prefix="/api/chat", tags=["chat"])


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: list[ChatMessage]


@router.post("")
def chat(req: ChatRequest):
    history = "\n".join(f"{m.role}: {m.content}" for m in req.messages[:-1])
    last = req.messages[-1].content
    prompt = f"{history}\nuser: {last}" if history else last
    result = complete(prompt)
    return {
        "response": result.text,
        "latency_ms": result.latency_ms,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
    }


@router.post("/stream")
def chat_stream(req: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in req.messages]

    def gen():
        for chunk in stream(messages):
            yield chunk

    return StreamingResponse(gen(), media_type="text/plain")
