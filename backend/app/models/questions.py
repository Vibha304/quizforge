from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    type = Column(String, nullable=False)  # mcq | true_false | short_answer
    difficulty = Column(String, nullable=False)  # easy | medium | hard
    bloom = Column(String, default="remember")  # remember|understand|apply|analyze|evaluate|create
    stem = Column(Text, nullable=False)
    options = Column(Text, nullable=True)  # JSON list for MCQ
    answer = Column(Text, nullable=False)
    explanation = Column(Text, default="")
    source_snippet = Column(Text, nullable=True)
    status = Column(String, default="active")  # active | draft | archived
    embedding = Column(Text, nullable=True)  # JSON list of floats (stored as text)
    time_limit_ms = Column(Integer, default=30000)  # default 30 seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    topic = relationship("Topic", back_populates="questions")
    attempts = relationship("Attempt", back_populates="question")
