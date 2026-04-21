"""
PageVisit Model - 埋点
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

class PageVisit(Base):
    __tablename__ = "men_page_visits"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("men_users.id", ondelete="SET NULL"), nullable=True)
    page_name = Column(String(64), nullable=False)
    session_id = Column(String(128), nullable=True)
    entrance_time = Column(DateTime(timezone=True), server_default=func.now())
    device_type = Column(String(32), nullable=True)

    user = relationship("User", back_populates="page_visits")

    def __repr__(self):
        return f"<PageVisit(id={self.id}, page={self.page_name})>"
