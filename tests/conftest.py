import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db import get_db, Base
from app.config import settings

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine


@pytest.fixture(scope="function")
def db_session(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture(scope="function")
def client(db_session):
    app.dependency_overrides[get_db] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def test_user_data():
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpassword123"
    }


@pytest.fixture
def auth_headers(client, test_user_data):
    # Register user
    response = client.post("/auth/register", json=test_user_data)
    assert response.status_code == 200
    
    # Login
    login_data = {
        "username": test_user_data["username"],
        "password": test_user_data["password"]
    }
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
