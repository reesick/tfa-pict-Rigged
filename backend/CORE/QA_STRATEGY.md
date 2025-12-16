# QUALITY ASSURANCE & TESTING STRATEGY
## Production-Ready Code + Rigorous Phase Testing

---

## CORE PRINCIPLES

### 1. No Hollow Code - Every Line Has Purpose
**What "Hollow Code" Looks Like (❌ NOT ACCEPTABLE):**
```python
# Hollow: Just placeholder
def get_transactions():
    pass  # TODO: Implement later

# Hollow: Fake implementation
def calculate_budget():
    return {"status": "success"}  # Doesn't actually calculate
```

**What Production Code Looks Like (✅ MY STANDARD):**
```python
# Complete: Full implementation with error handling
def get_transactions(
    db: Session,
    user_id: UUID,
    since: date = None,
    until: date = None,
    limit: int = 50
) -> List[Transaction]:
    """
    Get user transactions with filters.
    
    Args:
        db: Database session
        user_id: User ID to filter by
        since: Start date (inclusive)
        until: End date (inclusive)
        limit: Max results (capped at 100)
    
    Returns:
        List of Transaction objects
        
    Raises:
        ValidationException: If dates are invalid
    """
    query = db.query(Transaction).filter(Transaction.user_id == user_id)
    
    if since and until and since > until:
        raise ValidationException("start_date must be before end_date")
    
    if since:
        query = query.filter(Transaction.date >= since)
    if until:
        query = query.filter(Transaction.date <= until)
    
    return query.order_by(Transaction.date.desc()).limit(min(limit, 100)).all()
```

---

## PHASE CONNECTION STRATEGY

### Phase 1 → Phase 2 Connection Plan

**Phase 1 Built:**
- `app/database.py` - Database connection
- `app/config.py` - Settings (DATABASE_URL)
- `app/main.py` - FastAPI app

**Phase 2 Connects By:**

#### 1. **Import Chain Test**
```python
# Test that imports work end-to-end
from app.database import Base, get_db  # Phase 1
from app.models import User, Transaction  # Phase 2

# Verify Base is the same instance
assert User.__table__.metadata is Base.metadata
assert Transaction.__table__.metadata is Base.metadata
```

#### 2. **Configuration Flow Test**
```python
# Phase 1 config flows to Phase 2 models
from app.config import get_settings
from app.database import engine

settings = get_settings()
# Verify engine uses config DATABASE_URL
assert settings.database_url in str(engine.url)
```

#### 3. **Alembic Integration Test**
```python
# Phase 2 migration must use Phase 1 Base
from alembic.config import Config
from alembic.script import ScriptDirectory
from app.database import Base

alembic_cfg = Config("alembic.ini")
script_dir = ScriptDirectory.from_config(alembic_cfg)

# Verify Alembic sees all models
from app import models
expected_tables = {
    'users', 'transactions', 'merchant_master', 
    'budgets', 'portfolio_holdings', 
    'merkle_batches', 'user_corrections'
}
actual_tables = set(Base.metadata.tables.keys())
assert expected_tables == actual_tables, f"Missing tables: {expected_tables - actual_tables}"
```

---

### Phase 2 → Phase 3 Connection Plan (Authentication)

**Phase 2 Built:**
- All database models
- Relationships configured
- Database session factory

**Phase 3 Will Connect By:**

#### 1. **Model Usage Test**
```python
# Auth must use Phase 2 User model
from app.models import User
from app.utils.security import hash_password, verify_password

# Test password hashing integrates with User model
hashed = hash_password("test123")
user = User(email="test@example.com", hashed_password=hashed)
assert verify_password("test123", user.hashed_password)
```

#### 2. **Database Transaction Test**
```python
# Auth must use Phase 1 database session
from app.database import SessionLocal
from app.models import User

db = SessionLocal()
try:
    # Create user
    user = User(email="test@example.com", hashed_password="...")
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Verify user has ID (auto-generated UUID)
    assert user.id is not None
    
    # Verify user persisted
    found = db.query(User).filter(User.email == "test@example.com").first()
    assert found is not None
    assert found.id == user.id
finally:
    db.rollback()
    db.close()
```

