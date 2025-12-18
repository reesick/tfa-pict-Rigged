"""
Phase 1: Auth & Security Rigorous Tests
Tests: SQL injection, JWT exploits, password edge cases, email validation
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test database
TEST_DATABASE_URL = "sqlite:///./test_rigorous.db"
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


@pytest.fixture(scope="module")
def auth_token(client):
    """Create test user and return token."""
    client.post("/api/auth/register", json={
        "email": "security@test.com",
        "password": "SecurePass123!",
        "full_name": "Security Tester"
    })
    response = client.post("/api/auth/login", json={
        "email": "security@test.com",
        "password": "SecurePass123!"
    })
    return response.json()["access_token"]


# ==================== SQL INJECTION TESTS ====================

class TestSQLInjection:
    """Test SQL injection prevention."""
    
    def test_sql_injection_in_email(self, client):
        """SQL injection in email field should be rejected."""
        response = client.post("/api/auth/register", json={
            "email": "'; DROP TABLE users;--@evil.com",
            "password": "password123",
            "full_name": "Hacker"
        })
        # Should reject invalid email format
        assert response.status_code in [400, 422]
    
    def test_sql_injection_in_login(self, client):
        """SQL injection in login should not bypass auth."""
        response = client.post("/api/auth/login", json={
            "email": "' OR '1'='1",
            "password": "' OR '1'='1"
        })
        assert response.status_code in [400, 401, 422]
    
    def test_sql_injection_in_search(self, client, auth_token):
        """SQL injection in search param should be safe."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        response = client.get(
            "/api/transactions/?search='; DROP TABLE transactions;--",
            headers=headers
        )
        # Should return empty or handle gracefully, not crash
        assert response.status_code == 200


# ==================== JWT SECURITY TESTS ====================

class TestJWTSecurity:
    """Test JWT token security."""
    
    def test_expired_token_rejected(self, client):
        """Expired JWT should be rejected."""
        # This is a fabricated expired token
        expired_token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZXN0QHRlc3QuY29tIiwiZXhwIjoxNjAwMDAwMDAwfQ.invalid"
        headers = {"Authorization": f"Bearer {expired_token}"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_malformed_token_rejected(self, client):
        """Malformed JWT should be rejected."""
        headers = {"Authorization": "Bearer not.a.valid.token.at.all"}
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code == 401
    
    def test_missing_token_rejected(self, client):
        """Missing token should return 401 or 403."""
        response = client.get("/api/auth/me")
        assert response.status_code in [401, 403]
    
    def test_wrong_bearer_format(self, client, auth_token):
        """Wrong Authorization format should be rejected."""
        headers = {"Authorization": auth_token}  # Missing "Bearer "
        response = client.get("/api/auth/me", headers=headers)
        assert response.status_code in [401, 403]  # Either unauthorized or forbidden
    
    def test_token_with_extra_spaces(self, client, auth_token):
        """Token with extra spaces should be handled."""
        headers = {"Authorization": f"Bearer  {auth_token}"}  # Double space
        response = client.get("/api/auth/me", headers=headers)
        # Should either work or reject gracefully
        assert response.status_code in [200, 401]


# ==================== PASSWORD EDGE CASES ====================

class TestPasswordEdgeCases:
    """Test password validation edge cases."""
    
    def test_empty_password_rejected(self, client):
        """Empty password should be rejected."""
        response = client.post("/api/auth/register", json={
            "email": "empty@test.com",
            "password": "",
            "full_name": "Empty Pass"
        })
        assert response.status_code in [400, 422]
    
    def test_very_long_password(self, client):
        """Very long password should be handled."""
        long_pass = "A" * 1000  # 1000 character password
        response = client.post("/api/auth/register", json={
            "email": "longpass@test.com",
            "password": long_pass,
            "full_name": "Long Pass"
        })
        # Should either accept or reject gracefully
        assert response.status_code in [200, 201, 400, 422]
    
    def test_unicode_password(self, client):
        """Unicode characters in password should work."""
        response = client.post("/api/auth/register", json={
            "email": "unicode@test.com",
            "password": "密码🔐パスワード",
            "full_name": "Unicode User"
        })
        if response.status_code in [200, 201]:
            # Verify login works
            login_resp = client.post("/api/auth/login", json={
                "email": "unicode@test.com",
                "password": "密码🔐パスワード"
            })
            assert login_resp.status_code == 200
    
    def test_special_chars_password(self, client):
        """Special characters in password should work."""
        special_pass = "P@ss!#$%^&*()_+-=[]{}|;':\",./<>?"
        response = client.post("/api/auth/register", json={
            "email": "special@test.com",
            "password": special_pass,
            "full_name": "Special User"
        })
        if response.status_code in [200, 201]:
            login_resp = client.post("/api/auth/login", json={
                "email": "special@test.com",
                "password": special_pass
            })
            assert login_resp.status_code == 200
    
    def test_wrong_password_rejected(self, client, auth_token):
        """Wrong password should be rejected."""
        response = client.post("/api/auth/login", json={
            "email": "security@test.com",
            "password": "WrongPassword123!"
        })
        assert response.status_code == 401


# ==================== EMAIL VALIDATION ====================

class TestEmailValidation:
    """Test email validation and uniqueness."""
    
    def test_invalid_email_format(self, client):
        """Invalid email format should be rejected."""
        invalid_emails = [
            "notanemail",
            "@nodomain.com",
            "no@domain",
            "spaces in@email.com",
            "double@@at.com"
        ]
        for email in invalid_emails:
            response = client.post("/api/auth/register", json={
                "email": email,
                "password": "password123",
                "full_name": "Invalid Email"
            })
            assert response.status_code in [400, 422], f"Should reject: {email}"
    
    def test_duplicate_email_rejected(self, client, auth_token):
        """Duplicate email should be rejected."""
        response = client.post("/api/auth/register", json={
            "email": "security@test.com",  # Already exists
            "password": "password123",
            "full_name": "Duplicate"
        })
        assert response.status_code in [400, 409]
    
    def test_case_insensitive_email(self, client, auth_token):
        """Email should be case-insensitive for login."""
        response = client.post("/api/auth/login", json={
            "email": "SECURITY@TEST.COM",  # Uppercase
            "password": "SecurePass123!"
        })
        # May work or reject depending on case sensitivity implementation
        # Either behavior is acceptable, just shouldn't crash
        assert response.status_code in [200, 401]


# ==================== USER ISOLATION ====================

class TestUserIsolation:
    """Test that users can't access each other's data."""
    
    def test_user_cant_see_other_transactions(self, client, auth_token):
        """User A can't see User B's transactions."""
        headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Create a transaction for user A
        from datetime import date
        client.post("/api/transactions/", json={
            "amount": 100.0,
            "transaction_date": str(date.today()),
            "merchant_raw": "User A Store",
            "category": "Test"
        }, headers=headers)
        
        # Create User B
        client.post("/api/auth/register", json={
            "email": "userb@test.com",
            "password": "password123",
            "full_name": "User B"
        })
        login_b = client.post("/api/auth/login", json={
            "email": "userb@test.com",
            "password": "password123"
        })
        token_b = login_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}
        
        # User B should see 0 transactions
        response = client.get("/api/transactions/", headers=headers_b)
        assert response.status_code == 200
        assert response.json()["total"] == 0
