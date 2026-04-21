"""
Daily Metric Model - 日常数据记录
"""
from sqlalchemy import Column, String, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

class DailyMetric(Base):
    __tablename__ = "men_daily_metrics"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("men_users.id", ondelete="CASCADE"), nullable=False)
    recorded_date = Column(Date, nullable=False)

    weight = Column(Float, nullable=True)       # kg
    body_fat = Column(Float, nullable=True)     # %
    temperature = Column(Float, nullable=True)  # 基础体温
    sleep_hours = Column(Float, nullable=True)  # 睡眠时长（小时）

    notes = Column(Text, nullable=True)
    source = Column(String(32), nullable=True)  # manual, screenshot
    image_url = Column(String(512), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="daily_metrics")

    def __repr__(self):
        return f"<DailyMetric(id={self.id}, date={self.recorded_date})>"
