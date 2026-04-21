"""
AI Chat Route
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.api.deps import CurrentUser
from app.schemas import ChatMessageCreate, ChatResponse, ChatMessageResponse
from app.models.chat_message import ChatMessage
from app.services.llm import llm_service

router = APIRouter()

@router.get("/history")
async def get_history(
    current_user: CurrentUser,
    session_id: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Get chat messages"""
    query = select(ChatMessage).where(ChatMessage.user_id == current_user.id)
    if session_id:
        query = query.where(ChatMessage.session_id == session_id)
    query = query.order_by(ChatMessage.created_at.asc()).limit(50)
    result = await db.execute(query)
    return [ChatMessageResponse.model_validate(m) for m in result.scalars().all()]

@router.post("/", response_model=ChatResponse)
async def send_message(
    data: ChatMessageCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    """Send message and get AI reply"""
    session_id = data.session_id or str(uuid.uuid4())

    # Save user message
    user_msg = ChatMessage(user_id=current_user.id, session_id=session_id, role="user", content=data.content)
    db.add(user_msg)

    # Get conversation history for context
    result = await db.execute(
        select(ChatMessage).where(
            ChatMessage.user_id == current_user.id,
            ChatMessage.session_id == session_id,
        ).order_by(ChatMessage.created_at.asc()).limit(20)
    )
    history = result.scalars().all()

    messages = [{"role": m.role, "content": m.content} for m in history]

    # Build user profile for context
    user_profile = {
        "age": None,
        "height": float(current_user.height) if current_user.height else None,
    }
    if current_user.birthday:
        from datetime import date
        user_profile["age"] = (date.today() - current_user.birthday).days // 365

    # Get AI reply
    try:
        reply = await llm_service.chat(messages, user_profile=user_profile)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=503, detail=f"AI 服务暂时不可用: {str(e)}")

    # Save AI message
    ai_msg = ChatMessage(user_id=current_user.id, session_id=session_id, role="assistant", content=reply)
    db.add(ai_msg)
    await db.commit()

    # Return all messages
    result = await db.execute(
        select(ChatMessage).where(
            ChatMessage.user_id == current_user.id,
            ChatMessage.session_id == session_id,
        ).order_by(ChatMessage.created_at.asc()).limit(50)
    )
    return ChatResponse(
        reply=reply,
        session_id=session_id,
        messages=[ChatMessageResponse.model_validate(m) for m in result.scalars().all()],
    )
