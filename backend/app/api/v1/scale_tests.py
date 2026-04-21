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

# 荷尔蒙健康定量评估量表（30题）
HORMONE_QUESTIONS = {
    "dimensions": [
        {
            "name": "HPA轴功能评估（皮质醇节律）",
            "questions": [
                {"id": "q1", "label": "1. 早晨起床后仍感觉疲倦", "options": [{"score": 0, "label": "从未"}, {"score": 1, "label": "偶尔"}, {"score": 2, "label": "经常"}, {"score": 3, "label": "持续"}]},
                {"id": "q2", "label": "2. 压力大时会出现手抖/心悸", "options": [{"score": 0, "label": "从未"}, {"score": 1, "label": "偶尔"}, {"score": 2, "label": "经常"}, {"score": 3, "label": "持续"}]},
                {"id": "q3", "label": "3. 午后特别渴望咸味食物", "options": [{"score": 0, "label": "从未"}, {"score": 1, "label": "偶尔"}, {"score": 2, "label": "经常"}, {"score": 3, "label": "持续"}]},
                {"id": "q4", "label": "4. 夜深人静时反而思维活跃", "options": [{"score": 0, "label": "从未"}, {"score": 1, "label": "偶尔"}, {"score": 2, "label": "经常"}, {"score": 3, "label": "持续"}]},
                {"id": "q5", "label": "5. 白天频繁需要咖啡提神", "options": [{"score": 0, "label": "从未"}, {"score": 1, "label": "偶尔"}, {"score": 2, "label": "经常"}, {"score": 3, "label": "持续"}]},
            ]
        },
        {
            "name": "HPT轴功能评估（甲状腺代谢）",
            "questions": [
                {"id": "q6", "label": "6. 即使少吃多动，体重仍难下降", "options": [{"score": 0, "label": "完全不符"}, {"score": 1, "label": "不太符合"}, {"score": 2, "label": "比较符合"}, {"score": 3, "label": "完全符合"}]},
                {"id": "q7", "label": "7. 洗发时掉发量明显增多", "options": [{"score": 0, "label": "完全不符"}, {"score": 1, "label": "不太符合"}, {"score": 2, "label": "比较符合"}, {"score": 3, "label": "完全符合"}]},
                {"id": "q8", "label": "8. 说话语速比5年前变慢", "options": [{"score": 0, "label": "完全不符"}, {"score": 1, "label": "不太符合"}, {"score": 2, "label": "比较符合"}, {"score": 3, "label": "完全符合"}]},
                {"id": "q9", "label": "9. 常被家人提醒'手脚太凉'", "options": [{"score": 0, "label": "完全不符"}, {"score": 1, "label": "不太符合"}, {"score": 2, "label": "比较符合"}, {"score": 3, "label": "完全符合"}]},
            ]
        },
        {
            "name": "性健康与亲密关系",
            "questions": [
                {"id": "q10", "label": "10. 过去3个月主动拥抱/亲吻伴侣次数", "options": [{"score": 0, "label": "0次"}, {"score": 1, "label": "1-2次"}, {"score": 2, "label": "3-4次"}, {"score": 3, "label": "≥5次"}]},
                {"id": "q11", "label": "11. 因私密部位不适使用润滑产品的频率", "options": [{"score": 0, "label": "0次"}, {"score": 1, "label": "1-2次"}, {"score": 2, "label": "3-4次"}, {"score": 3, "label": "≥5次"}]},
                {"id": "q12", "label": "12. 回避讨论生理变化对亲密关系影响的对话次数", "options": [{"score": 0, "label": "0次"}, {"score": 1, "label": "1-2次"}, {"score": 2, "label": "3-4次"}, {"score": 3, "label": "≥5次"}]},
            ]
        },
        {
            "name": "社会角色适应",
            "questions": [
                {"id": "q13", "label": "13. 职场中感觉被年轻同事取代", "options": [{"score": 0, "label": "完全没困扰"}, {"score": 1, "label": "轻微困扰"}, {"score": 2, "label": "较大困扰"}, {"score": 3, "label": "严重困扰"}]},
                {"id": "q14", "label": "14. 家人对家务要求引发烦躁", "options": [{"score": 0, "label": "完全没困扰"}, {"score": 1, "label": "轻微困扰"}, {"score": 2, "label": "较大困扰"}, {"score": 3, "label": "严重困扰"}]},
                {"id": "q15", "label": "15. 被开玩笑'记性变差'时的心情", "options": [{"score": 0, "label": "完全没困扰"}, {"score": 1, "label": "轻微困扰"}, {"score": 2, "label": "较大困扰"}, {"score": 3, "label": "严重困扰"}]},
                {"id": "q16", "label": "16. 参加同学聚会的心理负担", "options": [{"score": 0, "label": "完全没困扰"}, {"score": 1, "label": "轻微困扰"}, {"score": 2, "label": "较大困扰"}, {"score": 3, "label": "严重困扰"}]},
            ]
        },
        {
            "name": "炎症与代谢信号",
            "questions": [
                {"id": "q17", "label": "17. 餐后头晕/嗜睡发生频率", "options": [{"score": 0, "label": "从未"}, {"score": 1, "label": "每月1次"}, {"score": 2, "label": "每周1次"}, {"score": 3, "label": "每天"}]},
                {"id": "q18", "label": "18. 关节僵硬/疼痛发作频率", "options": [{"score": 0, "label": "从未"}, {"score": 1, "label": "每月1次"}, {"score": 2, "label": "每周1次"}, {"score": 3, "label": "每天"}]},
                {"id": "q19", "label": "19. 运动起来关节嘎嘎响的频率", "options": [{"score": 0, "label": "从未"}, {"score": 1, "label": "每月1次"}, {"score": 2, "label": "每周1次"}, {"score": 3, "label": "每天"}]},
                {"id": "q20", "label": "20. 夜间因口渴醒来的次数", "options": [{"score": 0, "label": "从未"}, {"score": 1, "label": "每月1次"}, {"score": 2, "label": "每周1次"}, {"score": 3, "label": "每天"}]},
                {"id": "q21", "label": "21. 使用消炎药膏的频率", "options": [{"score": 0, "label": "从未"}, {"score": 1, "label": "每月1次"}, {"score": 2, "label": "每周1次"}, {"score": 3, "label": "每天"}]},
            ]
        },
        {
            "name": "神经内分泌交互",
            "questions": [
                {"id": "q22", "label": "22. 紧张时颈部有压迫感", "options": [{"score": 0, "label": "完全无感"}, {"score": 1, "label": "轻微感受"}, {"score": 2, "label": "明显感受"}, {"score": 3, "label": "强烈感受"}]},
                {"id": "q23", "label": "23. 温暖环境中仍畏寒", "options": [{"score": 0, "label": "完全无感"}, {"score": 1, "label": "轻微感受"}, {"score": 2, "label": "明显感受"}, {"score": 3, "label": "强烈感受"}]},
                {"id": "q24", "label": "24. 听到噪音容易心烦", "options": [{"score": 0, "label": "完全无感"}, {"score": 1, "label": "轻微感受"}, {"score": 2, "label": "明显感受"}, {"score": 3, "label": "强烈感受"}]},
                {"id": "q25", "label": "25. 对咖啡因的依赖程度", "options": [{"score": 0, "label": "完全无感"}, {"score": 1, "label": "轻微感受"}, {"score": 2, "label": "明显感受"}, {"score": 3, "label": "强烈感受"}]},
                {"id": "q26", "label": "26. 睡眠质量对次日效率的影响程度", "options": [{"score": 0, "label": "完全无感"}, {"score": 1, "label": "轻微感受"}, {"score": 2, "label": "明显感受"}, {"score": 3, "label": "强烈感受"}]},
            ]
        },
    ],
    # 开放题（不计分）
    "open_questions": [
        {"id": "q27", "label": "27. 您最近3个月最常做的放松活动是？", "options": ["阅读/听音乐", "瑜伽/散步", "刷短视频", "社交聚会", "其他"]},
        {"id": "q28", "label": "28. 选择服装时最在意的因素是？", "options": ["舒适度", "显瘦效果", "方便活动", "其他"]},
        {"id": "q29", "label": "29. 您潮热盗汗的频率是？", "options": ["从不", "偶尔，每周一次", "偶尔，每天一次", "很频繁"]},
        {"id": "q30", "label": "30. 您对自身健康调整/管理的长期目标是？", "options": ["维持现状", "改善体能", "延缓衰老", "减少症状", "其他"]},
    ]
}

def calculate_hormone_level(total_score):
    if total_score >= 52:
        return "严重失衡", "建议尽快就医，进行全面荷尔蒙检测和专业治疗"
    elif total_score >= 39:
        return "中度失衡", "建议进行生活方式调整，并在3个月后复测"
    elif total_score >= 26:
        return "轻度失衡", "建议关注日常作息和饮食，适当增加运动"
    elif total_score >= 13:
        return "基本正常", "身体状况良好，继续保持健康的生活方式"
    else:
        return "状态优秀", "荷尔蒙水平健康，请继续保持"

@router.get("/kupperman/questions")
async def get_kupperman_questions():
    return {"questions": KUPPERMAN_QUESTIONS}

@router.get("/hormone/questions")
async def get_hormone_questions():
    return HORMONE_QUESTIONS

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
