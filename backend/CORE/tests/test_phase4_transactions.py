"""Tests for Phase 4: Transaction APIs."""
import pytest
from decimal import Decimal
from datetime import date, timedelta
from uuid import uuid4


class TestTransactionCreate:
    """Test transaction creation."""
    
    def test_create_transaction_success(self, client, auth_headers):
        """Test creating a new transaction."""
        response = client.post("/api/transactions/", json={
            "amount": "45.50",
            "date": "2024-12-15",
            "merchant_raw": "SWIGGY BANGALORE",
            "category": "Food & Dining",
            "description": "Lunch order",
            "source": "manual"
        }, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["amount"] == "45.50"
        assert data["date"] == "2024-12-15"
        assert data["merchant_raw"] == "SWIGGY BANGALORE"
        assert data["category"] == "Food & Dining"
        assert data["description"] == "Lunch order"
        assert data["source"] == "manual"
        assert data["is_anchored"] is False
        assert data["anomaly_score"] == 0.0
        assert "id" in data
        assert "created_at" in data
    
    def test_create_transaction_minimal(self, client, auth_headers):
        """Test creating transaction with only required fields."""
        response = client.post("/api/transactions/", json={
            "amount": "100.00",
            "date": "2024-12-10"
        }, headers=auth_headers)
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["amount"] == "100.00"
        assert data["date"] == "2024-12-10"
        assert data["source"] == "manual"
    
    def test_create_transaction_invalid_amount(self, client, auth_headers):
        """Test creating transaction with invalid amount fails."""
        response = client.post("/api/transactions/", json={
            "amount": "-50.00",
            "date": "2024-12-15"
        }, headers=auth_headers)
        
        assert response.status_code == 422
    
    def test_create_transaction_no_auth(self, client):
        """Test creating transaction without auth fails."""
        response = client.post("/api/transactions/", json={
            "amount": "50.00",
            "date": "2024-12-15"
        })
        
        assert response.status_code == 403


class TestTransactionList:
    """Test transaction listing and filtering."""
    
    @pytest.fixture
    def sample_transactions(self, client, auth_headers):
        """Create sample transactions for testing."""
        transactions = [
            {"amount": "50.00", "date": "2024-12-15", "category": "Food", "merchant_raw": "SWIGGY"},
            {"amount": "100.00", "date": "2024-12-14", "category": "Transport", "merchant_raw": "UBER"},
            {"amount": "200.00", "date": "2024-12-13", "category": "Shopping", "merchant_raw": "AMAZON"},
            {"amount": "75.00", "date": "2024-12-12", "category": "Food", "merchant_raw": "ZOMATO"},
            {"amount": "150.00", "date": "2024-12-11", "category": "Entertainment", "merchant_raw": "NETFLIX"},
        ]
        
        created = []
        for txn in transactions:
            response = client.post("/api/transactions/", json=txn, headers=auth_headers)
            assert response.status_code == 201
            created.append(response.json())
        
        return created
    
    def test_list_transactions(self, client, auth_headers, sample_transactions):
        """Test listing all transactions."""
        response = client.get("/api/transactions/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total"] == 5
        assert len(data["data"]) == 5
        assert data["has_more"] is False
        
        # Verify ordered by date desc
        dates = [t["date"] for t in data["data"]]
        assert dates == sorted(dates, reverse=True)
    
    def test_list_transactions_pagination(self, client, auth_headers, sample_transactions):
        """Test pagination."""
        # First page
        response1 = client.get("/api/transactions/?limit=2&offset=0", headers=auth_headers)
        data1 = response1.json()
        
        assert len(data1["data"]) == 2
        assert data1["total"] == 5
        assert data1["has_more"] is True
        
        # Second page
        response2 = client.get("/api/transactions/?limit=2&offset=2", headers=auth_headers)
        data2 = response2.json()
        
        assert len(data2["data"]) == 2
        assert data2["has_more"] is True
        
        # Third page
        response3 = client.get("/api/transactions/?limit=2&offset=4", headers=auth_headers)
        data3 = response3.json()
        
        assert len(data3["data"]) == 1
        assert data3["has_more"] is False
    
    def test_list_transactions_filter_category(self, client, auth_headers, sample_transactions):
        """Test filter by category."""
        response = client.get("/api/transactions/?category=Food", headers=auth_headers)
        data = response.json()
        
        assert data["total"] == 2
        assert all(t["category"] == "Food" for t in data["data"])
    
    def test_list_transactions_filter_date_range(self, client, auth_headers, sample_transactions):
        """Test filter by date range."""
        response = client.get(
            "/api/transactions/?since=2024-12-13&until=2024-12-15",
            headers=auth_headers
        )
        data = response.json()
        
        assert data["total"] == 3
    
    def test_list_transactions_filter_amount_range(self, client, auth_headers, sample_transactions):
        """Test filter by amount range."""
        response = client.get(
            "/api/transactions/?min_amount=100&max_amount=200",
            headers=auth_headers
        )
        data = response.json()
        
        assert data["total"] == 3  # 100, 150, 200
    
    def test_list_transactions_search(self, client, auth_headers, sample_transactions):
        """Test search in merchant_raw."""
        response = client.get("/api/transactions/?search=SWIGGY", headers=auth_headers)
        data = response.json()
        
        assert data["total"] == 1
        assert data["data"][0]["merchant_raw"] == "SWIGGY"


class TestTransactionGet:
    """Test getting single transaction."""
    
    def test_get_transaction_success(self, client, auth_headers):
        """Test getting a transaction by ID."""
        # Create transaction
        create_response = client.post("/api/transactions/", json={
            "amount": "99.99",
            "date": "2024-12-15",
            "category": "Test"
        }, headers=auth_headers)
        
        transaction_id = create_response.json()["id"]
        
        # Get transaction
        response = client.get(f"/api/transactions/{transaction_id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["id"] == transaction_id
        assert response.json()["amount"] == "99.99"
    
    def test_get_transaction_not_found(self, client, auth_headers):
        """Test getting non-existent transaction."""
        fake_id = str(uuid4())
        response = client.get(f"/api/transactions/{fake_id}", headers=auth_headers)
        
        assert response.status_code == 404


class TestTransactionUpdate:
    """Test transaction updates."""
    
    def test_update_transaction_success(self, client, auth_headers):
        """Test updating a transaction."""
        # Create transaction
        create_response = client.post("/api/transactions/", json={
            "amount": "50.00",
            "date": "2024-12-15",
            "category": "Food"
        }, headers=auth_headers)
        
        transaction_id = create_response.json()["id"]
        
        # Update transaction
        response = client.patch(f"/api/transactions/{transaction_id}", json={
            "amount": "75.00",
            "category": "Shopping"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["amount"] == "75.00"
        assert data["category"] == "Shopping"
        assert data["date"] == "2024-12-15"  # Unchanged
    
    def test_update_transaction_partial(self, client, auth_headers):
        """Test partial update (only some fields)."""
        # Create transaction
        create_response = client.post("/api/transactions/", json={
            "amount": "100.00",
            "date": "2024-12-15",
            "category": "Food",
            "description": "Original description"
        }, headers=auth_headers)
        
        transaction_id = create_response.json()["id"]
        
        # Update only description
        response = client.patch(f"/api/transactions/{transaction_id}", json={
            "description": "Updated description"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["description"] == "Updated description"
        assert data["amount"] == "100.00"  # Unchanged
        assert data["category"] == "Food"  # Unchanged


class TestTransactionDelete:
    """Test transaction deletion."""
    
    def test_delete_transaction_success(self, client, auth_headers):
        """Test deleting a transaction."""
        # Create transaction
        create_response = client.post("/api/transactions/", json={
            "amount": "50.00",
            "date": "2024-12-15"
        }, headers=auth_headers)
        
        transaction_id = create_response.json()["id"]
        
        # Delete transaction
        response = client.delete(f"/api/transactions/{transaction_id}", headers=auth_headers)
        
        assert response.status_code == 204
        
        # Verify deleted
        get_response = client.get(f"/api/transactions/{transaction_id}", headers=auth_headers)
        assert get_response.status_code == 404
    
    def test_delete_transaction_not_found(self, client, auth_headers):
        """Test deleting non-existent transaction."""
        fake_id = str(uuid4())
        response = client.delete(f"/api/transactions/{fake_id}", headers=auth_headers)
        
        assert response.status_code == 404


class TestTransactionCorrection:
    """Test transaction correction for ML feedback."""
    
    def test_correct_category(self, client, auth_headers):
        """Test correcting transaction category."""
        # Create transaction
        create_response = client.post("/api/transactions/", json={
            "amount": "50.00",
            "date": "2024-12-15",
            "category": "Food"
        }, headers=auth_headers)
        
        transaction_id = create_response.json()["id"]
        
        # Correct category
        response = client.post(f"/api/transactions/{transaction_id}/correct", json={
            "field_corrected": "category",
            "new_value": "Groceries",
            "correction_reason": "This was a supermarket purchase"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["field_corrected"] == "category"
        assert data["old_value"] == "Food"
        assert data["new_value"] == "Groceries"
        assert "successfully" in data["message"].lower()
        
        # Verify transaction updated
        get_response = client.get(f"/api/transactions/{transaction_id}", headers=auth_headers)
        assert get_response.json()["category"] == "Groceries"
    
    def test_correct_merchant(self, client, auth_headers):
        """Test correcting merchant name."""
        # Create transaction
        create_response = client.post("/api/transactions/", json={
            "amount": "100.00",
            "date": "2024-12-15",
            "merchant_raw": "AMAZN INC"
        }, headers=auth_headers)
        
        transaction_id = create_response.json()["id"]
        
        # Correct merchant
        response = client.post(f"/api/transactions/{transaction_id}/correct", json={
            "field_corrected": "merchant",
            "new_value": "Amazon"
        }, headers=auth_headers)
        
        assert response.status_code == 200
        assert response.json()["old_value"] == "AMAZN INC"
        assert response.json()["new_value"] == "Amazon"
    
    def test_correct_invalid_field(self, client, auth_headers):
        """Test correcting invalid field fails."""
        # Create transaction
        create_response = client.post("/api/transactions/", json={
            "amount": "50.00",
            "date": "2024-12-15"
        }, headers=auth_headers)
        
        transaction_id = create_response.json()["id"]
        
        # Try to correct invalid field
        response = client.post(f"/api/transactions/{transaction_id}/correct", json={
            "field_corrected": "invalid_field",
            "new_value": "test"
        }, headers=auth_headers)
        
        assert response.status_code == 422


class TestTransactionStats:
    """Test transaction statistics."""
    
    def test_get_stats(self, client, auth_headers):
        """Test getting transaction statistics."""
        # Create some transactions
        transactions = [
            {"amount": "50.00", "date": "2024-12-15", "category": "Food"},
            {"amount": "100.00", "date": "2024-12-14", "category": "Food"},
            {"amount": "200.00", "date": "2024-12-13", "category": "Shopping"},
        ]
        
        for txn in transactions:
            client.post("/api/transactions/", json=txn, headers=auth_headers)
        
        # Get stats
        response = client.get("/api/transactions/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["total_transactions"] == 3
        assert data["total_amount"] == "350.00"
        assert "average_amount" in data
        assert "categories" in data
        assert "sources" in data
        
        # Verify category breakdown
        assert data["categories"]["Food"]["count"] == 2
        assert data["categories"]["Shopping"]["count"] == 1


class TestTransactionIntegration:
    """Integration tests for transaction flow."""
    
    def test_complete_transaction_flow(self, client, auth_headers):
        """Test complete transaction lifecycle."""
        # 1. Create transaction
        create_response = client.post("/api/transactions/", json={
            "amount": "99.99",
            "date": "2024-12-15",
            "merchant_raw": "Test Merchant",
            "category": "Test Category",
            "description": "Test transaction"
        }, headers=auth_headers)
        
        assert create_response.status_code == 201
        transaction_id = create_response.json()["id"]
        
        # 2. Read transaction
        get_response = client.get(f"/api/transactions/{transaction_id}", headers=auth_headers)
        assert get_response.status_code == 200
        assert get_response.json()["amount"] == "99.99"
        
        # 3. Update transaction
        update_response = client.patch(f"/api/transactions/{transaction_id}", json={
            "amount": "149.99",
            "category": "Updated Category"
        }, headers=auth_headers)
        assert update_response.status_code == 200
        assert update_response.json()["amount"] == "149.99"
        
        # 4. Correct transaction
        correct_response = client.post(f"/api/transactions/{transaction_id}/correct", json={
            "field_corrected": "category",
            "new_value": "Final Category"
        }, headers=auth_headers)
        assert correct_response.status_code == 200
        
        # 5. Verify in list
        list_response = client.get("/api/transactions/", headers=auth_headers)
        assert list_response.status_code == 200
        assert list_response.json()["total"] >= 1
        
        # 6. Check stats
        stats_response = client.get("/api/transactions/stats", headers=auth_headers)
        assert stats_response.status_code == 200
        
        # 7. Delete transaction
        delete_response = client.delete(f"/api/transactions/{transaction_id}", headers=auth_headers)
        assert delete_response.status_code == 204
        
        # 8. Verify deleted
        verify_response = client.get(f"/api/transactions/{transaction_id}", headers=auth_headers)
        assert verify_response.status_code == 404
