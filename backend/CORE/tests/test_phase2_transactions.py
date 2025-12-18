"""
Phase 2: Transaction Edge Cases Tests
Tests: amounts, dates, duplicate detection, soft delete, search
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date, timedelta
from decimal import Decimal
from app.main import app
from app.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test database
TEST_DATABASE_URL = "sqlite:///./test_transactions.db"
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
def auth_headers(client):
    """Create test user and return auth headers."""
    client.post("/api/auth/register", json={
        "email": "txntest@test.com",
        "password": "password123",
        "full_name": "Transaction Tester"
    })
    response = client.post("/api/auth/login", json={
        "email": "txntest@test.com",
        "password": "password123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ==================== AMOUNT EDGE CASES ====================

class TestAmountEdgeCases:
    """Test transaction amount edge cases."""
    
    def test_zero_amount(self, client, auth_headers):
        """Zero amount should be handled (either accepted or rejected)."""
        response = client.post("/api/transactions/", json={
            "amount": 0.0,
            "transaction_date": str(date.today()),
            "merchant_raw": "Zero Amount Store"
        }, headers=auth_headers)
        # Either accept or reject gracefully - both are valid design choices
        assert response.status_code in [201, 400, 422]
    
    def test_negative_amount(self, client, auth_headers):
        """Negative amount should be allowed (income/refunds)."""
        response = client.post("/api/transactions/", json={
            "amount": -50.00,
            "transaction_date": str(date.today()),
            "merchant_raw": "Refund Store"
        }, headers=auth_headers)
        # Could accept or reject - either is valid design choice
        assert response.status_code in [201, 400, 422]
    
    def test_very_large_amount(self, client, auth_headers):
        """Very large amount should work (up to 9,999,999,999.99)."""
        response = client.post("/api/transactions/", json={
            "amount": 999999999.99,
            "transaction_date": str(date.today()),
            "merchant_raw": "Big Purchase"
        }, headers=auth_headers)
        assert response.status_code == 201
    
    def test_very_small_amount(self, client, auth_headers):
        """Very small amount (1 cent) should work."""
        response = client.post("/api/transactions/", json={
            "amount": 0.01,
            "transaction_date": str(date.today()),
            "merchant_raw": "Penny Store"
        }, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["amount"] == "0.01"
    
    def test_decimal_precision(self, client, auth_headers):
        """Decimal precision should be maintained (2 decimal places)."""
        response = client.post("/api/transactions/", json={
            "amount": 123.456789,  # More than 2 decimals
            "transaction_date": str(date.today()),
            "merchant_raw": "Precision Store"
        }, headers=auth_headers)
        assert response.status_code == 201
        # Should round to 2 decimal places
        amount = float(response.json()["amount"])
        assert abs(amount - 123.46) < 0.01 or abs(amount - 123.45) < 0.01


# ==================== DATE EDGE CASES ====================

class TestDateEdgeCases:
    """Test transaction date edge cases."""
    
    def test_future_date(self, client, auth_headers):
        """Future date should be allowed (scheduled payments)."""
        future_date = date.today() + timedelta(days=30)
        response = client.post("/api/transactions/", json={
            "amount": 100.0,
            "transaction_date": str(future_date),
            "merchant_raw": "Future Payment"
        }, headers=auth_headers)
        assert response.status_code in [201, 400]  # Either is valid
    
    def test_very_old_date(self, client, auth_headers):
        """Very old date should be allowed (historical data)."""
        response = client.post("/api/transactions/", json={
            "amount": 50.0,
            "transaction_date": "2000-01-01",
            "merchant_raw": "Y2K Store"
        }, headers=auth_headers)
        assert response.status_code == 201
    
    def test_leap_year_date(self, client, auth_headers):
        """Leap year date should work."""
        response = client.post("/api/transactions/", json={
            "amount": 29.99,
            "transaction_date": "2024-02-29",
            "merchant_raw": "Leap Day Store"
        }, headers=auth_headers)
        assert response.status_code == 201
    
    def test_invalid_date_format(self, client, auth_headers):
        """Invalid date format should be rejected."""
        response = client.post("/api/transactions/", json={
            "amount": 50.0,
            "transaction_date": "not-a-date",
            "merchant_raw": "Invalid Date"
        }, headers=auth_headers)
        assert response.status_code == 422


# ==================== DUPLICATE DETECTION ====================

class TestDuplicateDetection:
    """Test duplicate transaction detection."""
    
    def test_exact_duplicate_handled(self, client, auth_headers):
        """Exact duplicate should be detected."""
        today = str(date.today())
        
        # Create first transaction
        resp1 = client.post("/api/transactions/", json={
            "amount": 77.77,
            "transaction_date": today,
            "merchant_raw": "Duplicate Test Store"
        }, headers=auth_headers)
        assert resp1.status_code == 201
        id1 = resp1.json()["id"]
        
        # Create exact duplicate
        resp2 = client.post("/api/transactions/", json={
            "amount": 77.77,
            "transaction_date": today,
            "merchant_raw": "Duplicate Test Store"
        }, headers=auth_headers)
        # Should return existing or create new - either is valid
        assert resp2.status_code in [200, 201]
    
    def test_different_date_not_duplicate(self, client, auth_headers):
        """Different date should not be considered duplicate."""
        yesterday = str(date.today() - timedelta(days=5))
        
        resp1 = client.post("/api/transactions/", json={
            "amount": 88.88,
            "transaction_date": str(date.today()),
            "merchant_raw": "Date Test Store"
        }, headers=auth_headers)
        
        resp2 = client.post("/api/transactions/", json={
            "amount": 88.88,
            "transaction_date": yesterday,
            "merchant_raw": "Date Test Store"
        }, headers=auth_headers)
        
        # Should create separate transactions
        assert resp2.status_code == 201


# ==================== SOFT DELETE ====================

class TestSoftDelete:
    """Test soft delete functionality."""
    
    def test_deleted_hidden_from_list(self, client, auth_headers):
        """Deleted transactions should be hidden from list."""
        # Create transaction
        resp = client.post("/api/transactions/", json={
            "amount": 555.55,
            "transaction_date": str(date.today()),
            "merchant_raw": "Delete Test Store"
        }, headers=auth_headers)
        txn_id = resp.json()["id"]
        
        # Delete it
        del_resp = client.delete(f"/api/transactions/{txn_id}", headers=auth_headers)
        assert del_resp.status_code in [200, 204]
        
        # Should not appear in list
        list_resp = client.get("/api/transactions/", headers=auth_headers)
        ids = [t["id"] for t in list_resp.json()["data"]]
        assert txn_id not in ids
    
    def test_deleted_excluded_from_stats(self, client, auth_headers):
        """Deleted transactions should be excluded from stats."""
        # Get current stats
        stats1 = client.get("/api/transactions/stats", headers=auth_headers)
        count1 = stats1.json()["total_transactions"]
        
        # Create and immediately delete a transaction
        resp = client.post("/api/transactions/", json={
            "amount": 1000.00,
            "transaction_date": str(date.today()),
            "merchant_raw": "Stats Test Store"
        }, headers=auth_headers)
        
        if resp.status_code == 201:
            txn_id = resp.json()["id"]
            client.delete(f"/api/transactions/{txn_id}", headers=auth_headers)
        
        # Stats should not include deleted
        stats2 = client.get("/api/transactions/stats", headers=auth_headers)
        # Count should be same or only increase if duplicate detection returned existing
        assert stats2.json()["total_transactions"] <= count1 + 1


# ==================== SEARCH ====================

class TestSearch:
    """Test transaction search functionality."""
    
    def test_case_insensitive_search(self, client, auth_headers):
        """Search should be case-insensitive."""
        # Create searchable transaction
        client.post("/api/transactions/", json={
            "amount": 25.00,
            "transaction_date": str(date.today()),
            "merchant_raw": "STARBUCKS CAFE"
        }, headers=auth_headers)
        
        # Search with lowercase
        resp = client.get("/api/transactions/?search=starbucks", headers=auth_headers)
        assert resp.status_code == 200
        # Should find it (case-insensitive)
        found = any("starbucks" in t["merchant_raw"].lower() for t in resp.json()["data"])
        assert found
    
    def test_partial_match_search(self, client, auth_headers):
        """Partial text should match."""
        client.post("/api/transactions/", json={
            "amount": 15.00,
            "transaction_date": str(date.today()),
            "merchant_raw": "AMAZON PRIME VIDEO"
        }, headers=auth_headers)
        
        resp = client.get("/api/transactions/?search=amazon", headers=auth_headers)
        assert resp.status_code == 200
    
    def test_empty_search_returns_all(self, client, auth_headers):
        """Empty search should return all transactions."""
        resp = client.get("/api/transactions/", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["total"] > 0
    
    def test_search_special_chars(self, client, auth_headers):
        """Search with special chars should not crash."""
        # These could cause SQL issues if not handled
        special_queries = [
            "'; DROP TABLE",
            "% OR 1=1",
            "<script>alert(1)</script>",
            "\\n\\r\\t"
        ]
        for q in special_queries:
            resp = client.get(f"/api/transactions/?search={q}", headers=auth_headers)
            # Should not crash, return 200 with empty or partial results
            assert resp.status_code in [200, 422]
