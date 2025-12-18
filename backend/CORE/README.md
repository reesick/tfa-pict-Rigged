    # SmartFinance AI - Core Backend

> **Production-Ready FastAPI Backend for AI-Powered Personal Finance**

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         SmartFinance AI Backend                         │
├─────────────────────────────────────────────────────────────────────────┤
│  FastAPI Application (app/main.py)                                      │
│  ├── Auth API (/api/auth) ─────────────── JWT Authentication            │
│  ├── Transactions API (/api/transactions) ─ CRUD + Stats + Corrections  │
│  ├── Budgets API (/api/budgets) ────────── Budget Management + Alerts   │
│  ├── Merchants API (/api/merchants) ────── Merchant Search              │
│  └── WebSocket (/ws) ───────────────────── Real-time Notifications      │
├─────────────────────────────────────────────────────────────────────────┤
│  Service Layer (app/services/)                                          │
│  ├── TransactionService ─ Business logic for transactions              │
│  ├── BudgetService ────── Spending calculations, alerts                 │
│  └── MerchantService ──── Merchant lookup and search                    │
├─────────────────────────────────────────────────────────────────────────┤
│  Celery Tasks (app/tasks/)                                              │
│  ├── process_transaction ─ For Person 2 ML Pipeline                     │
│  ├── notifications ─────── Real-time alerts via WebSocket               │
│  └── blockchain ────────── For Person 3 Anchoring                       │
├─────────────────────────────────────────────────────────────────────────┤
│  Database Models (app/models/) ─────────── SQLAlchemy + PostgreSQL      │
│  ├── User, Transaction, Budget                                          │
│  ├── MerchantMaster, PortfolioHolding                                   │
│  └── MerkleBatch, UserCorrection                                        │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
backend/CORE/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration (env vars)
│   ├── database.py          # SQLAlchemy setup
│   ├── celery_app.py        # Celery configuration
│   │
│   ├── api/                  # API Endpoints
│   │   ├── auth.py          # Authentication (6 routes)
│   │   ├── transactions.py  # Transaction CRUD (7 routes)
│   │   ├── budgets.py       # Budget management (6 routes)
│   │   ├── merchants.py     # Merchant search (3 routes)
│   │   └── websocket.py     # WebSocket (2 routes)
│   │
│   ├── models/               # SQLAlchemy Models
│   │   ├── user.py          # User + custom GUIDType
│   │   ├── transaction.py   # Transaction + source enum
│   │   ├── budget.py        # Budget periods
│   │   ├── merchant.py      # MerchantMaster
│   │   ├── portfolio.py     # PortfolioHolding
│   │   └── blockchain.py    # MerkleBatch, UserCorrection
│   │
│   ├── schemas/              # Pydantic Schemas
│   │   ├── auth.py          # UserRegister, TokenResponse
│   │   ├── transaction.py   # TransactionCreate, Response
│   │   ├── budget.py        # BudgetCreate, BudgetAlert
│   │   └── merchant.py      # MerchantResponse
│   │
│   ├── services/             # Business Logic
│   │   ├── transaction.py   # TransactionService
│   │   ├── budget.py        # BudgetService
│   │   └── merchant.py      # MerchantService
│   │
│   ├── tasks/                # Celery Background Tasks
│   │   ├── process_transaction.py  # ML pipeline tasks
│   │   ├── notifications.py        # Alert tasks
│   │   └── blockchain.py           # Anchoring tasks
│   │
│   ├── utils/
│   │   ├── security.py      # Password hashing, JWT
│   │   ├── dependencies.py  # FastAPI dependencies
│   │   └── exceptions.py    # Custom exceptions
│   │
│   └── websocket/
│       └── manager.py       # ConnectionManager
│
├── tests/                    # Test Suite
│   ├── conftest.py          # Fixtures
│   ├── test_integration.py  # Phase 1-4 tests (31)
│   └── test_phase5_*.py     # Budget/Merchant tests (17)
│
├── alembic/                  # Database Migrations
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+ (or SQLite for testing)
- Redis (for Celery)

### Installation

