"""
Scale Tests CRUD
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.api.deps import CurrentUser
from app.schemas import ScaleTestCreate, ScaleTestResponse
from app.models.scale_test import ScaleTest

router = APIRouter()

# Kupperman 量表题目和评分
KUPPERMAN_QUESTIONS = [
    {"id": "hot_flashes", "label": "潮热出汗", "options": [{"score": 0, "label": "无"}, {"score": 1, "label": "<3次/天"}, {"score": 2, "label": "3-5次/天"}, {"score": 3, "label": ">5次/天"}]},
    {"id": "mood", "label": "感觉/情绪", "options": [{"score": 0, "label": "正常"}, {"score": 1, "label": "偶尔"}, {"score": 2, "label": "经常"}, {"score": 3, "label": "持续"}]},
    {"id": "insomnia", "label": "失眠", "options": [{"score": 0, "label": "无"}, {"score": 1, "label": "偶尔"}, {"score": 2, "label": "经常"}, {"score": 3, "label": "持续"}]},
    {"id": "joint_muscle", "label": "关节/肌肉", "options": [{"score": 0, "label": "无"}, {"score": 1, "label": "偶尔"}, {"score": 2, "label": "不影响活动"}, {"score": 3, "label": "影响活动"}]},
    {"id": "headache", "label": "头痛", "options": [{"score": 0, "label": "无"}, {"score": 1, "label": "偶尔"}, {"score": 2, "label": "经常"}, {"score": 3, "label": "持续"}]},
    {"id": "palpitations", "label": "心悸", "options": [{"score": 0, "label": "无"}, {"score": 1, "label": "偶尔"}, {"score": 2, "label": "经常"}, {"score": 3, "label": "持续"}]},
    {"id": "tingling", "label": "皮肤蚁走感", "options": [{"score": 0, "label": "无"}, {"score": 1, "label": "偶尔"}, {"score": 2, "label": "经常"}, {"score": 3, "label": "持续"}]},
    {"id": "libido", "label": "性欲", "options": [{"score": 0, "label": "正常"}, {"score": 1, "label": "轻度下降"}, {"score": 2, "label": "明显下降"}, {"score": 3, "label": "丧失"}]},
    {"id": "vaginal", "label": "阴道干燥", "options": [{"score": 0, "label": "无"}, {"score": 1, "label": "偶尔"}, {"score": 2, "label": "性交困难"}, {"score": 3, "label": "严重"}]},
    {"id": "urinary", "label": "泌尿症状", "options": [{"score": 0, "label": "无"}, {"score": 1, "label": "偶尔"}, {"score": 2, "label": "经常"}, {"score": 3, "label": "持续"}]},
]

@router.get("/kupperman/questions")
async def get_kupperman_questions():
    """返回 Kupperman 量表题目"""
    return {"questions": KUPPERMAN_QUESTIONS}

@router.get("/", response_model=list[ScaleTestResponse])
async def list_tests(current_user: CurrentUser, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(ScaleTest).where(ScaleTest.user_id == current_user.id).order_by(ScaleTest.test_date.desc())
    )
    return [ScaleTestResponse.model_validate(t) for t in result.scalars().all()]

@router.post("/", response_model=ScaleTestResponse)
async def create_test(
    data: ScaleTestCreate,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    test = ScaleTest(user_id=current_user.id, **data.model_dump())
    db.add(test)
    await db.commit()
    await db.refresh(test)
    return ScaleTestResponse.model_validate(test)

@router.delete("/{test_id}")
async def delete_test(
    test_id: str,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
):
    from uuid import UUID
    result = await db.execute(
        select(ScaleTest).where(ScaleTest.id == UUID(test_id), ScaleTest.user_id == current_user.id)
    )
    test = result.scalar_one_or_none()
    if not test:
        raise HTTPException(status_code=404, detail="Not found")
    await db.delete(test)
    await db.commit()
    return {"success": True}
