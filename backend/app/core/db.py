from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class TestRun(Base):
    __tablename__ = "test_runs"

    id = Column(Integer, primary_key=True, index=True)
    run_type = Column(String)  # "eval" | "security" | "hallucination"
    prompt_id = Column(String)
    category = Column(String)
    prompt_text = Column(Text)
    expected = Column(Text, nullable=True)
    model_response = Column(Text)
    score = Column(Float, nullable=True)
    passed = Column(Boolean, default=False)
    latency_ms = Column(Float, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    judge_reasoning = Column(Text, nullable=True)
    flag = Column(String, nullable=True)  # e.g. "hallucination", "injection_success", "toxic"
    model_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
