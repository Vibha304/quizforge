from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Topic(Base):
    __tablename__ = "topics"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("topics.id"), nullable=True)
    name = Column(String, nullable=False)
    keywords = Column(Text, default="[]")  # JSON list of keywords
    summary = Column(Text, nullable=True)
    difficulty_prior = Column(Float, default=0.5)  # [0, 1]
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    document = relationship("Document", back_populates="topics")
    parent = relationship("Topic", remote_side=[id], back_populates="children")
    children = relationship("Topic", back_populates="parent", cascade="all, delete-orphan")
    questions = relationship("Question", back_populates="topic", cascade="all, delete-orphan")
    mastery_records = relationship("Mastery", back_populates="topic", cascade="all, delete-orphan")

    @property
    def question_count(self) -> int:
        return len(self.questions) if self.questions else 0
