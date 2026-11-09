from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Boolean, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=True)
    mode = Column(String, default="adaptive")  # adaptive|sequential|random|weak_focus
    status = Column(String, default="active")  # active | completed
    score = Column(Float, default=0.0)
    xp_earned = Column(Integer, default=0)
    max_questions = Column(Integer, default=20)
    question_ids_json = Column(Text, default="[]")  # JSON list of question IDs in order
    recent_question_ids_json = Column(Text, default="[]")  # last N question IDs for no-repeat
    current_streak = Column(Integer, default=0)
    current_combo = Column(Integer, default=0)
    attempt_count = Column(Integer, default=0)
    correct_count = Column(Integer, default=0)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", back_populates="quiz_sessions")
    attempts = relationship("Attempt", back_populates="session", cascade="all, delete-orphan")


class Attempt(Base):
    __tablename__ = "attempts"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("quiz_sessions.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_given = Column(Text, nullable=True)
    correct = Column(Boolean, nullable=False)
    response_ms = Column(Integer, default=0)
    xp_gained = Column(Integer, default=0)
    mastery_before = Column(Float, nullable=True)
    mastery_after = Column(Float, nullable=True)
    ts = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("QuizSession", back_populates="attempts")
    user = relationship("User", back_populates="attempts")
    question = relationship("Question", back_populates="attempts")
