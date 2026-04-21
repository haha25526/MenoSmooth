"""
MenoSmooth Backstage - Admin Dashboard
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, date

# Add project root and backend to path
project_root = Path(__file__).parent.parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(project_root))

from uuid import UUID
from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from backstage.app.config import settings
from backstage.app.deps import verify_admin_password, VALID_ADMIN_TOKEN

# Create a separate engine for the menopause database
engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)

# Import MenoSmooth models (after sys.path modification)
from app.models.user import User
from app.models.page_visit import PageVisit
from app.models.lab_test import LabTest
from app.models.daily_metric import DailyMetric
from app.models.scale_test import ScaleTest
from app.models.chat_message import ChatMessage

app = FastAPI(title=settings.APP_NAME)

templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

static_dir = Path(__file__).parent.parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/backstage/static", StaticFiles(directory=str(static_dir)), name="backstage_static")


def get_current_admin(request: Request):
    token = request.cookies.get("backstage_token")
    if token != VALID_ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Not authenticated")


@app.get("/backstage/login", response_class=HTMLResponse)
async def login_page(request: Request):
    token = request.cookies.get("backstage_token")
    if token == VALID_ADMIN_TOKEN:
        return RedirectResponse(url="/backstage/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/backstage/login")
async def login_submit(request: Request, password: str = Form(...)):
    if verify_admin_password(password):
        response = RedirectResponse(url="/backstage/dashboard", status_code=302)
        response.set_cookie(key="backstage_token", value=VALID_ADMIN_TOKEN, httponly=True, samesite="lax", max_age=86400 * 7)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "密码错误"})


@app.get("/backstage/logout")
async def logout():
    response = RedirectResponse(url="/backstage/login", status_code=302)
    response.delete_cookie("backstage_token")
    return response


@app.get("/backstage/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        get_current_admin(request)
    except HTTPException:
        return RedirectResponse(url="/backstage/login", status_code=302)

    async with async_session_maker() as db:
        total_users = await db.scalar(select(func.count(User.id))) or 0

        # PV/UV from page_visits
        total_pv = await db.scalar(select(func.count(PageVisit.id))) or 0
        unique_sessions = await db.execute(select(func.count(func.distinct(PageVisit.session_id))))
        total_uv = unique_sessions.scalar() or 0

        today = datetime.now().date()
        today_pv = await db.scalar(select(func.count(PageVisit.id)).where(func.date(PageVisit.entrance_time) == today)) or 0
        today_sessions = await db.execute(select(func.count(func.distinct(PageVisit.session_id))).where(func.date(PageVisit.entrance_time) == today))
        today_uv = today_sessions.scalar() or 0

        # 7-day trend
        seven_days_ago = today - timedelta(days=6)
        trend_rows = await db.execute(
            select(
                func.date(PageVisit.entrance_time).label("d"),
                func.count(PageVisit.id).label("pv"),
                func.count(func.distinct(PageVisit.session_id)).label("uv"),
            ).where(func.date(PageVisit.entrance_time) >= seven_days_ago)
             .group_by(func.date(PageVisit.entrance_time)).order_by(func.date(PageVisit.entrance_time))
        )
        trend = [{"date": str(r.d), "pv": r.pv, "uv": r.uv} for r in trend_rows.all()]

        # Page stats
        page_rows = await db.execute(
            select(
                PageVisit.page_name,
                func.count(PageVisit.id).label("pv"),
                func.count(func.distinct(PageVisit.session_id)).label("uv"),
            ).group_by(PageVisit.page_name).order_by(func.count(PageVisit.id).desc()).limit(10)
        )
        page_stats = [{"page_name": r.page_name, "pv": r.pv, "uv": r.uv} for r in page_rows.all()]

        # Lab test count
        total_labs = await db.scalar(select(func.count(LabTest.id))) or 0
        total_scales = await db.scalar(select(func.count(ScaleTest.id))) or 0
        total_chats = await db.execute(select(func.count(func.distinct(ChatMessage.session_id))))
        total_chat_sessions = total_chats.scalar() or 0

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "stats": {
                "total_users": total_users,
                "total_pv": total_pv, "total_uv": total_uv,
                "today_pv": today_pv, "today_uv": today_uv,
                "trend": trend, "page_stats": page_stats,
                "total_labs": total_labs, "total_scales": total_scales, "total_chat_sessions": total_chat_sessions,
            }
        })


@app.get("/backstage/users", response_class=HTMLResponse)
async def user_list(request: Request, page: int = 1, page_size: int = 20, search: str = None):
    try:
        get_current_admin(request)
    except HTTPException:
        return RedirectResponse(url="/backstage/login", status_code=302)

    async with async_session_maker() as db:
        base_query = select(User)
        if search:
            base_query = base_query.where(
                (User.nickname.ilike(f"%{search}%")) | (User.phone.ilike(f"%{search}%"))
            )

        count_query = select(func.count()).select_from(base_query.subquery())
        total = await db.scalar(count_query) or 0
        total_pages = (total + page_size - 1) // page_size

        offset = (page - 1) * page_size
        users_result = await db.execute(base_query.offset(offset).limit(page_size).order_by(desc(User.created_at)))
        users = users_result.scalars().all()

        return templates.TemplateResponse("users.html", {
            "request": request, "users": users,
            "page": page, "page_size": page_size, "total": total, "total_pages": total_pages, "search": search,
        })


@app.get("/backstage/users/{user_id}", response_class=HTMLResponse)
async def user_detail(request: Request, user_id: str):
    try:
        get_current_admin(request)
    except HTTPException:
        return RedirectResponse(url="/backstage/login", status_code=302)

    try:
        uid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    async with async_session_maker() as db:
        user_result = await db.execute(select(User).where(User.id == uid))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        labs = await db.execute(select(LabTest).where(LabTest.user_id == uid).order_by(desc(LabTest.created_at)).limit(20))
        scales = await db.execute(select(ScaleTest).where(ScaleTest.user_id == uid).order_by(desc(ScaleTest.created_at)).limit(20))
        metrics = await db.execute(select(DailyMetric).where(DailyMetric.user_id == uid).order_by(desc(DailyMetric.created_at)).limit(20))

        chat_sessions = await db.execute(
            select(ChatMessage.session_id, func.count(ChatMessage.id).label("msg_count"), func.max(ChatMessage.created_at).label("last_msg"))
            .where(ChatMessage.user_id == uid).group_by(ChatMessage.session_id).order_by(desc(func.max(ChatMessage.created_at))).limit(20)
        )

        return templates.TemplateResponse("user_detail.html", {
            "request": request, "user": user,
            "lab_tests": labs.scalars().all(),
            "scale_tests": scales.scalars().all(),
            "daily_metrics": metrics.scalars().all(),
            "chat_sessions": chat_sessions.all(),
        })
