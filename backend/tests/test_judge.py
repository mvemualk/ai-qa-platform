from unittest.mock import patch
from app.services import judge
from app.services.llm_client import LLMResult


def _fake_result(text):
    return LLMResult(text=text, latency_ms=5.0, input_tokens=10, output_tokens=5)


def test_judge_parses_clean_json():
    fake_json = '{"correctness": 10, "completeness": 9, "tone": 9, "safety": 10, "overall": 9.5, "passed": true, "reasoning": "matches"}'
    with patch("app.services.judge.complete", return_value=_fake_result(fake_json)):
        result = judge.judge_response("What is the capital of France?", "Paris", "exact_match", "Paris")
    assert result["passed"] is True
    assert result["overall"] == 9.5


def test_judge_handles_markdown_fenced_json():
    fenced = "```json\n{\"correctness\": 8, \"completeness\": 8, \"tone\": 8, \"safety\": 9, \"overall\": 8.2, \"passed\": true, \"reasoning\": \"ok\"}\n```"
    with patch("app.services.judge.complete", return_value=_fake_result(fenced)):
        result = judge.judge_response("Explain Kubernetes", "container orchestration", "semantic", "Kubernetes orchestrates containers")
    assert result["passed"] is True


def test_judge_handles_malformed_json_gracefully():
    with patch("app.services.judge.complete", return_value=_fake_result("not json at all")):
        result = judge.judge_response("q", "e", "semantic", "a")
    assert result["passed"] is False
    assert "reasoning" in result
