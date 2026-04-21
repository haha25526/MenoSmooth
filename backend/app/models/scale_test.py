"""
Scale Test Model - 量表测试记录
"""
from sqlalchemy import Column, String, Float, Date, DateTime, ForeignKey, Text, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

class ScaleTest(Base):
    __tablename__ = "men_scale_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("men_users.id", ondelete="CASCADE"), nullable=False)
    test_date = Column(Date, nullable=False)
    scale_type = Column(String(32), nullable=False)  # kupperman, hormone_health
    scores = Column(JSONB, nullable=True)            # 各题得分
    total_score = Column(Float, nullable=True)
    severity_level = Column(String(32), nullable=True)  # 轻度/中度/重度

    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="scale_tests")

    def __repr__(self):
        return f"<ScaleTest(id={self.id}, type={self.scale_type}, date={self.test_date})>"
