import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
    MODEL_UNDER_TEST: str = os.getenv("MODEL_UNDER_TEST", "claude-sonnet-4-6")
    JUDGE_MODEL: str = os.getenv("JUDGE_MODEL", "claude-sonnet-4-6")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./ai_qa.db")
    HALLUCINATION_SCORE_THRESHOLD: float = float(os.getenv("HALLUCINATION_THRESHOLD", "0.5"))


settings = Settings()