---

## RIGOROUS TESTING AFTER EACH PHASE

### Phase 1 Testing: Infrastructure

#### Test 1: Configuration Loading
```python
# tests/test_phase1_config.py
import pytest
from app.config import get_settings

def test_settings_load_from_env():
    """Verify settings load from .env file."""
    settings = get_settings()
    assert settings.database_url is not None
    assert "postgresql" in settings.database_url
    assert settings.jwt_secret is not None
    assert len(settings.jwt_secret) >= 32  # Secure length

def test_cors_origins_parsing():
    """Verify CORS origins parse correctly."""
    settings = get_settings()
    origins = settings.cors_origins_list
    assert isinstance(origins, list)
    assert len(origins) > 0
    assert all("http" in origin for origin in origins)
```

#### Test 2: Database Connection
```python
# tests/test_phase1_database.py
from sqlalchemy import text
from app.database import engine, get_db

def test_database_connection():
    """Verify PostgreSQL connection works."""
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1

def test_get_db_dependency():
    """Verify get_db yields working session."""
    db_gen = get_db()
    db = next(db_gen)
    
    try:
        # Execute simple query
        result = db.execute(text("SELECT current_database()"))
        assert result.scalar() == "financedb"
    finally:
        db_gen.close()
```

#### Test 3: FastAPI App
```python
# tests/test_phase1_app.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_root_endpoint():
    """Verify root endpoint responds."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "SmartFinance AI" in data["message"]

def test_health_check():
    """Verify health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"

def test_openapi_docs():
    """Verify OpenAPI docs are accessible."""
    response = client.get("/docs")
    assert response.status_code == 200
```

**Phase 1 Test Command:**
```bash
pytest tests/test_phase1_*.py -v --cov=app --cov-report=term-missing
```

**Expected Output:**
```
tests/test_phase1_config.py::test_settings_load_from_env PASSED
tests/test_phase1_config.py::test_cors_origins_parsing PASSED
tests/test_phase1_database.py::test_database_connection PASSED
tests/test_phase1_database.py::test_get_db_dependency PASSED
tests/test_phase1_app.py::test_root_endpoint PASSED
tests/test_phase1_app.py::test_health_check PASSED
tests/test_phase1_app.py::test_openapi_docs PASSED

Coverage: 85%
```

---

### Phase 2 Testing: Database Models

#### Test 1: Model Creation & Validation
```python
# tests/test_phase2_models.py
import pytest
from decimal import Decimal
from datetime import date, datetime
from app.models import User, Transaction, MerchantMaster, Budget
from app.database import SessionLocal

@pytest.fixture
def db():
    """Provide test database session."""
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()

def test_user_model_creation(db):
    """Test User model with all fields."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_pw_123",
        full_name="Test User",
        phone="+1234567890",
        wallet_addresses=["0x123", "0x456"],
        preferences={"currency": "USD", "theme": "dark"}
    )
    db.add(user)
    db.flush()  # Generate ID without committing
    
    # Verify fields
    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_active is True
    assert user.is_verified is False
    assert len(user.wallet_addresses) == 2
    assert user.preferences["currency"] == "USD"
    assert user.created_at is not None

def test_transaction_model_with_numeric(db):
    """Test Transaction model with exact decimal amounts."""
    user = User(email="user@example.com", hashed_password="hash")
    db.add(user)
    db.flush()
    
    txn = Transaction(
        user_id=user.id,
        amount=Decimal("123.45"),  # Exact decimal
        date=date(2024, 12, 15),
        merchant_raw="SWIGGY BANGALORE",
        category="Food",
        source="sms",
        confidence={"overall": 0.95, "amount": 0.99},
        anomaly_score=0.1
    )
    db.add(txn)
    db.flush()
    
    # Verify exact decimal (no float errors)
    assert txn.amount == Decimal("123.45")
    assert float(txn.amount) == 123.45
    
    # Verify JSONB
    assert txn.confidence["overall"] == 0.95
    
    # Verify relationships
    assert txn.user.email == "user@example.com"
```

