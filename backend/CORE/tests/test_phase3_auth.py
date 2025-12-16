"""Tests for Phase 3: Authentication System."""
import pytest
import time
from app.utils.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token_type
)


class TestPasswordHashing:
    """Test password hashing and verification."""
    
    def test_hash_password_creates_bcrypt_hash(self):
        """Test password hashing creates valid bcrypt hash."""
        password = "SecurePassword123!"
        hashed = hash_password(password)
        
        # Verify bcrypt format
        assert hashed.startswith("$2b$")
        assert len(hashed) == 60
        
        # Password not in plaintext
        assert password not in hashed
    
    def test_hash_password_uses_salt(self):
        """Test same password creates different hashes (salt)."""
        password = "test123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        
        # Different hashes due to random salt
        assert hash1 != hash2
        
        # Both verify correctly
        assert verify_password(password, hash1)
        assert verify_password(password, hash2)
    
    def test_verify_password_correct(self):
        """Test password verification with correct password."""
        password = "CorrectPassword!"
        hashed = hash_password(password)
        
        assert verify_password(password, hashed) is True
    
    def test_verify_password_incorrect(self):
        """Test password verification with wrong password."""
        password = "CorrectPassword!"
        hashed = hash_password(password)
        
        assert verify_password("WrongPassword!", hashed) is False
    
    def test_password_hashing_timing(self):
        """Test bcrypt hashing takes appropriate time (~150-300ms)."""
        password = "TestPassword123!"
        
        start = time.time()
        hash_password(password)
        elapsed = time.time() - start
        
        # Should take 150-500ms with 12 rounds
        assert 0.05 < elapsed < 1.0, f"Hashing took {elapsed}s (expected 0.05-1.0s)"


class TestJWTTokens:
    """Test JWT token creation and validation."""
    
    def test_create_access_token_structure(self):
        """Test access token has correct structure."""
        token = create_access_token({"sub": "user-123"})
        
        # JWT has 3 parts: header.payload.signature
        parts = token.split(".")
        assert len(parts) == 3
    
    def test_create_access_token_payload(self):
        """Test access token contains correct payload."""
        token = create_access_token({"sub": "user-123"})
        payload = decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user-123"
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
    
    def test_create_refresh_token(self):
        """Test refresh token creation."""
        token = create_refresh_token({"sub": "user-456"})
        payload = decode_token(token)
        
        assert payload is not None
        assert payload["sub"] == "user-456"
        assert payload["type"] == "refresh"
    
    def test_decode_token_valid(self):
        """Test decoding valid token."""
        token = create_access_token({"sub": "user-789", "extra": "data"})
        payload = decode_token(token)
        
        assert payload["sub"] == "user-789"
        assert payload["extra"] == "data"
    
    def test_decode_token_invalid(self):
        """Test decoding invalid token returns None."""
        invalid_token = "invalid.jwt.token"
        payload = decode_token(invalid_token)
        
        assert payload is None
    
    def test_verify_token_type_access(self):
        """Test verifying access token type."""
        access_token = create_access_token({"sub": "user-1"})
        payload = verify_token_type(access_token, "access")
        
        assert payload is not None
        assert payload["type"] == "access"
    
    def test_verify_token_type_refresh(self):
        """Test verifying refresh token type."""
        refresh_token = create_refresh_token({"sub": "user-2"})
        payload = verify_token_type(refresh_token, "refresh")
        
        assert payload is not None
        assert payload["type"] == "refresh"
    
    def test_verify_token_type_mismatch(self):
        """Test verifying wrong token type returns None."""
        access_token = create_access_token({"sub": "user-3"})
        payload = verify_token_type(access_token, "refresh")
        
        assert payload is None


