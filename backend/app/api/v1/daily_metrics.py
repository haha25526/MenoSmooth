"""
Daily Metrics CRUD + Vision Parse
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import base64

from app.database import get_db
from app.api.deps import CurrentUser
from app.schemas import DailyMetricCreate, DailyMetricResponse, VisionParseResponse
from app.models.daily_metric import DailyMetric
from app.services.vision import vision_service

router = APIRouter()

@router.get("/", response_model=list[DailyMetricResponse])
async def list_metrics(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(DailyMetric).where(DailyMetric.user_id == current_user.id).order_by(DailyMetric.recorded_date.desc())
    )
    return [DailyMetricResponse.model_validate(m) for m in result.scalars().all()]

@router.post("/", response_model=DailyMetricResponse)
async def create_metric(
    data: DailyMetricCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    metric = DailyMetric(user_id=current_user.id, **data.model_dump())
    db.add(metric)
    await db.commit()
    await db.refresh(metric)
    return DailyMetricResponse.model_validate(metric)

@router.delete("/{metric_id}")
async def delete_metric(
    metric_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    result = await db.execute(
        select(DailyMetric).where(DailyMetric.id == UUID(metric_id), DailyMetric.user_id == current_user.id)
    )
    metric = result.scalar_one_or_none()
    if not metric:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(metric)
    await db.commit()
    return {"success": True}

@router.post("/vision-parse", response_model=VisionParseResponse)
async def parse_screenshot(
    current_user: CurrentUser,
    image: UploadFile = File(...),
):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片")
    data = await image.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片过大")
    result = await vision_service.parse_health_screenshot(base64.b64encode(data).decode())
    return VisionParseResponse(**result)
