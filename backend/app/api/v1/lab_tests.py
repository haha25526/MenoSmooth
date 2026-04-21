"""
Lab Tests CRUD + Vision Parse
"""
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import base64

from app.database import get_db
from app.api.deps import CurrentUser
from app.schemas import LabTestCreate, LabTestResponse, VisionParseResponse
from app.models.lab_test import LabTest
from app.services.vision import vision_service

router = APIRouter()

@router.get("/", response_model=list[LabTestResponse])
async def list_tests(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(LabTest).where(LabTest.user_id == current_user.id).order_by(LabTest.test_date.desc())
    )
    return [LabTestResponse.model_validate(t) for t in result.scalars().all()]

@router.post("/", response_model=LabTestResponse)
async def create_test(
    data: LabTestCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    test = LabTest(user_id=current_user.id, **data.model_dump())
    db.add(test)
    await db.commit()
    await db.refresh(test)
    return LabTestResponse.model_validate(test)

@router.delete("/{test_id}")
async def delete_test(
    test_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    result = await db.execute(
        select(LabTest).where(LabTest.id == UUID(test_id), LabTest.user_id == current_user.id)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(test)
    await db.commit()
    return {"success": True}

@router.post("/vision-parse", response_model=VisionParseResponse)
async def parse_lab_test(
    current_user: CurrentUser,
    image: UploadFile = File(...),
):
    if not image.content_type or not image.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="请上传图片")
    data = await image.read()
    if len(data) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片过大")
    result = await vision_service.parse_lab_test(base64.b64encode(data).decode())
    return VisionParseResponse(**result)
