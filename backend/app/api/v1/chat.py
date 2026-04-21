"""
AI Chat Route
"""
import uuid
import logging
from datetime import date, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.api.deps import CurrentUser
from app.schemas import ChatMessageCreate, ChatResponse, ChatMessageResponse
from app.models.chat_message import ChatMessage
from app.services.llm import llm_service

logger = logging.getLogger(__name__)

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
    """Send message and get AI reply with full user context"""
    session_id = data.session_id or str(uuid.uuid4())

    # Save user message
    user_msg = ChatMessage(user_id=current_user.id, session_id=session_id, role="user", content=data.content)
    db.add(user_msg)

    # Get conversation history for context (last 20 messages in this session)
    result = await db.execute(
        select(ChatMessage).where(
            ChatMessage.user_id == current_user.id,
            ChatMessage.session_id == session_id,
        ).order_by(ChatMessage.created_at.asc()).limit(20)
    )
    history = result.scalars().all()
    messages = [{"role": m.role, "content": m.content} for m in history]

    # ============ Build comprehensive user profile ============
    user_profile = {
        "age": None,
        "height": float(current_user.height) if current_user.height else None,
    }

    # Basic info from birthday
    if current_user.birthday:
        user_profile["age"] = (date.today() - current_user.birthday).days // 365

    # Recent scale test results with trend analysis
    from app.models.scale_test import ScaleTest
    scale_result = await db.execute(
        select(ScaleTest).where(ScaleTest.user_id == current_user.id).order_by(ScaleTest.created_at.desc()).limit(5)
    )
    scale_tests = scale_result.scalars().all()
    if scale_tests:
        parts = ["\n用户最近的量表测试结果（按时间从近到远）："]
        for i, st in enumerate(scale_tests):
            st_type = "Kupperman量表" if st.scale_type == "kupperman" else "荷尔蒙健康评估"
            parts.append(f"- {st_type} ({st.test_date}): 总分{st.total_score}，严重程度{st.severity_level or '未知'}")
        # Trend: compare latest vs earliest
        if len(scale_tests) >= 2:
            latest = scale_tests[0].total_score
            earliest = scale_tests[-1].total_score
            if latest < earliest:
                parts.append(f"\n趋势：量表分数呈下降趋势（最新{latest} vs 最早{earliest}），症状有所改善")
            elif latest > earliest:
                parts.append(f"\n趋势：量表分数呈上升趋势（最新{latest} vs 最早{earliest}），症状有所加重")
            else:
                parts.append(f"\n趋势：量表分数保持稳定（{latest}分）")
        user_profile["scale_tests"] = "\n".join(parts)

    # Recent lab test results with trend analysis
    from app.models.lab_test import LabTest
    lab_result = await db.execute(
        select(LabTest).where(LabTest.user_id == current_user.id).order_by(LabTest.created_at.desc()).limit(5)
    )
    lab_tests = lab_result.scalars().all()
    if lab_tests:
        parts = ["\n用户最近的化验结果（按时间从近到远）："]
        for lt in lab_tests:
            items = []
            if lt.e2 is not None: items.append(f"E2={lt.e2}")
            if lt.fsh is not None: items.append(f"FSH={lt.fsh}")
            if lt.lh is not None: items.append(f"LH={lt.lh}")
            if lt.progesterone is not None: items.append(f"孕酮={lt.progesterone}")
            if lt.prolactin is not None: items.append(f"PRL={lt.prolactin}")
            if lt.calcium is not None: items.append(f"钙={lt.calcium}")
            if lt.vitamin_d is not None: items.append(f"维D={lt.vitamin_d}")
            if items:
                parts.append(f"- {lt.test_date}: {', '.join(items)}")
        # Trend for key hormones
        if len(lab_tests) >= 2:
            trends = []
            latest = lab_tests[0]
            earliest = lab_tests[-1]
            for key, label in [("e2", "E2"), ("fsh", "FSH"), ("lh", "LH"), ("calcium", "钙"), ("vitamin_d", "维D")]:
                lv = getattr(latest, key)
                ev = getattr(earliest, key)
                if lv is not None and ev is not None:
                    if lv > ev: trends.append(f"{label}上升（{ev}→{lv}）")
                    elif lv < ev: trends.append(f"{label}下降（{ev}→{lv}）")
                    else: trends.append(f"{label}稳定（{lv}）")
            if trends:
                parts.append(f"\n指标变化趋势：{', '.join(trends)}")
        user_profile["lab_tests"] = "\n".join(parts)

    # Log what context we're injecting
    logger.info(f"Chat context for user {current_user.id}: age={user_profile.get('age')}, "
                f"has_scale={'scale_tests' in user_profile}, has_lab={'lab_tests' in user_profile}")

    # ============ Call LLM with context ============
    try:
        reply = await llm_service.chat(messages, user_profile=user_profile)
    except Exception as e:
        logger.error(f"LLM error: {e}")
        await db.rollback()
        raise HTTPException(status_code=503, detail=f"AI 服务暂时不可用: {str(e)}")

    # Fallback for empty responses
    if not reply or not reply.strip():
        logger.warning(f"LLM returned empty response for user {current_user.id}")
        reply = "抱歉，我暂时无法回复。请稍后再试。"

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