#### Test 2: Relationships & Cascades
```python
def test_cascade_delete_user_transactions(db):
    """Test CASCADE delete removes user's transactions."""
    user = User(email="delete@example.com", hashed_password="hash")
    db.add(user)
    db.flush()
    
    # Create 3 transactions
    for i in range(3):
        txn = Transaction(
            user_id=user.id,
            amount=Decimal("10.00"),
            date=date.today(),
            source="manual"
        )
        db.add(txn)
    db.flush()
    
    user_id = user.id
    
    # Count transactions before delete
    count_before = db.query(Transaction).filter(Transaction.user_id == user_id).count()
    assert count_before == 3
    
    # Delete user
    db.delete(user)
    db.flush()
    
    # Verify transactions also deleted (CASCADE)
    count_after = db.query(Transaction).filter(Transaction.user_id == user_id).count()
    assert count_after == 0
```

#### Test 3: Indexes Performance
```python
def test_transaction_user_date_index(db):
    """Test composite index on (user_id, date) for dashboard query."""
    from sqlalchemy import inspect
    
    inspector = inspect(db.bind)
    indexes = inspector.get_indexes("transactions")
    
    # Find idx_txn_user_date
    user_date_idx = next(
        (idx for idx in indexes if idx["name"] == "idx_txn_user_date"),
        None
    )
    
    assert user_date_idx is not None, "idx_txn_user_date index missing"
    assert "user_id" in user_date_idx["column_names"]
    assert "date" in user_date_idx["column_names"]
    
    # Verify index is used in query plan
    from sqlalchemy import text
    user_id = "550e8400-e29b-41d4-a716-446655440000"
    explain = db.execute(text(
        f"EXPLAIN SELECT * FROM transactions WHERE user_id = '{user_id}' ORDER BY date DESC"
    )).fetchall()
    
    explain_text = "\n".join([row[0] for row in explain])
    assert "idx_txn_user_date" in explain_text, "Index not being used"
```

#### Test 4: JSONB & Array Operations
```python
def test_merchant_aliases_gin_index(db):
    """Test GIN index for fast array contains queries."""
    merchant = MerchantMaster(
        canonical_name="Swiggy",
        category="Food & Dining",
        aliases=["SWGY", "Swiggy", "Swiggy Bangalore"]
    )
    db.add(merchant)
    db.flush()
    
    # Test array contains query (uses GIN index)
    found = db.query(MerchantMaster).filter(
        MerchantMaster.aliases.contains(["SWGY"])
    ).first()
    
    assert found is not None
    assert found.canonical_name == "Swiggy"
    
    # Test multiple alias search
    found2 = db.query(MerchantMaster).filter(
        MerchantMaster.aliases.contains(["Swiggy Bangalore"])
    ).first()
    
    assert found2.id == merchant.id
```

#### Test 5: Model Helper Methods
```python
def test_portfolio_profit_loss_calculation(db):
    """Test PortfolioHolding.calculate_profit_loss() method."""
    from app.models import PortfolioHolding
    
    user = User(email="investor@example.com", hashed_password="hash")
    db.add(user)
    db.flush()
    
    holding = PortfolioHolding(
        user_id=user.id,
        asset_type="stock",
        identifier="AAPL",
        units=Decimal("10.0"),
        cost_basis=Decimal("150.00"),  # Bought at $150
        current_price=Decimal("180.00")  # Now at $180
    )
    db.add(holding)
    db.flush()
    
    # Calculate profit/loss
    pl = holding.calculate_profit_loss()
    
    assert pl["total_cost"] == 1500.00  # 10 * 150
    assert pl["current_value"] == 1800.00  # 10 * 180
    assert pl["profit_loss"] == 300.00  # 1800 - 1500
    assert pl["profit_loss_percentage"] == 20.00  # 300/1500 * 100
```

