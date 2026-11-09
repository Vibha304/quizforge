from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_size = Column(Integer, default=0)
    mime_type = Column(String, default="")
    status = Column(String, default="pending")  # pending|parsing|extracting_topics|generating|ready|error
    error_message = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    structure_json = Column(Text, nullable=True)  # JSON string of parsed structure
    page_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="documents")
    topics = relationship("Topic", back_populates="document", cascade="all, delete-orphan")

    @property
    def topic_count(self) -> int:
        return len(self.topics) if self.topics else 0

    @property
    def question_count(self) -> int:
        count = 0
        for topic in (self.topics or []):
            count += len(topic.questions) if topic.questions else 0
        return count
