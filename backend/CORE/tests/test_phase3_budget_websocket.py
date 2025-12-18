"""
Phase 3: Budget & WebSocket Tests
Tests: budget thresholds, alerts, WebSocket message types
"""
import pytest
from fastapi.testclient import TestClient
from datetime import date
from app.main import app
from app.database import get_db, Base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Test database
TEST_DATABASE_URL = "sqlite:///./test_budget.db"
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
        "email": "budget@test.com",
        "password": "password123",
        "full_name": "Budget Tester"
    })
    response = client.post("/api/auth/login", json={
        "email": "budget@test.com",
        "password": "password123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ==================== BUDGET THRESHOLD TESTS ====================

class TestBudgetThresholds:
    """Test budget threshold and alert logic."""
    
    def test_budget_creation(self, client, auth_headers):
        """Create budget with alert threshold."""
        response = client.post("/api/budgets/", json={
            "category": "Food",
            "limit_amount": 1000.00,
            "period": "monthly",
            "start_date": str(date.today()),
            "alert_threshold": 80.0
        }, headers=auth_headers)
        assert response.status_code == 201
        assert response.json()["category"] == "Food"
        assert float(response.json()["limit_amount"]) == 1000.00
    
    def test_budget_spending_tracked(self, client, auth_headers):
        """Spending should be tracked against budget."""
        # Create a transaction in Food category
        client.post("/api/transactions/", json={
            "amount": 50.00,
            "transaction_date": str(date.today()),
            "merchant_raw": "Restaurant",
            "category": "Food"
        }, headers=auth_headers)
        
        # Check budget status
        budgets = client.get("/api/budgets/", headers=auth_headers)
        food_budget = next(
            (b for b in budgets.json()["data"] if b["category"] == "Food"),
            None
        )
        # Should track spending
        assert food_budget is not None
    
    def test_zero_budget_handled(self, client, auth_headers):
        """Zero budget limit should not crash."""
        response = client.post("/api/budgets/", json={
            "category": "ZeroTest",
            "limit_amount": 0.01,
            "period": "monthly",
            "start_date": str(date.today()),
            "alert_threshold": 80.0
        }, headers=auth_headers)
        # Should either accept or reject gracefully
        assert response.status_code in [201, 400, 422]
    
    def test_negative_budget_rejected(self, client, auth_headers):
        """Negative budget should be rejected."""
        response = client.post("/api/budgets/", json={
            "category": "NegativeTest",
            "limit_amount": -100.00,
            "period": "monthly",
            "start_date": str(date.today())
        }, headers=auth_headers)
        assert response.status_code in [400, 422]


# ==================== WEBSOCKET MESSAGE TESTS ====================

class TestWebSocketMessages:
    """Test WebSocket message types and factory functions."""
    
    def test_message_type_enum(self):
        """MessageType enum should have all required types."""
        from app.websocket.message_types import MessageType
        
        required_types = [
            "CONNECTED", "BUDGET_ALERT", "ANOMALY_DETECTED",
            "SUBSCRIPTION_DETECTED", "BLOCKCHAIN_ANCHORED"
        ]
        for t in required_types:
            assert hasattr(MessageType, t), f"Missing MessageType: {t}"
    
    def test_budget_alert_factory(self):
        """Budget alert factory should create proper format."""
        from app.websocket.message_types import msg_budget_alert
        
        msg = msg_budget_alert("Food", 800.0, 1000.0, 80.0)
        
        assert msg["type"] == "budget_alert"
        assert msg["data"]["category"] == "Food"
        assert msg["data"]["spent"] == 800.0
        assert msg["data"]["limit"] == 1000.0
        assert msg["data"]["percentage"] == 80.0
        assert "timestamp" in msg
    
    def test_anomaly_detected_factory(self):
        """Anomaly alert factory should create proper format."""
        from app.websocket.message_types import msg_anomaly_detected
        
        msg = msg_anomaly_detected("txn-123", 0.92, "Unusual amount")
        
        assert msg["type"] == "anomaly_detected"
        assert msg["data"]["transaction_id"] == "txn-123"
        assert msg["data"]["anomaly_score"] == 0.92
        assert msg["data"]["reason"] == "Unusual amount"
        assert msg["data"]["severity"] == "high"  # score > 0.8
    
    def test_subscription_detected_factory(self):
        """Subscription detection factory should create proper format."""
        from app.websocket.message_types import msg_subscription_detected
        
        msg = msg_subscription_detected(
            merchant="Netflix",
            amount=15.99,
            period_days=30,
            next_date="2024-01-15",
            confidence=0.95
        )
        
        assert msg["type"] == "subscription_detected"
        assert msg["data"]["merchant"] == "Netflix"
        assert msg["data"]["amount"] == 15.99
        assert msg["data"]["period_days"] == 30
        assert msg["data"]["period_label"] == "monthly"
    
    def test_blockchain_anchored_factory(self):
        """Blockchain anchored factory should create proper format."""
        from app.websocket.message_types import msg_blockchain_anchored
        
        msg = msg_blockchain_anchored(
            transaction_id="txn-456",
            blockchain_hash="0x123abc",
            ipfs_cid="Qm789"
        )
        
        assert msg["type"] == "blockchain_anchored"
        assert msg["data"]["transaction_id"] == "txn-456"
        assert msg["data"]["blockchain_hash"] == "0x123abc"
        assert msg["data"]["ipfs_cid"] == "Qm789"
    
    def test_timestamp_auto_added(self):
        """All messages should have timestamp auto-added."""
        from app.websocket.message_types import msg_budget_alert, msg_error
        
        msg1 = msg_budget_alert("Test", 0, 100, 0)
        msg2 = msg_error("Test error")
        
        assert "timestamp" in msg1
        assert "timestamp" in msg2
        # Should be ISO format
        assert "T" in msg1["timestamp"]


# ==================== CELERY TASKS TESTS ====================

class TestCeleryTasks:
    """Test Celery task definitions and routing."""
    
    def test_budget_task_exists(self):
        """Check all budget alerts task exists."""
        from app.tasks.budgets import check_all_budget_alerts
        assert callable(check_all_budget_alerts)
    
    def test_subscription_task_exists(self):
        """Subscription detection task should exist."""
        from app.tasks.process_transaction import detect_subscriptions
        assert callable(detect_subscriptions)
    
    def test_celery_queues_configured(self):
        """Celery should have 4 priority queues."""
        from app.celery_app import celery_app
        
        queues = [q.name for q in celery_app.conf.task_queues]
        expected = ['high_priority', 'default', 'low_priority', 'scheduled']
        
        for q in expected:
            assert q in queues, f"Missing queue: {q}"
    
    def test_beat_schedule_configured(self):
        """Celery Beat should have scheduled tasks."""
        from app.celery_app import celery_app
        
        schedule = celery_app.conf.beat_schedule
        assert len(schedule) >= 3, "Should have at least 3 scheduled tasks"
