import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app
from app.models.users import User
from app.models.documents import Document
from app.models.topics import Topic
from app.models.questions import Question
from app.models.gamification import UserStats
from app.core.security import get_password_hash, create_access_token
from app.services.gamification.engine import _ensure_badges

# In-memory test SQLite DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    _ensure_badges(db)
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    user = User(
        email="teststudent@quizforge.app",
        name="Test Student",
        password_hash=get_password_hash("testpass123"),
        role="student",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    stats = UserStats(
        user_id=user.id,
        xp=100,
        level=1,
        streak=2,
    )
    db_session.add(stats)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(test_user):
    token = create_access_token({"sub": str(test_user.id), "email": test_user.email, "role": test_user.role})
    return {"Authorization": f"Bearer {token}"}