```bash
# Navigate to project
cd backend/CORE

# Create virtual environment
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Edit .env with your settings
```

### Environment Variables (.env)

```env
# Database
DATABASE_URL=postgresql://financeuser:password@localhost:5432/financedb

# Security
JWT_SECRET=your-super-secret-key-minimum-32-characters
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=30

# Redis (for Celery)
REDIS_URL=redis://localhost:6379/0

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080

# Debug
DEBUG=True
```

### Run Server

```bash
# Development
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Run Tests

```bash
# All tests
pytest tests/ -v

# Specific phase
pytest tests/test_integration.py -v
pytest tests/test_phase5_budgets_merchants.py -v
```

### Run Celery Worker

```bash
# Start worker
celery -A app.celery_app worker --loglevel=info

# Start beat scheduler (for periodic tasks)
celery -A app.celery_app beat --loglevel=info
```

---

## 🔐 Authentication

### JWT Token Flow

```
1. Register/Login → Get access_token + refresh_token
2. Use access_token in header: Authorization: Bearer <token>
3. Token expires → Use refresh_token to get new access_token
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Create new account |
| POST | `/api/auth/login` | Login, get tokens |
| POST | `/api/auth/refresh` | Refresh access token |
| GET | `/api/auth/me` | Get current user profile |
| POST | `/api/auth/change-password` | Change password |
| POST | `/api/auth/logout` | Logout (client-side) |

### Example: Register

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

---

## 💰 Transaction API

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/transactions/` | List with filters |
| GET | `/api/transactions/stats` | Spending statistics |
| GET | `/api/transactions/{id}` | Get single |
| POST | `/api/transactions/` | Create new |
| PATCH | `/api/transactions/{id}` | Update |
| DELETE | `/api/transactions/{id}` | Delete |
| POST | `/api/transactions/{id}/correct` | ML correction |

### Query Parameters (List)

| Param | Type | Description |
|-------|------|-------------|
| `since` | date | Start date (YYYY-MM-DD) |
| `until` | date | End date |
| `category` | string | Filter by category |
| `source` | string | ocr, sms, csv, manual, blockchain |
| `min_amount` | float | Minimum amount |
| `max_amount` | float | Maximum amount |
| `limit` | int | Page size (default 50) |
| `offset` | int | Pagination offset |

### Example: Create Transaction

```bash
curl -X POST http://localhost:8000/api/transactions/ \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 45.99,
    "transaction_date": "2024-01-15",
    "category": "Food",
    "merchant_raw": "STARBUCKS #12345",
    "source": "manual"
  }'
```

---

## 📊 Budget API

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/budgets/` | List all budgets |
| GET | `/api/budgets/alerts` | Get over-threshold |
| GET | `/api/budgets/{id}` | Get with spending |
| POST | `/api/budgets/` | Create budget |
| PATCH | `/api/budgets/{id}` | Update |
| DELETE | `/api/budgets/{id}` | Delete |

### Budget Response (includes spending)

```json
{
  "id": "uuid",
  "category": "Food",
  "limit_amount": "500.00",
  "period": "monthly",
  "start_date": "2024-01-01",
  "alert_threshold": 80.0,
  "current_spending": "350.00",
  "percentage_used": 70.0,
  "is_over_limit": false
}
```

---

