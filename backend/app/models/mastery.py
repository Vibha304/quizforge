from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Float, Text, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Mastery(Base):
    __tablename__ = "mastery"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    topic_id = Column(Integer, ForeignKey("topics.id"), nullable=False)
    p_L = Column(Float, default=0.3)  # BKT mastery probability [0, 1]
    attempts_count = Column(Integer, default=0)
    history_json = Column(Text, default="[]")  # JSON list of {ts, p_L, correct}
    last_attempted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_mastery_user_topic"),
    )

    # Relationships
    user = relationship("User", back_populates="mastery_records")
    topic = relationship("Topic", back_populates="mastery_records")

    @property
    def is_weak(self) -> bool:
        return self.p_L < 0.6 and self.attempts_count >= 3

    @property
    def is_mastered(self) -> bool:
        return self.p_L >= 0.9
