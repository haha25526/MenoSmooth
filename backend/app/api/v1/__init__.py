"""
API v1 Router
"""
from fastapi import APIRouter
from .auth import router as auth_router
from .users import router as users_router
from .lab_tests import router as lab_tests_router
from .daily_metrics import router as daily_metrics_router
from .scale_tests import router as scale_tests_router
from .chat import router as chat_router
from .analytics import router as analytics_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["Auth"])
router.include_router(users_router, prefix="/users", tags=["Users"])
router.include_router(lab_tests_router, prefix="/lab-tests", tags=["Lab Tests"])
router.include_router(daily_metrics_router, prefix="/daily-metrics", tags=["Daily Metrics"])
router.include_router(scale_tests_router, prefix="/scale-tests", tags=["Scale Tests"])
router.include_router(chat_router, prefix="/chat", tags=["Chat"])
router.include_router(analytics_router, prefix="/analytics", tags=["Analytics"])