**Phase 2 Test Command:**
```bash
pytest tests/test_phase2_*.py -v --cov=app.models --cov-report=html
```

**Expected Output:**
```
tests/test_phase2_models.py::test_user_model_creation PASSED
tests/test_phase2_models.py::test_transaction_model_with_numeric PASSED
tests/test_phase2_models.py::test_cascade_delete_user_transactions PASSED
tests/test_phase2_models.py::test_transaction_user_date_index PASSED
tests/test_phase2_models.py::test_merchant_aliases_gin_index PASSED
tests/test_phase2_models.py::test_portfolio_profit_loss_calculation PASSED

Coverage (app.models): 92%
```

---

### Phase 3 Testing: Authentication

#### Test 1: Password Security
```python
# tests/test_phase3_auth.py
from app.utils.security import hash_password, verify_password

def test_password_hashing_bcrypt():
    """Test bcrypt hashing is secure."""
    password = "SecurePassword123!"
    hashed = hash_password(password)
    
    # Verify bcrypt format ($2b$...)
    assert hashed.startswith("$2b$")
    
    # Verify password not stored in plain text
    assert password not in hashed
    
    # Verify hash is different each time (salt)
    hashed2 = hash_password(password)
    assert hashed != hashed2
    
    # Verify both verify correctly
    assert verify_password(password, hashed)
    assert verify_password(password, hashed2)

def test_password_verification_timing():
    """Test password verification takes reasonable time (~200ms)."""
    import time
    password = "test123"
    hashed = hash_password(password)
    
    start = time.time()
    verify_password(password, hashed)
    elapsed = time.time() - start
    
    # Should take 150-300ms (bcrypt rounds = 12)
    assert 0.15 < elapsed < 0.5, f"Verification took {elapsed}s (expected 0.15-0.5s)"
```

#### Test 2: JWT Token Security
```python
from app.utils.security import create_access_token, decode_token
import time

def test_jwt_token_creation():
    """Test JWT token structure."""
    token = create_access_token({"sub": "user-123"})
    
    # Verify JWT format (header.payload.signature)
    parts = token.split(".")
    assert len(parts) == 3
    
    # Decode and verify payload
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"
    assert "exp" in payload

def test_jwt_expiration():
    """Test JWT tokens expire."""
    # Create token with 1 second expiry
    from app.config import Settings
    from app.utils import security
    
    old_setting = security.settings.access_token_expire_minutes
    security.settings.access_token_expire_minutes = 0.01  # 0.6 seconds
    
    token = create_access_token({"sub": "user-123"})
    
    # Token valid immediately
    payload = decode_token(token)
    assert payload is not None
    
    # Wait for expiration
    time.sleep(2)
    
    # Token now invalid
    expired_payload = decode_token(token)
    assert expired_payload is None
    
    # Restore setting
    security.settings.access_token_expire_minutes = old_setting
```

#### Test 3: Registration Endpoint
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_register_endpoint_success():
    """Test user registration creates user and returns token."""
    response = client.post("/api/auth/register", json={
        "email": "newuser@example.com",
        "password": "SecurePass123!",
        "full_name": "New User"
    })
    
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    
    # Verify token is valid
    token = data["access_token"]
    from app.utils.security import decode_token
    payload = decode_token(token)
    assert payload is not None
    assert "sub" in payload

def test_register_duplicate_email():
    """Test registration fails for duplicate email."""
    # Register first user
    client.post("/api/auth/register", json={
        "email": "duplicate@example.com",
        "password": "Pass123!",
        "full_name": "First User"
    })
    
    # Try to register again with same email
    response = client.post("/api/auth/register", json={
        "email": "duplicate@example.com",
        "password": "DifferentPass123!",
        "full_name": "Second User"
    })
    
    assert response.status_code == 409  # Conflict
    assert "already registered" in response.json()["detail"].lower()
