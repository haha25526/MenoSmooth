"""
Analytics Route - Page view tracking
"""
from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, date
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.page_visit import PageVisit
from app.core.security import verify_access_token
from app.schemas import PageViewIncrement
from pydantic import BaseModel

router = APIRouter()

class SummaryItem(BaseModel):
    page_name: str
    date: str
    pv: int
    uv: int

class SummaryResponse(BaseModel):
    total_pv: int
    total_uv: int
    pages: list[SummaryItem]

@router.post("/page-views/increment", status_code=201)
async def increment_page_view(
    request: PageViewIncrement,
    authorization: Optional[str] = Header(None),
    db: AsyncSession = Depends(get_db),
):
    user_id = None
    if authorization and authorization.startswith("Bearer "):
        try:
            token = authorization[7:]
            payload = verify_access_token(token)
            if payload:
                from uuid import UUID
                result = await db.execute(select(User).where(User.id == payload.get("sub")))
                user = result.scalar_one_or_none()
                if user:
                    user_id = user.id
        except Exception:
            pass

    visit = PageVisit(user_id=user_id, page_name=request.page_name, session_id=request.session_id)
    db.add(visit)
    await db.commit()
    return {"success": True}

@router.get("/page-views/summary", response_model=SummaryResponse)
async def get_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: AsyncSession = Depends(get_db),
):
    query = select(
        PageVisit.page_name,
        func.date(PageVisit.entrance_time).label("date"),
        func.count(PageVisit.id).label("pv"),
        func.count(func.distinct(func.coalesce(PageVisit.user_id, PageVisit.session_id))).label("uv"),
    )
    if start_date:
        query = query.where(func.date(PageVisit.entrance_time) >= start_date)
    if end_date:
        query = query.where(func.date(PageVisit.entrance_time) <= end_date)

    query = query.group_by(PageVisit.page_name, func.date(PageVisit.entrance_time)).order_by(func.date(PageVisit.entrance_time).desc())
    result = await db.execute(query)
    pages = [SummaryItem(page_name=r.page_name, date=str(r.date), pv=r.pv, uv=r.uv) for r in result.all()]

    return SummaryResponse(total_pv=sum(p.pv for p in pages), total_uv=sum(p.uv for p in pages), pages=pages)
