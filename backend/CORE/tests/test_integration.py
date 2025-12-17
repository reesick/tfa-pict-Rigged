"""
Comprehensive Integration Test - Phase 1 to Phase 4
Tests the complete flow using ACTUAL models with all edge cases.
Run with: pytest tests/test_integration.py -v
"""
import os

# Set test environment BEFORE imports
os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-minimum-32-characters-long"

import pytest
import uuid


# ==================== PHASE 1: CORE SETUP TESTS ====================

class TestPhase1CoreSetup:
    """Tests for basic project setup and configuration."""
    
    def test_config_loads(self):
        """Config system works."""
        from app.config import get_settings
        settings = get_settings()
        assert settings.app_name == "SmartFinance AI"
        assert len(settings.jwt_secret) >= 32
    
    def test_database_base_exists(self):
        """Database Base class exists."""
        from app.database import Base
        assert Base is not None
    
    def test_app_starts(self, client):
        """FastAPI app is running."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_openapi_docs(self, client):
        """OpenAPI documentation is accessible."""
        response = client.get("/docs")
        assert response.status_code == 200


# ==================== PHASE 2: MODEL TESTS ====================

class TestPhase2Models:
    """Tests for database models."""
    
    def test_all_models_import(self):
        """All models can be imported."""
        from app.models.user import User
        from app.models.transaction import Transaction
        from app.models.merchant import MerchantMaster
        from app.models.budget import Budget
        from app.models.portfolio import PortfolioHolding
        from app.models.blockchain import MerkleBatch, UserCorrection
        
        assert User.__tablename__ == "users"
        assert Transaction.__tablename__ == "transactions"
        assert MerchantMaster.__tablename__ == "merchant_master"
        assert Budget.__tablename__ == "budgets"
        assert PortfolioHolding.__tablename__ == "portfolio_holdings"
        assert MerkleBatch.__tablename__ == "merkle_batches"
        assert UserCorrection.__tablename__ == "user_corrections"
    
    def test_user_model_creation(self, db):
        """User can be created in database."""
        from app.models.user import User
        from app.utils.security import hash_password
        
        user = User(
            email="model_test@example.com",
            hashed_password=hash_password("password123"),
            full_name="Model Test User"
        )
        db.add(user)
        db.commit()
        
        found = db.query(User).filter(User.email == "model_test@example.com").first()
        assert found is not None
        assert found.full_name == "Model Test User"
        assert found.is_active is True


# ==================== PHASE 3: AUTHENTICATION TESTS ====================

class TestPhase3Authentication:
    """Tests for authentication system."""
    
    def test_password_hashing(self):
        """Password hashing works correctly."""
        from app.utils.security import hash_password, verify_password
        
        password = "SecurePass123!"
        hashed = hash_password(password)
        
        # Hash is different from password
        assert hashed != password
        # Hash is bcrypt format
        assert hashed.startswith("$2b$")
        # Verification works
        assert verify_password(password, hashed) is True
        assert verify_password("wrong_password", hashed) is False
    
    def test_password_hashing_edge_cases(self):
        """Password hashing handles edge cases."""
        from app.utils.security import hash_password, verify_password
        
        # Empty string (should work but be verified)
        h1 = hash_password("")
        assert verify_password("", h1) is True
        
        # Very long password
        long_pass = "A" * 100
        h2 = hash_password(long_pass)
        assert verify_password(long_pass, h2) is True
        
        # Unicode password
        unicode_pass = "пароль123!"
        h3 = hash_password(unicode_pass)
        assert verify_password(unicode_pass, h3) is True
    
    def test_jwt_creation_and_validation(self):
        """JWT tokens can be created and validated."""
        from app.utils.security import create_access_token, decode_token
        
        payload = {"sub": "user-123"}
        token = create_access_token(payload)
        
        assert token is not None
        assert len(token.split(".")) == 3  # JWT format
        
        decoded = decode_token(token)
        assert decoded["sub"] == "user-123"
        assert decoded["type"] == "access"
    
    def test_expired_token_handling(self):
        """Expired tokens are properly rejected."""
        from app.utils.security import create_access_token, decode_token
        from datetime import timedelta
        
        # Create token that already expired
        token = create_access_token({"sub": "user"}, expires_delta=timedelta(seconds=-10))
        decoded = decode_token(token)
        assert decoded is None  # Expired tokens return None
    
    def test_user_registration(self, client):
        """User can register."""
        response = client.post("/api/auth/register", json={
            "email": "newuser@example.com",
            "password": "NewPass123!",
            "full_name": "New User"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
    
    def test_duplicate_registration_fails(self, client):
        """Duplicate email registration fails with proper error."""
        # First registration
        client.post("/api/auth/register", json={
            "email": "duplicate@example.com",
            "password": "Pass123!",
            "full_name": "First User"
        })
        
        # Second registration with same email
        response = client.post("/api/auth/register", json={
            "email": "duplicate@example.com",
            "password": "DifferentPass123!",
            "full_name": "Second User"
        })
        
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()
    
    def test_user_login(self, client):
        """User can login with correct credentials."""
        # Register first
        client.post("/api/auth/register", json={
            "email": "login@example.com",
            "password": "LoginPass123!",
            "full_name": "Login User"
        })
        
        # Login
        response = client.post("/api/auth/login", json={
            "email": "login@example.com",
            "password": "LoginPass123!"
        })
        
        assert response.status_code == 200
        assert "access_token" in response.json()
    
    def test_wrong_password_fails(self, client):
        """Wrong password login fails."""
        # Register
        client.post("/api/auth/register", json={
            "email": "wrongpass@example.com",
            "password": "CorrectPass123!",
            "full_name": "User"
        })
        
        # Login with wrong password
        response = client.post("/api/auth/login", json={
            "email": "wrongpass@example.com",
            "password": "WrongPassword!"
        })
        
        assert response.status_code == 401
    
    def test_nonexistent_user_login_fails(self, client):
        """Login for non-existent user fails."""
        response = client.post("/api/auth/login", json={
            "email": "doesnotexist@example.com",
            "password": "SomePass123!"
        })
        
        assert response.status_code == 401
    
    def test_get_current_user(self, client, registered_user, auth_headers):
        """Authenticated user can get their profile."""
        response = client.get("/api/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == registered_user["email"]
    
    def test_unauthenticated_request_fails(self, client):
        """Request without token fails."""
        response = client.get("/api/auth/me")
        assert response.status_code == 403


# ==================== PHASE 4: TRANSACTION TESTS ====================

class TestPhase4Transactions:
    """Tests for transaction API with edge case coverage."""
    
    def test_create_transaction(self, client, auth_headers):
        """Transaction can be created."""
        response = client.post(
            "/api/transactions/",
            headers=auth_headers,
            json={
                "amount": 50.00,
                "transaction_date": "2024-01-15",
                "category": "Food",
                "merchant_raw": "Coffee Shop"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert float(data["amount"]) == 50.00
        assert data["category"] == "Food"
        assert "id" in data
    
    def test_create_transaction_minimal(self, client, auth_headers):
        """Transaction can be created with minimal fields."""
        response = client.post(
            "/api/transactions/",
            headers=auth_headers,
            json={
                "amount": 25.00,
                "transaction_date": "2024-01-15"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["category"] is None
        assert data["merchant_raw"] is None
    
    def test_create_transaction_validates_amount(self, client, auth_headers):
        """Transaction creation validates amount is positive."""
        response = client.post(
            "/api/transactions/",
            headers=auth_headers,
            json={
                "amount": -10.00,
                "transaction_date": "2024-01-15"
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_list_transactions(self, client, auth_headers, sample_transactions):
        """Transactions can be listed."""
        response = client.get("/api/transactions/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 5
        assert len(data["data"]) == 5
        assert "has_more" in data
    
    def test_list_transactions_pagination(self, client, auth_headers, sample_transactions):
        """Transaction listing supports pagination."""
        # Get first 2
        response = client.get("/api/transactions/?limit=2&offset=0", headers=auth_headers)
        data = response.json()
        assert len(data["data"]) == 2
        assert data["has_more"] is True
        
        # Get next 2
        response = client.get("/api/transactions/?limit=2&offset=2", headers=auth_headers)
        data = response.json()
        assert len(data["data"]) == 2
    
    def test_list_transactions_filter_category(self, client, auth_headers, sample_transactions):
        """Transaction listing can filter by category."""
        response = client.get("/api/transactions/?category=Food", headers=auth_headers)
        data = response.json()
        
        assert data["total"] == 1
        assert data["data"][0]["category"] == "Food"
    
    def test_get_single_transaction(self, client, auth_headers, sample_transactions):
        """Single transaction can be retrieved."""
        txn_id = sample_transactions[0]["id"]
        
        response = client.get(f"/api/transactions/{txn_id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["id"] == txn_id
    
    def test_get_nonexistent_transaction(self, client, auth_headers):
        """Getting non-existent transaction returns 404."""
        fake_id = str(uuid.uuid4())
        response = client.get(f"/api/transactions/{fake_id}", headers=auth_headers)
        
        assert response.status_code == 404
    
    def test_update_transaction(self, client, auth_headers, sample_transactions):
        """Transaction can be updated."""
        txn_id = sample_transactions[0]["id"]
        
        response = client.patch(
            f"/api/transactions/{txn_id}",
            headers=auth_headers,
            json={"category": "Updated Category"}
        )
        
        assert response.status_code == 200
        assert response.json()["category"] == "Updated Category"
    
    def test_update_transaction_amount(self, client, auth_headers, sample_transactions):
        """Transaction amount can be updated."""
        txn_id = sample_transactions[0]["id"]
        
        response = client.patch(
            f"/api/transactions/{txn_id}",
            headers=auth_headers,
            json={"amount": 999.99}
        )
        
        assert response.status_code == 200
        assert float(response.json()["amount"]) == 999.99
    
    def test_delete_transaction(self, client, auth_headers):
        """Transaction can be deleted."""
        # Create a transaction
        create_resp = client.post(
            "/api/transactions/",
            headers=auth_headers,
            json={"amount": 10.00, "transaction_date": "2024-01-15"}
        )
        txn_id = create_resp.json()["id"]
        
        # Delete it
        response = client.delete(f"/api/transactions/{txn_id}", headers=auth_headers)
        assert response.status_code == 204
        
        # Verify deleted
        get_resp = client.get(f"/api/transactions/{txn_id}", headers=auth_headers)
        assert get_resp.status_code == 404
    
    def test_transaction_stats(self, client, auth_headers, sample_transactions):
        """Transaction stats are calculated correctly."""
        response = client.get("/api/transactions/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_transactions"] == 5
        # Sum of 25 + 50 + 75 + 100 + 125 = 375
        assert float(data["total_amount"]) == 375.00
        assert "categories" in data
        assert "sources" in data
    
    def test_transaction_isolation_between_users(self, client):
        """Users can only see their own transactions."""
        # User 1 registration and transaction
        resp1 = client.post("/api/auth/register", json={
            "email": "user1@example.com",
            "password": "User1Pass123!",
            "full_name": "User 1"
        })
        headers1 = {"Authorization": f"Bearer {resp1.json()['access_token']}"}
        
        client.post("/api/transactions/", headers=headers1,
                   json={"amount": 100.00, "transaction_date": "2024-01-15"})
        
        # User 2 registration and transaction
        resp2 = client.post("/api/auth/register", json={
            "email": "user2@example.com",
            "password": "User2Pass123!",
            "full_name": "User 2"
        })
        headers2 = {"Authorization": f"Bearer {resp2.json()['access_token']}"}
        
        client.post("/api/transactions/", headers=headers2,
                   json={"amount": 200.00, "transaction_date": "2024-01-15"})
        
        # User 1 only sees their transaction
        list1 = client.get("/api/transactions/", headers=headers1)
        assert list1.json()["total"] == 1
        assert float(list1.json()["data"][0]["amount"]) == 100.00
        
        # User 2 only sees their transaction
        list2 = client.get("/api/transactions/", headers=headers2)
        assert list2.json()["total"] == 1
        assert float(list2.json()["data"][0]["amount"]) == 200.00


# ==================== END-TO-END INTEGRATION ====================

class TestEndToEndFlow:
    """Complete flow from registration to transaction management."""
    
    def test_complete_user_journey(self, client):
        """Full user journey: register -> login -> create transactions -> stats."""
        
        # 1. Register
        reg_response = client.post("/api/auth/register", json={
            "email": "journey@example.com",
            "password": "Journey123!",
            "full_name": "Journey User"
        })
        assert reg_response.status_code == 201
        token = reg_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Check profile
        me_response = client.get("/api/auth/me", headers=headers)
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "journey@example.com"
        
        # 3. Create transactions
        for i in range(5):
            txn_response = client.post(
                "/api/transactions/",
                headers=headers,
                json={
                    "amount": (i + 1) * 10.0,
                    "transaction_date": f"2024-01-{i+1:02d}",
                    "category": "Food" if i % 2 == 0 else "Transport"
                }
            )
            assert txn_response.status_code == 201
        
        # 4. List transactions
        list_response = client.get("/api/transactions/", headers=headers)
        assert list_response.status_code == 200
        assert list_response.json()["total"] == 5
        
        # 5. Get stats
        stats_response = client.get("/api/transactions/stats", headers=headers)
        assert stats_response.status_code == 200
        stats = stats_response.json()
        assert stats["total_transactions"] == 5
        # 10+20+30+40+50 = 150
        assert float(stats["total_amount"]) == 150.00
        
        # 6. Update a transaction
        txn_id = list_response.json()["data"][0]["id"]
        update_response = client.patch(
            f"/api/transactions/{txn_id}",
            headers=headers,
            json={"category": "Updated"}
        )
        assert update_response.status_code == 200
        
        # 7. Delete a transaction
        delete_response = client.delete(f"/api/transactions/{txn_id}", headers=headers)
        assert delete_response.status_code == 204
        
        # 8. Verify final count
        final_list = client.get("/api/transactions/", headers=headers)
        assert final_list.json()["total"] == 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