class TestAuthEndpoints:
    """Test authentication API endpoints."""
    
    def test_register_success(self, client):
        """Test successful user registration."""
        response = client.post("/api/auth/register", json={
            "email": "newuser@example.com",
            "password": "StrongPass123!",
            "full_name": "New User",
            "phone": "+9876543210"
        })
        
        assert response.status_code == 201
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["expires_in"] == 3600
        
        # Verify tokens are valid
        access_payload = decode_token(data["access_token"])
        assert access_payload is not None
        assert access_payload["type"] == "access"
        
        refresh_payload = decode_token(data["refresh_token"])
        assert refresh_payload is not None
        assert refresh_payload["type"] == "refresh"
    
    def test_register_duplicate_email(self, client):
        """Test registration fails with duplicate email."""
        # Register first user
        client.post("/api/auth/register", json={
            "email": "duplicate@example.com",
            "password": "Pass123!",
            "full_name": "First User"
        })
        
        # Try to register again
        response = client.post("/api/auth/register", json={
            "email": "duplicate@example.com",
            "password": "DifferentPass123!",
            "full_name": "Second User"
        })
        
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()
    
    def test_register_invalid_email(self, client):
        """Test registration fails with invalid email."""
        response = client.post("/api/auth/register", json={
            "email": "not-an-email",
            "password": "Pass123!",
            "full_name": "User"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_register_short_password(self, client):
        """Test registration fails with short password."""
        response = client.post("/api/auth/register", json={
            "email": "user@example.com",
            "password": "short",
            "full_name": "User"
        })
        
        assert response.status_code == 422
    
    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post("/api/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_login_wrong_password(self, client, test_user):
        """Test login fails with wrong password."""
        response = client.post("/api/auth/login", json={
            "email": test_user["email"],
            "password": "WrongPassword123!"
        })
        
        assert response.status_code == 401
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_login_nonexistent_user(self, client):
        """Test login fails for non-existent user."""
        response = client.post("/api/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "SomePass123!"
        })
        
        assert response.status_code == 401
    
    def test_get_me_authenticated(self, client, auth_headers, test_user):
        """Test get current user with valid token."""
        response = client.get("/api/auth/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == test_user["email"]
        assert data["full_name"] == "Test User"
        assert data["phone"] == "+1234567890"
        assert data["is_active"] is True
        assert data["is_verified"] is False
        assert "id" in data
        assert "created_at" in data
        
        # Password should not be returned
        assert "password" not in data
        assert "hashed_password" not in data
    
    def test_get_me_no_token(self, client):
        """Test get current user without token fails."""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 403  # No credentials
    
    def test_get_me_invalid_token(self, client):
        """Test get current user with invalid token fails."""
        headers = {"Authorization": "Bearer invalid.token.here"}
        response = client.get("/api/auth/me", headers=headers)
        
        assert response.status_code == 401
    
    def test_refresh_token_success(self, client, test_user):
        """Test refreshing access token."""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": test_user["refresh_token"]
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        
        # New tokens should be different
        assert data["access_token"] != test_user["access_token"]
    
    def test_refresh_token_invalid(self, client):
        """Test refresh with invalid token fails."""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": "invalid.refresh.token"
        })
        
        assert response.status_code == 401
    
    def test_refresh_token_with_access_token(self, client, test_user):
        """Test refresh fails when using access token instead of refresh token."""
        response = client.post("/api/auth/refresh", json={
            "refresh_token": test_user["access_token"]  # Wrong token type
        })
        
        assert response.status_code == 401
    
    def test_change_password_success(self, client, auth_headers, test_user):
        """Test successful password change."""
        response = client.post("/api/auth/change-password", json={
            "current_password": test_user["password"],
            "new_password": "NewSecurePass456!"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        assert "successfully" in response.json()["message"].lower()
        
        # Verify can login with new password
        login_response = client.post("/api/auth/login", json={
            "email": test_user["email"],
            "password": "NewSecurePass456!"
        })
        assert login_response.status_code == 200
        
        # Old password should not work
        old_login = client.post("/api/auth/login", json={
            "email": test_user["email"],
            "password": test_user["password"]
        })
        assert old_login.status_code == 401
    
    def test_change_password_wrong_current(self, client, auth_headers):
        """Test password change fails with wrong current password."""
        response = client.post("/api/auth/change-password", json={
            "current_password": "WrongCurrentPass!",
            "new_password": "NewPass123!"
        }, headers=auth_headers)
        
        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()
    
    def test_change_password_same_as_current(self, client, auth_headers, test_user):
        """Test password change fails if new password same as current."""
        response = client.post("/api/auth/change-password", json={
            "current_password": test_user["password"],
            "new_password": test_user["password"]  # Same password
        }, headers=auth_headers)
        
        assert response.status_code == 400
        assert "different" in response.json()["detail"].lower()
    
    def test_logout(self, client, auth_headers):
        """Test logout endpoint."""
        response = client.post("/api/auth/logout", headers=auth_headers)
        
        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()


class TestAuthIntegration:
    """Integration tests for authentication flow."""
    
    def test_complete_auth_flow(self, client, db):
        """Test complete authentication flow: register → login → get profile → change password."""
        # 1. Register
        register_response = client.post("/api/auth/register", json={
            "email": "flowtest@example.com",
            "password": "FlowPass123!",
            "full_name": "Flow Test User"
        })
        assert register_response.status_code == 201
        tokens = register_response.json()
        
        # 2. Get profile with token from registration
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        profile_response = client.get("/api/auth/me", headers=headers)
        assert profile_response.status_code == 200
        assert profile_response.json()["email"] == "flowtest@example.com"
        
        # 3. Change password
        change_response = client.post("/api/auth/change-password", json={
            "current_password": "FlowPass123!",
            "new_password": "NewFlowPass456!"
        }, headers=headers)
        assert change_response.status_code == 200
        
        # 4. Login with new password
        login_response = client.post("/api/auth/login", json={
            "email": "flowtest@example.com",
            "password": "NewFlowPass456!"
        })
        assert login_response.status_code == 200
        
        # 5. Verify old password doesn't work
        old_login = client.post("/api/auth/login", json={
            "email": "flowtest@example.com",
            "password": "FlowPass123!"
        })
        assert old_login.status_code == 401
    
    def test_user_persists_in_database(self, client, db):
        """Test user is correctly saved to database."""
        from app.models.user import User
        
        # Register user
        client.post("/api/auth/register", json={
            "email": "dbtest@example.com",
            "password": "DbPass123!",
            "full_name": "Database Test",
            "phone": "+1111111111"
        })
        
        # Query database
        user = db.query(User).filter(User.email == "dbtest@example.com").first()
        
        assert user is not None
        assert user.email == "dbtest@example.com"
        assert user.full_name == "Database Test"
        assert user.phone == "+1111111111"
        assert user.is_active is True
        assert user.is_verified is False
        assert user.hashed_password.startswith("$2b$")
        assert user.wallet_addresses == []
        assert user.preferences == {}
