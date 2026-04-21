"""
User Model
"""
from sqlalchemy import Column, String, Integer, Float, Boolean, Date, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

class User(Base):
    __tablename__ = "men_users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone = Column(String(20), unique=True, nullable=False)
    nickname = Column(String(64), nullable=False, default="更年期姐妹")
    avatar = Column(String(512), nullable=True)
    birthday = Column(Date, nullable=True)
    gender = Column(String(8), nullable=False, default="female")
    height = Column(Numeric(5, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    lab_tests = relationship("LabTest", back_populates="user", cascade="all, delete-orphan")
    daily_metrics = relationship("DailyMetric", back_populates="user", cascade="all, delete-orphan")
    scale_tests = relationship("ScaleTest", back_populates="user", cascade="all, delete-orphan")
    page_visits = relationship("PageVisit", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, phone={self.phone})>"
