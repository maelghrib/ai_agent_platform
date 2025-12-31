import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from app.main import app
from app.database import get_session

TEST_DATABASE_URL = "sqlite:///./ai_agent_platform_test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)


@pytest.fixture(scope="session", autouse=True)
def create_test_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)


@pytest.fixture()
def session_override():
    with Session(engine) as session:
        yield session


@pytest.fixture()
def client(session_override):
    def get_test_session():
        yield session_override

    app.dependency_overrides[get_session] = get_test_session
    yield TestClient(app)
    app.dependency_overrides.clear()