```

#### Test 4: Login Endpoint
```python
def test_login_endpoint_success():
    """Test login with correct credentials."""
    # Register user first
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
    data = response.json()
    assert "access_token" in data

def test_login_wrong_password():
    """Test login fails with wrong password."""
    # Register user
    client.post("/api/auth/register", json={
        "email": "user@example.com",
        "password": "CorrectPass123!",
        "full_name": "User"
    })
    
    # Try login with wrong password
    response = client.post("/api/auth/login", json={
        "email": "user@example.com",
        "password": "WrongPassword!"
    })
    
    assert response.status_code == 401
    assert "incorrect" in response.json()["detail"].lower()
```

---

## INTEGRATION TESTING

### Cross-Phase Integration Test
```python
# tests/test_integration.py
def test_full_user_journey():
    """
    Test complete user journey across all phases.
    
    Tests:
    - Phase 1: App + Database
    - Phase 2: Models + Relationships
    - Phase 3: Auth
    - Phase 4: Transaction APIs
    """
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # 1. Register user (Phase 3 + Phase 2 + Phase 1)
    response = client.post("/api/auth/register", json={
        "email": "journey@example.com",
        "password": "SecurePass123!",
        "full_name": "Journey User"
    })
    assert response.status_code == 201
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Create transaction (Phase 4 + Phase 2 + Phase 1)
    response = client.post("/api/transactions/", json={
        "amount": 45.50,
        "date": "2024-12-15",
        "merchant_raw": "SWIGGY",
        "category": "Food",
        "source": "manual"
    }, headers=headers)
    assert response.status_code == 201
    transaction = response.json()
    
    # 3. List transactions (Phase 4 + Phase 2 + Phase 1)
    response = client.get("/api/transactions/", headers=headers)
    assert response.status_code == 200
    transactions = response.json()["data"]
    assert len(transactions) == 1
    assert transactions[0]["amount"] == "45.50"
    
    # 4. Create budget (Phase 5 + Phase 2 + Phase 1)
    response = client.post("/api/budgets/", json={
        "category": "Food",
        "amount": 500.00,
        "start_date": "2024-12-01",
        "end_date": "2024-12-31"
    }, headers=headers)
    assert response.status_code == 201
    
    # 5. Check budget (integrates all phases)
    response = client.get("/api/budgets/", headers=headers)
    assert response.status_code == 200
    budgets = response.json()["data"]
    assert budgets[0]["category"] == "Food"
    assert budgets[0]["spent"] == 45.50
    assert budgets[0]["remaining"] == 454.50
```

---

## CONTINUOUS TESTING COMMANDS

### After Each Phase
```bash
# Run phase-specific tests
pytest tests/test_phase{N}_*.py -v

# Run all previous phase tests (regression)
pytest tests/test_phase{1..N}_*.py -v

# Check code coverage
pytest --cov=app --cov-report=html --cov-fail-under=70

# Check integration
pytest tests/test_integration.py -v
```

### Performance Testing
```bash
# Load test with Locust
locust -f tests/load_test.py --headless -u 100 -r 10 -t 1m
```

---

## QUALITY GATES

### Phase Cannot Proceed Unless:

1. ✅ **All unit tests pass** (100% pass rate)
2. ✅ **Code coverage ≥ 70%** (new code)
3. ✅ **No Lint errors** (`ruff check app/`)
4. ✅ **Type checking passes** (`mypy app/`)
5. ✅ **Integration tests pass** (cross-phase)
6. ✅ **Manual smoke test** (curl endpoints)
7. ✅ **Database migrations reversible** (`alembic downgrade -1`)

---

## THIS IS MY COMMITMENT

**Every phase I build will have:**
1. Complete, production-ready implementations
2. Full test coverage demonstrating functionality
3. Integration tests proving connection to previous phases
4. Documentation explaining design decisions
5. Performance verification
6. Security validation

**No hollow code. No shortcuts. Production-grade only.**
