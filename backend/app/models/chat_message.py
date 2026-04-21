"""
Chat Message Model - AI对话记录
"""
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.database import Base

class ChatMessage(Base):
    __tablename__ = "men_chat_messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("men_users.id", ondelete="CASCADE"), nullable=False)
    session_id = Column(String(64), nullable=False)
    role = Column(String(16), nullable=False)  # user, assistant
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.role})>"
