"""
Schemas for request/response validation
"""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID

# Auth
class SendCodeRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")

class SendCodeResponse(BaseModel):
    message: str = "Verification code sent"
    expires_in: int = 300

class PhoneAuthRequest(BaseModel):
    phone: str = Field(..., pattern=r"^1[3-9]\d{9}$")
    code: str = Field(..., min_length=4, max_length=6)

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"
    expires_in: int = 1800
    user: "UserResponse"

# User
class UserProfileUpdate(BaseModel):
    nickname: Optional[str] = Field(None, min_length=1, max_length=64)
    avatar: Optional[str] = Field(None, max_length=512)
    birthday: Optional[date] = None
    height: Optional[float] = Field(None, ge=50, le=250)

class UserResponse(BaseModel):
    id: UUID
    phone: str
    nickname: str
    avatar: Optional[str] = None
    birthday: Optional[date] = None
    gender: str
    height: Optional[float] = None
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Lab Test
class LabTestCreate(BaseModel):
    test_date: date
    e2: Optional[float] = None
    fsh: Optional[float] = None
    lh: Optional[float] = None
    progesterone: Optional[float] = None
    prolactin: Optional[float] = None
    calcium: Optional[float] = None
    vitamin_d: Optional[float] = None
    notes: Optional[str] = None
    source: Optional[str] = "manual"

class LabTestResponse(BaseModel):
    id: UUID
    user_id: UUID
    test_date: date
    e2: Optional[float] = None
    fsh: Optional[float] = None
    lh: Optional[float] = None
    progesterone: Optional[float] = None
    prolactin: Optional[float] = None
    calcium: Optional[float] = None
    vitamin_d: Optional[float] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class VisionParseResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
    confidence: Optional[float] = None
    raw_text: Optional[str] = None

# Daily Metric
class DailyMetricCreate(BaseModel):
    recorded_date: date
    weight: Optional[float] = None
    body_fat: Optional[float] = None
    temperature: Optional[float] = None
    sleep_hours: Optional[float] = None
    notes: Optional[str] = None
    source: Optional[str] = "manual"

class DailyMetricResponse(BaseModel):
    id: UUID
    user_id: UUID
    recorded_date: date
    weight: Optional[float] = None
    body_fat: Optional[float] = None
    temperature: Optional[float] = None
    sleep_hours: Optional[float] = None
    notes: Optional[str] = None
    source: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Scale Test
class ScaleTestCreate(BaseModel):
    test_date: date
    scale_type: str
    scores: Optional[Dict[str, Any]] = None
    total_score: Optional[float] = None
    severity_level: Optional[str] = None

class ScaleTestResponse(BaseModel):
    id: UUID
    user_id: UUID
    test_date: date
    scale_type: str
    scores: Optional[Dict[str, Any]] = None
    total_score: Optional[float] = None
    severity_level: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

# Chat
class ChatMessageCreate(BaseModel):
    content: str
    session_id: Optional[str] = None

class ChatMessageResponse(BaseModel):
    id: UUID
    role: str
    content: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    messages: List[ChatMessageResponse]

# Analytics
class PageViewIncrement(BaseModel):
    page_name: str
    session_id: Optional[str] = None
