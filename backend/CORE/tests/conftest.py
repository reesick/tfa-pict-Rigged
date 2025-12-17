"""
Test Configuration - Proper fixtures for comprehensive testing.
Uses the ACTUAL models (not simplified) to ensure real edge cases are tested.
"""
import os
import sys

# Set test environment BEFORE any app imports
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-minimum-32-characters-long"
os.environ["DEBUG"] = "True"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Import app modules
from app.database import Base, get_db, reset_engine

# Reset the engine to use our test settings
reset_engine()

# Create test engine
TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ==================== FIXTURES ====================

@pytest.fixture(scope="function")
def db():
    """
    Create a fresh database for each test function.
    This ensures test isolation - each test starts with clean state.
    """
    # Import models to ensure they're registered with Base
    from app.models.user import User
    from app.models.transaction import Transaction
    from app.models.merchant import MerchantMaster
    from app.models.budget import Budget
    from app.models.portfolio import PortfolioHolding
    from app.models.blockchain import MerkleBatch, UserCorrection
    
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
    Create a test client with database injection.
    Uses the REAL app with the test database.
    """
    from app.main import app
    
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
def registered_user(client):
    """
    Create a registered user and return auth data.
    Returns: dict with access_token, refresh_token, email, password
    """
    user_data = {
        "email": "test@example.com",
        "password": "TestPassword123!",
        "full_name": "Test User",
        "phone": "+1234567890"
    }
    
    response = client.post("/api/auth/register", json=user_data)
    assert response.status_code == 201, f"Registration failed: {response.json()}"
    
    tokens = response.json()
    return {
        "email": user_data["email"],
        "password": user_data["password"],
        "access_token": tokens["access_token"],
        "refresh_token": tokens["refresh_token"],
    }


@pytest.fixture
def auth_headers(registered_user):
    """Return authorization headers for authenticated requests."""
    return {"Authorization": f"Bearer {registered_user['access_token']}"}


@pytest.fixture
def sample_transactions(client, auth_headers):
    """Create sample transactions for testing."""
    transactions = []
    for i in range(5):
        response = client.post(
            "/api/transactions/",
            headers=auth_headers,
            json={
                "amount": (i + 1) * 25.0,
                "transaction_date": f"2024-01-{(i + 1):02d}",
                "category": ["Food", "Transport", "Shopping", "Entertainment", "Bills"][i],
                "merchant_raw": f"Merchant {i + 1}",
                "description": f"Test transaction {i + 1}"
            }
        )
        assert response.status_code == 201
        transactions.append(response.json())
    
    return transactions
