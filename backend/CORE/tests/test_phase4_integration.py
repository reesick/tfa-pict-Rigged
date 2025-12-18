"""
Phase 4: Cross-Phase Integration Tests
Tests end-to-end flows and connections between all features.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date
from app.main import app
from app.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test database
TEST_DATABASE_URL = "sqlite:///./test_integration_full.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="module")
def client():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = get_test_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ==================== FULL USER JOURNEY ====================

class TestFullUserJourney:
    """Test complete user journey through all features."""
    
    def test_complete_flow(self, client):
        """Full flow: Register → Login → Create Budget → Create Transactions → Stats."""
        
        # 1. Register
        reg_resp = client.post("/api/auth/register", json={
            "email": "journey@test.com",
            "password": "JourneyPass123!",
            "full_name": "Journey Tester"
        })
        assert reg_resp.status_code == 201
        
        # 2. Login
        login_resp = client.post("/api/auth/login", json={
            "email": "journey@test.com",
            "password": "JourneyPass123!"
        })
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 3. Create Budget
        budget_resp = client.post("/api/budgets/", json={
            "category": "Shopping",
            "limit_amount": 500.00,
            "period": "monthly",
            "start_date": str(date.today()),
            "alert_threshold": 80.0
        }, headers=headers)
        assert budget_resp.status_code == 201
        
        # 4. Create Transactions
        for i in range(3):
            txn_resp = client.post("/api/transactions/", json={
                "amount": 50.00 + i * 10,
                "transaction_date": str(date.today()),
                "merchant_raw": f"Store {i}",
                "category": "Shopping"
            }, headers=headers)
            assert txn_resp.status_code == 201
        
        # 5. Check Stats
        stats_resp = client.get("/api/transactions/stats", headers=headers)
        assert stats_resp.status_code == 200
        assert stats_resp.json()["total_transactions"] >= 3
        
        # 6. List Transactions
        list_resp = client.get("/api/transactions/", headers=headers)
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] >= 3
        
        # 7. Get Profile
        me_resp = client.get("/api/auth/me", headers=headers)
        assert me_resp.status_code == 200
        assert me_resp.json()["email"] == "journey@test.com"


# ==================== AUTH → ALL ENDPOINTS ====================

class TestAuthProtection:
    """Verify all endpoints require authentication."""
    
    def test_transactions_require_auth(self, client):
        """Transaction endpoints should require auth."""
        # No auth header
        endpoints = [
            ("GET", "/api/transactions/"),
            ("POST", "/api/transactions/"),
            ("GET", "/api/transactions/stats"),
        ]
        for method, url in endpoints:
            if method == "GET":
                resp = client.get(url)
            else:
                resp = client.post(url, json={})
            assert resp.status_code in [401, 403, 422], f"{method} {url} should require auth"
    
    def test_budgets_require_auth(self, client):
        """Budget endpoints should require auth."""
        resp = client.get("/api/budgets/")
        assert resp.status_code in [401, 403]
        
        resp = client.post("/api/budgets/", json={})
        assert resp.status_code in [401, 403, 422]
    
    def test_merchants_require_auth(self, client):
        """Merchant endpoints should require auth."""
        resp = client.get("/api/merchants/search?q=test")
        assert resp.status_code in [401, 403]


# ==================== USER ISOLATION ====================

class TestCrossUserIsolation:
    """Test that users cannot access each other's data."""
    
    def test_user_a_cannot_access_user_b_data(self, client):
        """Users should have completely isolated data."""
        
        # Create User A
        client.post("/api/auth/register", json={
            "email": "userA@iso.com",
            "password": "password123",
            "full_name": "User A"
        })
        login_a = client.post("/api/auth/login", json={
            "email": "userA@iso.com",
            "password": "password123"
        })
        headers_a = {"Authorization": f"Bearer {login_a.json()['access_token']}"}
        
        # User A creates transaction
        txn_a = client.post("/api/transactions/", json={
            "amount": 999.99,
            "transaction_date": str(date.today()),
            "merchant_raw": "User A Secret Store"
        }, headers=headers_a)
        txn_a_id = txn_a.json()["id"]
        
        # Create User B
        client.post("/api/auth/register", json={
            "email": "userB@iso.com",
            "password": "password123",
            "full_name": "User B"
        })
        login_b = client.post("/api/auth/login", json={
            "email": "userB@iso.com",
            "password": "password123"
        })
        headers_b = {"Authorization": f"Bearer {login_b.json()['access_token']}"}
        
        # User B tries to access User A's transaction
        resp = client.get(f"/api/transactions/{txn_a_id}", headers=headers_b)
        assert resp.status_code == 404, "User B should not see User A's transaction"
        
        # User B's list should not include User A's data
        list_b = client.get("/api/transactions/", headers=headers_b)
        ids_b = [t["id"] for t in list_b.json()["data"]]
        assert txn_a_id not in ids_b


# ==================== MODEL INTEGRATION ====================

class TestModelIntegration:
    """Test that all models work together."""
    
    def test_all_models_importable(self):
        """All models should be importable."""
        from app.models import (
            User, Transaction, Budget, MerchantMaster,
            PortfolioHolding, MerkleBatch, UserCorrection,
            Recurrence, Embedding
        )
        assert User is not None
        assert Transaction is not None
        assert Recurrence is not None
        assert Embedding is not None
    
    def test_service_layer_works(self):
        """Service layer should be functional."""
        from app.services.transaction import TransactionService
        from app.services.budget import BudgetService
        from app.services.merchant import MerchantService
        
        assert hasattr(TransactionService, 'create')
        assert hasattr(TransactionService, 'find_duplicate')
        assert hasattr(BudgetService, 'create')
        assert hasattr(MerchantService, 'search')


# ==================== EDGE CASE COMBINATIONS ====================

class TestEdgeCaseCombinations:
    """Test edge cases that span multiple features."""
    
    def test_transaction_with_all_optional_fields(self, client):
        """Transaction with all optional fields."""
        # Login
        client.post("/api/auth/register", json={
            "email": "combo@test.com",
            "password": "password123",
            "full_name": "Combo Tester"
        })
        login = client.post("/api/auth/login", json={
            "email": "combo@test.com",
            "password": "password123"
        })
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        
        # Create with all fields
        resp = client.post("/api/transactions/", json={
            "amount": 123.45,
            "transaction_date": str(date.today()),
            "merchant_raw": "Full Fields Store",
            "category": "Testing",
            "description": "This is a test transaction with description",
            "source": "manual"
        }, headers=headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["merchant_raw"] == "Full Fields Store"
        assert data["category"] == "Testing"
    
    def test_search_and_filter_combined(self, client):
        """Search with category filter should work together."""
        # Login
        login = client.post("/api/auth/login", json={
            "email": "combo@test.com",
            "password": "password123"
        })
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        
        # Search with filter
        resp = client.get(
            "/api/transactions/?search=Full&category=Testing",
            headers=headers
        )
        assert resp.status_code == 200
