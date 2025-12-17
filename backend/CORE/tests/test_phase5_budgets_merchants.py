"""
Phase 5: Budget and Merchant API Tests
Comprehensive tests with edge cases.
"""
import os

os.environ["DATABASE_URL"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-minimum-32-characters-long"

import pytest
import uuid
from datetime import date, timedelta


# ==================== BUDGET TESTS ====================

class TestBudgetAPI:
    """Budget API tests with edge cases."""
    
    def _get_auth_headers(self, client):
        """Create user and get auth headers."""
        response = client.post("/api/auth/register", json={
            "email": f"budget{uuid.uuid4().hex[:8]}@test.com",
            "password": "BudgetPass123!",
            "full_name": "Budget User"
        })
        return {"Authorization": f"Bearer {response.json()['access_token']}"}
    
    def test_create_budget(self, client):
        """Budget can be created."""
        headers = self._get_auth_headers(client)
        
        response = client.post("/api/budgets/", headers=headers, json={
            "category": "Food",
            "limit_amount": 500.00,
            "period": "monthly",
            "start_date": str(date.today()),
            "alert_threshold": 80.0
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["category"] == "Food"
        assert float(data["limit_amount"]) == 500.00
        assert data["is_active"] is True
    
    def test_create_budget_minimal(self, client):
        """Budget can be created with minimal fields."""
        headers = self._get_auth_headers(client)
        
        response = client.post("/api/budgets/", headers=headers, json={
            "category": "Transport",
            "limit_amount": 200.00,
            "start_date": str(date.today())
        })
        
        assert response.status_code == 201
        assert response.json()["period"] == "monthly"  # Default
        assert response.json()["alert_threshold"] == 80.0  # Default
    
    def test_create_budget_validates_amount(self, client):
        """Budget creation validates amount is positive."""
        headers = self._get_auth_headers(client)
        
        response = client.post("/api/budgets/", headers=headers, json={
            "category": "Food",
            "limit_amount": -100.00,
            "start_date": str(date.today())
        })
        
        assert response.status_code == 422
    
    def test_list_budgets(self, client):
        """Budgets can be listed."""
        headers = self._get_auth_headers(client)
        
        # Create budgets
        for cat in ["Food", "Transport", "Entertainment"]:
            client.post("/api/budgets/", headers=headers, json={
                "category": cat,
                "limit_amount": 300.00,
                "start_date": str(date.today())
            })
        
        response = client.get("/api/budgets/", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        assert len(data["data"]) == 3
    
    def test_get_single_budget(self, client):
        """Single budget can be retrieved."""
        headers = self._get_auth_headers(client)
        
        create_resp = client.post("/api/budgets/", headers=headers, json={
            "category": "Shopping",
            "limit_amount": 400.00,
            "start_date": str(date.today())
        })
        budget_id = create_resp.json()["id"]
        
        response = client.get(f"/api/budgets/{budget_id}", headers=headers)
        
        assert response.status_code == 200
        assert response.json()["category"] == "Shopping"
    
    def test_get_nonexistent_budget(self, client):
        """Getting non-existent budget returns 404."""
        headers = self._get_auth_headers(client)
        fake_id = str(uuid.uuid4())
        
        response = client.get(f"/api/budgets/{fake_id}", headers=headers)
        
        assert response.status_code == 404
    
    def test_update_budget(self, client):
        """Budget can be updated."""
        headers = self._get_auth_headers(client)
        
        create_resp = client.post("/api/budgets/", headers=headers, json={
            "category": "Bills",
            "limit_amount": 600.00,
            "start_date": str(date.today())
        })
        budget_id = create_resp.json()["id"]
        
        response = client.patch(f"/api/budgets/{budget_id}", headers=headers, json={
            "limit_amount": 800.00,
            "alert_threshold": 90.0
        })
        
        assert response.status_code == 200
        assert float(response.json()["limit_amount"]) == 800.00
        assert response.json()["alert_threshold"] == 90.0
    
    def test_delete_budget(self, client):
        """Budget can be deleted."""
        headers = self._get_auth_headers(client)
        
        create_resp = client.post("/api/budgets/", headers=headers, json={
            "category": "Temp",
            "limit_amount": 100.00,
            "start_date": str(date.today())
        })
        budget_id = create_resp.json()["id"]
        
        # Delete
        response = client.delete(f"/api/budgets/{budget_id}", headers=headers)
        assert response.status_code == 204
        
        # Verify deleted
        get_resp = client.get(f"/api/budgets/{budget_id}", headers=headers)
        assert get_resp.status_code == 404
    
    def test_budget_with_spending_calculation(self, client):
        """Budget spending is calculated from transactions."""
        headers = self._get_auth_headers(client)
        
        # Create budget
        budget_resp = client.post("/api/budgets/", headers=headers, json={
            "category": "Food",
            "limit_amount": 100.00,
            "start_date": str(date.today())
        })
        
        # Create transactions in that category
        for i in range(3):
            client.post("/api/transactions/", headers=headers, json={
                "amount": 25.00,
                "transaction_date": str(date.today()),
                "category": "Food"
            })
        
        # Get budget - should show spending
        response = client.get("/api/budgets/", headers=headers)
        budget = response.json()["data"][0]
        
        assert float(budget["current_spending"]) == 75.00
        assert budget["percentage_used"] == 75.0
    
    def test_budget_alerts(self, client):
        """Budget alerts when threshold exceeded."""
        headers = self._get_auth_headers(client)
        
        # Create budget with low limit
        client.post("/api/budgets/", headers=headers, json={
            "category": "Food",
            "limit_amount": 50.00,
            "start_date": str(date.today()),
            "alert_threshold": 50.0
        })
        
        # Spend 60% (over 50% threshold)
        client.post("/api/transactions/", headers=headers, json={
            "amount": 30.00,
            "transaction_date": str(date.today()),
            "category": "Food"
        })
        
        # Check alerts
        response = client.get("/api/budgets/alerts", headers=headers)
        
        assert response.status_code == 200
        alerts = response.json()
        assert len(alerts) == 1
        assert alerts[0]["category"] == "Food"
        assert alerts[0]["percentage_used"] >= 50.0
    
    def test_budget_isolation_between_users(self, client):
        """Users can only see their own budgets."""
        headers1 = self._get_auth_headers(client)
        headers2 = self._get_auth_headers(client)
        
        # User 1 creates budget
        client.post("/api/budgets/", headers=headers1, json={
            "category": "User1Food",
            "limit_amount": 100.00,
            "start_date": str(date.today())
        })
        
        # User 2 creates budget
        client.post("/api/budgets/", headers=headers2, json={
            "category": "User2Food",
            "limit_amount": 200.00,
            "start_date": str(date.today())
        })
        
        # User 1 only sees their budget
        resp1 = client.get("/api/budgets/", headers=headers1)
        assert resp1.json()["total"] == 1
        assert resp1.json()["data"][0]["category"] == "User1Food"
        
        # User 2 only sees their budget
        resp2 = client.get("/api/budgets/", headers=headers2)
        assert resp2.json()["total"] == 1
        assert resp2.json()["data"][0]["category"] == "User2Food"


# ==================== MERCHANT TESTS ====================

class TestMerchantAPI:
    """Merchant API tests."""
    
    def _get_auth_headers(self, client):
        """Create user and get auth headers."""
        response = client.post("/api/auth/register", json={
            "email": f"merch{uuid.uuid4().hex[:8]}@test.com",
            "password": "MerchPass123!",
            "full_name": "Merchant User"
        })
        return {"Authorization": f"Bearer {response.json()['access_token']}"}
    
    def test_create_merchant(self, client):
        """Merchant can be created."""
        headers = self._get_auth_headers(client)
        
        response = client.post("/api/merchants/", headers=headers, json={
            "canonical_name": "Starbucks",
            "category": "Food & Drink",
            "subcategory": "Coffee"
        })
        
        assert response.status_code == 201
        data = response.json()
        assert data["canonical_name"] == "Starbucks"
        assert data["category"] == "Food & Drink"
    
    def test_get_merchant(self, client):
        """Merchant can be retrieved by ID."""
        headers = self._get_auth_headers(client)
        
        create_resp = client.post("/api/merchants/", headers=headers, json={
            "canonical_name": "McDonald's",
            "category": "Food & Drink"
        })
        merchant_id = create_resp.json()["id"]
        
        response = client.get(f"/api/merchants/{merchant_id}", headers=headers)
        
        assert response.status_code == 200
        assert response.json()["canonical_name"] == "McDonald's"
    
    def test_get_nonexistent_merchant(self, client):
        """Getting non-existent merchant returns 404."""
        headers = self._get_auth_headers(client)
        fake_id = str(uuid.uuid4())
        
        response = client.get(f"/api/merchants/{fake_id}", headers=headers)
        
        assert response.status_code == 404
    
    def test_search_merchants(self, client):
        """Merchants can be searched."""
        headers = self._get_auth_headers(client)
        
        # Create merchants
        for name in ["Apple Store", "Apple Music", "Starbucks"]:
            client.post("/api/merchants/", headers=headers, json={
                "canonical_name": name,
                "category": "Shopping"
            })
        
        # Search for "Apple"
        response = client.get("/api/merchants/search?q=Apple", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert data["query"] == "Apple"
    
    def test_search_merchants_min_length(self, client):
        """Search requires minimum 2 characters."""
        headers = self._get_auth_headers(client)
        
        response = client.get("/api/merchants/search?q=A", headers=headers)
        
        assert response.status_code == 422  # Validation error
    
    def test_search_merchants_case_insensitive(self, client):
        """Merchant search is case insensitive."""
        headers = self._get_auth_headers(client)
        
        client.post("/api/merchants/", headers=headers, json={
            "canonical_name": "WALMART",
            "category": "Shopping"
        })
        
        # Search with different cases
        resp_lower = client.get("/api/merchants/search?q=walmart", headers=headers)
        resp_upper = client.get("/api/merchants/search?q=WALMART", headers=headers)
        resp_mixed = client.get("/api/merchants/search?q=WalMart", headers=headers)
        
        assert resp_lower.json()["total"] == 1
        assert resp_upper.json()["total"] == 1
        assert resp_mixed.json()["total"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
