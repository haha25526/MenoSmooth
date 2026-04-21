"""
Lab Test Model - 体检化验记录
"""
from sqlalchemy import Column, String, Integer, Float, Date, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

class LabTest(Base):
    __tablename__ = "men_lab_tests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("men_users.id", ondelete="CASCADE"), nullable=False)
    test_date = Column(Date, nullable=False)

    # Hormone panels
    e2 = Column(Float, nullable=True)        # 雌二醇 pg/mL
    fsh = Column(Float, nullable=True)       # 促卵泡激素 mIU/mL
    lh = Column(Float, nullable=True)        # 促黄体生成素 mIU/mL
    progesterone = Column(Float, nullable=True)  # 黄体酮 ng/mL
    prolactin = Column(Float, nullable=True)     # 催乳素 ng/mL

    # Nutrients
    calcium = Column(Float, nullable=True)       # 钙 mmol/L
    vitamin_d = Column(Float, nullable=True)     # 维生素D ng/mL

    notes = Column(Text, nullable=True)
    source = Column(String(32), nullable=True)  # manual, upload
    image_url = Column(String(512), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="lab_tests")

    def __repr__(self):
        return f"<LabTest(id={self.id}, date={self.test_date})>"
