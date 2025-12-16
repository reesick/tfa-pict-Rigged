"""Test fixtures and configuration for pytest."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.main import app
from app.database import Base, get_db
from app.models.user import User

# Use in-memory SQLite for testing (fast, isolated)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """
    Create a fresh database for each test.
    
    Yields database session, automatically rolls back after test.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """
    Create test client with test database.
    
    Overrides get_db dependency to use test database.
    """
    def override_get_db():
        try:
            yield db
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def test_user(client, db):
    """
    Create a test user and return tokens.
    
    Returns dict with user data and authentication tokens.
    """
    response = client.post("/api/auth/register", json={
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User",
        "phone": "+1234567890"
    })
    
    assert response.status_code == 201
    data = response.json()
    
    # Get user from database
    user = db.query(User).filter(User.email == "test@example.com").first()
    
    return {
        "user": user,
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "email": "test@example.com",
        "password": "TestPass123!"
    }


@pytest.fixture
def auth_headers(test_user):
    """
    Return authorization headers for authenticated requests.
    
    Usage:
        response = client.get("/api/auth/me", headers=auth_headers)
    """
    return {
        "Authorization": f"Bearer {test_user['access_token']}"
    }
