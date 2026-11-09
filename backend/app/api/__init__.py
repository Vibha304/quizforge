from fastapi import APIRouter
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.topics import router as topics_router
from app.api.questions import router as questions_router
from app.api.quiz import router as quiz_router
from app.api.analytics import router as analytics_router
from app.api.leaderboard import router as leaderboard_router
from app.api.export import router as export_router

api_router = APIRouter()

api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(documents_router, prefix="/documents", tags=["documents"])
api_router.include_router(topics_router, prefix="/topics", tags=["topics"])
api_router.include_router(questions_router, prefix="/questions", tags=["questions"])
api_router.include_router(quiz_router, prefix="/quiz", tags=["quiz"])
api_router.include_router(analytics_router, prefix="/analytics", tags=["analytics"])
api_router.include_router(leaderboard_router, prefix="/leaderboard", tags=["leaderboard"])
api_router.include_router(export_router, prefix="/export", tags=["export"])
