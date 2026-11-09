import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import engine, Base, SessionLocal
from app.api import api_router
from app.services.gamification.engine import _ensure_badges

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("quizforge")

app = FastAPI(
    title="QuizForge API",
    version="1.0.0",
    description="Adaptive AI-Powered Syllabus-to-Quiz Learning Engine with BKT Mastery & Gamification",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include core API router
app.include_router(api_router)

FRONTEND_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "frontend",
)
STATIC_DIR = os.path.join(FRONTEND_DIR, "static")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.on_event("startup")
def on_startup():
    logger.info("Initializing QuizForge database tables...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        _ensure_badges(db)
        from app.models.users import User
        count = db.query(User).count()
        if count == 0:
            logger.info("Empty database detected. Running seed...")
            from seed import seed_database
            seed_database(db=db)
    except Exception as e:
        logger.warning(f"Error during startup seeding: {e}")
    finally:
        db.close()


@app.get("/health", tags=["system"])
def health_check():
    return {
        "status": "healthy",
        "service": "QuizForge API",
        "version": "1.0.0",
        "llm_provider": settings.LLM_PROVIDER,
    }


@app.get("/", tags=["system"])
def root_index():
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {
        "message": "Welcome to QuizForge API — Gamified AI-Based Syllabus-to-Quiz Learning System",
        "docs": "/docs",
        "health": "/health",
    }