## 🏪 Merchant API

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/merchants/search?q=star` | Search by name |
| GET | `/api/merchants/{id}` | Get by ID |
| POST | `/api/merchants/` | Create (admin) |

---

## 🔌 WebSocket API

### Connect

```javascript
const ws = new WebSocket('ws://localhost:8000/ws?token=<jwt_token>');

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log(message.type, message.data);
};
```

### Message Types

| Type | Description |
|------|-------------|
| `connected` | Connection confirmed |
| `budget_alert` | Budget threshold exceeded |
| `new_transaction` | New transaction added |
| `anomaly_detected` | Unusual transaction |
| `blockchain_anchored` | Merkle batch confirmed |

### Status Endpoint

```
GET /ws/status
→ {"total_connections": 5, "connected_users": 3}
```

---

## 🗄️ Database Models

### User
```python
id: UUID (PK)
email: str (unique)
hashed_password: str
full_name: str
phone: str
wallet_addresses: JSON[]
preferences: JSON
is_active: bool
is_verified: bool
created_at, updated_at: datetime
```

### Transaction
```python
id: UUID (PK)
user_id: UUID (FK → users)
amount: Decimal(12,2)
date: Date
merchant_raw: str
merchant_id: UUID (FK → merchant_master)
category: str
description: str
source: enum (ocr|sms|csv|manual|blockchain)
confidence: JSON {amount: 0.95, category: 0.87}
anomaly_score: Decimal(5,4)
blockchain_hash: str
ipfs_cid: str
is_anchored: bool
```

### Budget
```python
id: UUID (PK)
user_id: UUID (FK)
category: str
limit_amount: Decimal
period: enum (daily|weekly|monthly|yearly)
start_date, end_date: Date
alert_threshold: Decimal (default 80%)
is_active: bool
```

### MerchantMaster
```python
id: UUID (PK)
canonical_name: str (unique)
category: str
subcategory: str
aliases: JSON[]
logo_url: str
```

---

## ⚙️ Celery Tasks

### For Person 2 (ML Integration)

```python
from app.tasks.process_transaction import process_new_transaction

# Queue transaction for ML processing
process_new_transaction.delay(transaction_id)
```

### For Person 3 (Blockchain)

```python
from app.tasks.blockchain import anchor_transaction_batch

# Anchor batch to blockchain
anchor_transaction_batch.delay(
    batch_id="batch-123",
    merkle_root="0x1234...",
    transaction_ids=["txn-1", "txn-2"]
)
```

### Periodic Tasks (Celery Beat)

| Task | Schedule |
|------|----------|
| `check_all_budget_alerts` | Every hour |
| `process_pending_batches` | Every 5 min |

---

## 🧪 Testing

```bash
# Run all tests (48+ tests)
pytest tests/ -v

# With coverage
pytest tests/ --cov=app --cov-report=html

# Specific test class
pytest tests/test_integration.py::TestPhase3Authentication -v
```

### Test Structure
- `conftest.py` - Fixtures (db, client, auth)
- `test_integration.py` - Phase 1-4 (31 tests)
- `test_phase5_*.py` - Budget/Merchant (17 tests)

---

## 📡 API Documentation

When server is running:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## 🔧 Configuration

### config.py Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `app_name` | SmartFinance AI | App title |
| `debug` | False | Debug mode |
| `database_url` | - | PostgreSQL connection |
| `jwt_secret` | - | JWT signing key (32+ chars) |
| `jwt_algorithm` | HS256 | JWT algorithm |
| `access_token_expire_minutes` | 60 | Token TTL |
| `refresh_token_expire_days` | 30 | Refresh TTL |
| `cors_origins` | - | Allowed origins |
| `redis_url` | localhost:6379 | Celery broker |

---

## 🚢 Production Deployment

```bash
# Use production ASGI server
pip install gunicorn uvloop httptools

# Run with Gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000

# With Docker (example)
docker build -t smartfinance-backend .
docker run -p 8000:8000 --env-file .env smartfinance-backend
```

---

## 📈 Route Summary

| API | Routes | Auth Required |
|-----|--------|---------------|
| Auth | 6 | No (except /me) |
| Transactions | 7 | Yes |
| Budgets | 6 | Yes |
| Merchants | 3 | Yes |
| WebSocket | 2 | Token in query |
| Health | 2 | No |
| **Total** | **30** | - |

---

## 🤝 Integration Points

### Person 2 (ML/AI)
- Use `TransactionService` for data access
- Call `process_new_transaction.delay()` for ML pipeline
- Update `confidence` and `anomaly_score` fields

### Person 3 (Blockchain)
- Use `MerkleBatch` model for batch tracking
- Call `anchor_transaction_batch.delay()` for anchoring
- Update `blockchain_hash`, `ipfs_cid`, `is_anchored`

### Person 4 (Frontend)
- All endpoints documented in Swagger UI
- WebSocket for real-time updates
- JWT token in Authorization header

---

*Built with FastAPI, SQLAlchemy, Pydantic, Celery*
