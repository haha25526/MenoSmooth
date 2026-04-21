"""
MenoSmooth Backstage - Admin Dashboard
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta, date
from uuid import UUID as pyUUID

# Add project root and backend to path
project_root = Path(__file__).parent.parent.parent
backend_path = project_root / "backend"
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select, func, desc, Table, Column, String, Float, Date, DateTime, Text, Integer, Boolean, MetaData
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func as sa_func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from backstage.app.config import settings
from backstage.app.deps import verify_admin_password, VALID_ADMIN_TOKEN

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False)
metadata = MetaData()

# Define tables directly (no ORM Base dependency)
users = Table("men_users", metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("phone", String(20), nullable=False),
    Column("nickname", String(64)),
    Column("avatar", String(512)),
    Column("birthday", Date),
    Column("height", Float),
    Column("created_at", DateTime(timezone=True)),
)

page_visits = Table("men_page_visits", metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("user_id", UUID(as_uuid=True)),
    Column("page_name", String(64), nullable=False),
    Column("session_id", String(128)),
    Column("entrance_time", DateTime(timezone=True)),
)

lab_tests = Table("men_lab_tests", metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("user_id", UUID(as_uuid=True), nullable=False),
    Column("test_date", Date, nullable=False),
    Column("e2", Float), Column("fsh", Float), Column("lh", Float),
    Column("progesterone", Float), Column("prolactin", Float),
    Column("calcium", Float), Column("vitamin_d", Float),
    Column("notes", Text), Column("created_at", DateTime(timezone=True)),
)

daily_metrics = Table("men_daily_metrics", metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("user_id", UUID(as_uuid=True), nullable=False),
    Column("recorded_date", Date, nullable=False),
    Column("weight", Float), Column("body_fat", Float),
    Column("temperature", Float), Column("sleep_hours", Float),
    Column("notes", Text), Column("created_at", DateTime(timezone=True)),
)

scale_tests = Table("men_scale_tests", metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("user_id", UUID(as_uuid=True), nullable=False),
    Column("test_date", Date, nullable=False),
    Column("scale_type", String(32), nullable=False),
    Column("total_score", Float), Column("severity_level", String(32)),
    Column("scores", JSONB), Column("created_at", DateTime(timezone=True)),
)

chat_messages = Table("men_chat_messages", metadata,
    Column("id", UUID(as_uuid=True), primary_key=True),
    Column("user_id", UUID(as_uuid=True), nullable=False),
    Column("session_id", String(128), nullable=False),
    Column("role", String(16), nullable=False),
    Column("content", Text),
    Column("created_at", DateTime(timezone=True)),
)

app = FastAPI(title=settings.APP_NAME)

templates_path = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(templates_path))

static_dir = Path(__file__).parent.parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/meno/backstage/static", StaticFiles(directory=str(static_dir)), name="backstage_static")


def get_current_admin(request: Request):
    token = request.cookies.get("backstage_token")
    if token != VALID_ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Not authenticated")


@app.get("/meno/backstage/login", response_class=HTMLResponse)
async def login_page(request: Request):
    token = request.cookies.get("backstage_token")
    if token == VALID_ADMIN_TOKEN:
        return RedirectResponse(url="/meno/backstage/dashboard", status_code=302)
    return templates.TemplateResponse("login.html", {"request": request})


@app.post("/meno/backstage/login")
async def login_submit(request: Request, password: str = Form(...)):
    if verify_admin_password(password):
        response = RedirectResponse(url="/meno/backstage/dashboard", status_code=302)
        response.set_cookie(key="backstage_token", value=VALID_ADMIN_TOKEN, httponly=True, samesite="lax", max_age=86400 * 7)
        return response
    return templates.TemplateResponse("login.html", {"request": request, "error": "密码错误"})


@app.get("/meno/backstage/logout")
async def logout():
    response = RedirectResponse(url="/meno/backstage/login", status_code=302)
    response.delete_cookie("backstage_token")
    return response


@app.get("/meno/backstage/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    try:
        get_current_admin(request)
    except HTTPException:
        return RedirectResponse(url="/meno/backstage/login", status_code=302)

    async with async_session_maker() as db:
        total_users = await db.scalar(select(func.count(users.c.id))) or 0
        total_pv = await db.scalar(select(func.count(page_visits.c.id))) or 0
        total_uv_result = await db.execute(select(func.count(func.distinct(page_visits.c.session_id))))
        total_uv = total_uv_result.scalar() or 0

        today = datetime.now().date()
        today_pv = await db.scalar(select(func.count(page_visits.c.id)).where(func.date(page_visits.c.entrance_time) == today)) or 0
        today_uv_result = await db.execute(select(func.count(func.distinct(page_visits.c.session_id))).where(func.date(page_visits.c.entrance_time) == today))
        today_uv = today_uv_result.scalar() or 0

        # 7-day trend
        seven_days_ago = today - timedelta(days=6)
        trend_rows = await db.execute(
            select(func.date(page_visits.c.entrance_time).label("d"),
                   func.count(page_visits.c.id).label("pv"),
                   func.count(func.distinct(page_visits.c.session_id)).label("uv"))
            .where(func.date(page_visits.c.entrance_time) >= seven_days_ago)
            .group_by(func.date(page_visits.c.entrance_time)).order_by(func.date(page_visits.c.entrance_time))
        )
        trend = [{"date": str(r.d), "pv": r.pv, "uv": r.uv} for r in trend_rows.all()]

        # Page stats
        page_rows = await db.execute(
            select(page_visits.c.page_name,
                   func.count(page_visits.c.id).label("pv"),
                   func.count(func.distinct(page_visits.c.session_id)).label("uv"))
            .group_by(page_visits.c.page_name).order_by(func.count(page_visits.c.id).desc()).limit(10)
        )
        page_stats = [{"page_name": r.page_name or "unknown", "pv": r.pv, "uv": r.uv} for r in page_rows.all()]

        total_labs = await db.scalar(select(func.count(lab_tests.c.id))) or 0
        total_scales = await db.scalar(select(func.count(scale_tests.c.id))) or 0
        total_chat_result = await db.execute(select(func.count(func.distinct(chat_messages.c.session_id))))
        total_chat_sessions = total_chat_result.scalar() or 0

        return templates.TemplateResponse("dashboard.html", {
            "request": request,
            "stats": {
                "total_users": total_users, "total_pv": total_pv, "total_uv": total_uv,
                "today_pv": today_pv, "today_uv": today_uv,
                "trend": trend, "page_stats": page_stats,
                "total_labs": total_labs, "total_scales": total_scales, "total_chat_sessions": total_chat_sessions,
            }
        })


@app.get("/meno/backstage/users", response_class=HTMLResponse)
async def user_list(request: Request, page: int = 1, page_size: int = 20, search: str = None):
    try:
        get_current_admin(request)
    except HTTPException:
        return RedirectResponse(url="/meno/backstage/login", status_code=302)

    async with async_session_maker() as db:
        base_query = select(users)
        if search:
            base_query = base_query.where(
                users.c.nickname.ilike(f"%{search}%") | users.c.phone.ilike(f"%{search}%")
            )
        count_query = select(func.count()).select_from(base_query.subquery())
        total = await db.scalar(count_query) or 0
        total_pages = (total + page_size - 1) // page_size

        offset = (page - 1) * page_size
        user_rows = await db.execute(base_query.offset(offset).limit(page_size).order_by(desc(users.c.created_at)))
        user_list_rows = user_rows.all()

        return templates.TemplateResponse("users.html", {
            "request": request, "users": user_list_rows,
            "page": page, "page_size": page_size, "total": total, "total_pages": total_pages, "search": search,
        })


@app.get("/meno/backstage/users/{user_id}", response_class=HTMLResponse)
async def user_detail(request: Request, user_id: str):
    try:
        get_current_admin(request)
    except HTTPException:
        return RedirectResponse(url="/meno/backstage/login", status_code=302)

    try:
        uid = pyUUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    async with async_session_maker() as db:
        user_row = await db.execute(select(users).where(users.c.id == uid))
        user = user_row.first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        labs = await db.execute(select(lab_tests).where(lab_tests.c.user_id == uid).order_by(desc(lab_tests.c.created_at)).limit(20))
        scales = await db.execute(select(scale_tests).where(scale_tests.c.user_id == uid).order_by(desc(scale_tests.c.created_at)).limit(20))
        metrics = await db.execute(select(daily_metrics).where(daily_metrics.c.user_id == uid).order_by(desc(daily_metrics.c.created_at)).limit(20))
        chat_sess = await db.execute(
            select(chat_messages.c.session_id,
                   func.count(chat_messages.c.id).label("msg_count"),
                   func.max(chat_messages.c.created_at).label("last_msg"))
            .where(chat_messages.c.user_id == uid)
            .group_by(chat_messages.c.session_id).order_by(desc(func.max(chat_messages.c.created_at))).limit(20)
        )

        return templates.TemplateResponse("user_detail.html", {
            "request": request, "user": user,
            "lab_tests": labs.all(), "scale_tests": scales.all(),
            "daily_metrics": metrics.all(), "chat_sessions": chat_sess.all(),
        })
