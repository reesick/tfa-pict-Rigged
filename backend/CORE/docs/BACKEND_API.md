# SmartFinance Backend API Documentation

## What's Built ✅

### Core Features
- User Authentication (Register, Login, JWT tokens)
- Transaction Management (CRUD, Stats, Search, Soft Delete)
- Budget Management (CRUD, Alerts, Spending Tracking)
- Merchant Management (CRUD, Fuzzy Search)
- Real-time WebSocket Notifications
- Background Tasks (Celery with 4 priority queues)

### Database Models (9 total)
- User, Transaction, Budget, MerchantMaster
- PortfolioHolding, MerkleBatch, UserCorrection
- Recurrence (subscriptions), Embedding (ML vectors)

### Security
- JWT Authentication
- Password hashing (bcrypt)
- User data isolation
- SQL injection protection

---

## Folder Structure

```
backend/CORE/
├── app/
│   ├── main.py              # FastAPI app entry point
│   ├── database.py          # Database connection & session
│   ├── celery_app.py        # Celery configuration & queues
│   │
│   ├── api/                 # API Route Handlers
│   │   ├── __init__.py
│   │   ├── auth.py          # /api/auth/* endpoints
│   │   ├── transactions.py  # /api/transactions/* endpoints
│   │   ├── budgets.py       # /api/budgets/* endpoints
│   │   ├── merchants.py     # /api/merchants/* endpoints
│   │   └── websocket.py     # WebSocket /ws endpoint
│   │
│   ├── models/              # SQLAlchemy Database Models
│   │   ├── __init__.py      # Exports all models
│   │   ├── user.py          # User model
│   │   ├── transaction.py   # Transaction model
│   │   ├── budget.py        # Budget model
│   │   ├── merchant.py      # MerchantMaster model
│   │   ├── blockchain.py    # MerkleBatch, UserCorrection
│   │   ├── portfolio.py     # PortfolioHolding
│   │   ├── recurrence.py    # Subscription patterns (P2)
│   │   └── embedding.py     # ML vectors (P2)
│   │
│   ├── schemas/             # Pydantic Request/Response Models
│   │   ├── auth.py          # Auth schemas
│   │   ├── transaction.py   # Transaction schemas
│   │   ├── budget.py        # Budget schemas
│   │   └── merchant.py      # Merchant schemas
│   │
│   ├── services/            # Business Logic Layer
│   │   ├── auth.py          # Auth service
│   │   ├── transaction.py   # Transaction service
│   │   ├── budget.py        # Budget service
│   │   └── merchant.py      # Merchant service
│   │
│   ├── tasks/               # Celery Background Tasks
│   │   ├── process_transaction.py  # ML tasks (P2)
│   │   ├── blockchain.py           # Blockchain tasks (P3)
│   │   ├── budgets.py              # Budget alert tasks
│   │   └── notifications.py        # Notification tasks
│   │
│   ├── websocket/           # WebSocket Handlers
│   │   ├── manager.py       # Connection manager
│   │   └── message_types.py # Pydantic message schemas
│   │
│   └── utils/               # Utilities
│       ├── security.py      # Password hashing, JWT
│       └── exceptions.py    # Custom exceptions
│
├── tests/                   # Test Files
├── docs/                    # Documentation
├── alembic/                 # Database migrations
├── requirements.txt         # Python dependencies
└── .env                     # Environment variables
```

---

## How to Run

### 1. Setup Environment
```bash
cd backend/CORE
python -m venv venv
.\venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Set Environment Variables
```bash
# Windows PowerShell
$env:DATABASE_URL = "sqlite:///./smartfinance.db"
$env:JWT_SECRET = "your-secret-key-minimum-32-characters-long"
$env:REDIS_URL = "redis://localhost:6379/0"  # For Celery
```

### 3. Run Database Migrations
```bash
alembic upgrade head
```

### 4. Start Backend Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. API Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

# API Reference

## 1. Authentication

### POST /api/auth/register
Create a new user account.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response (201):**
```json
{
  "id": "uuid-here",
  "email": "user@example.com",
  "full_name": "John Doe",
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### POST /api/auth/login
Login and get access token.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer"
}
```

### GET /api/auth/me
Get current user profile. **Requires Auth.**

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response (200):**
```json
{
  "id": "uuid-here",
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "created_at": "2024-12-18T12:00:00"
}
```

### 🔌 Frontend Connection (Auth)
```javascript
// React Native / JavaScript
const API_URL = 'http://localhost:8000';

// Register
const register = async (email, password, fullName) => {
  const response = await fetch(`${API_URL}/api/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, full_name: fullName })
  });
  const data = await response.json();
  // Store token: AsyncStorage.setItem('token', data.access_token);
  return data;
};

// Login
const login = async (email, password) => {
  const response = await fetch(`${API_URL}/api/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  });
  return await response.json();
};

// Get Profile (with auth)
const getProfile = async (token) => {
  const response = await fetch(`${API_URL}/api/auth/me`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
};
```

---

## 2. Transactions

### GET /api/transactions/
List user's transactions with filters. **Requires Auth.**

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| since | date | Start date (YYYY-MM-DD) |
| until | date | End date |
| category | string | Filter by category |
| source | string | Filter by source (manual, ocr, csv) |
| search | string | Search in merchant/description |
| min_amount | float | Minimum amount |
| max_amount | float | Maximum amount |
| limit | int | Page size (default 50, max 100) |
| offset | int | Pagination offset |

**Response (200):**
```json
{
  "data": [
    {
      "id": "txn-uuid",
      "amount": "25.50",
      "date": "2024-12-18",
      "merchant_raw": "Starbucks Coffee",
      "category": "Food",
      "description": "Morning coffee",
      "source": "manual",
      "is_anchored": false,
      "created_at": "2024-12-18T10:30:00"
    }
  ],
  "total": 42,
  "limit": 50,
  "offset": 0,
  "has_more": false
}
```

### POST /api/transactions/
Create new transaction. **Requires Auth.**

**Request:**
```json
{
  "amount": 25.50,
  "transaction_date": "2024-12-18",
  "merchant_raw": "Starbucks Coffee",
  "category": "Food",
  "description": "Morning coffee",
  "source": "manual"
}
```

**Response (201):** Returns created transaction.

### GET /api/transactions/{id}
Get single transaction. **Requires Auth.**

### PATCH /api/transactions/{id}
Update transaction. **Requires Auth.**

### DELETE /api/transactions/{id}
Soft delete transaction. **Requires Auth.**

### GET /api/transactions/stats
Get spending statistics. **Requires Auth.**

**Response (200):**
```json
{
  "total_transactions": 42,
  "total_amount": "1250.00",
  "average_amount": "29.76",
  "categories": {
    "Food": { "count": 15, "amount": "350.00" },
    "Transport": { "count": 10, "amount": "200.00" }
  },
  "sources": { "manual": 30, "ocr": 12 }
}
```

### POST /api/transactions/{id}/correct
Submit user correction (for ML training). **Requires Auth.**

**Request:**
```json
{
  "field": "category",
  "new_value": "Entertainment",
  "reason": "This was a movie ticket, not food"
}
```

### POST /api/transactions/upload
Upload CSV file for batch import. **Requires Auth.**

### GET /api/transactions/export
Export transactions as CSV or JSON. **Requires Auth.**

### 🔌 Frontend Connection (Transactions)
```javascript
// List transactions with filters
const getTransactions = async (token, filters = {}) => {
  const params = new URLSearchParams(filters);
  const response = await fetch(`${API_URL}/api/transactions/?${params}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
};

// Create transaction
const createTransaction = async (token, transaction) => {
  const response = await fetch(`${API_URL}/api/transactions/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(transaction)
  });
  return await response.json();
};

// Search transactions
const searchTransactions = async (token, query) => {
  const response = await fetch(`${API_URL}/api/transactions/?search=${query}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
};

// Get stats
const getStats = async (token) => {
  const response = await fetch(`${API_URL}/api/transactions/stats`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
};

// Delete transaction
const deleteTransaction = async (token, id) => {
  await fetch(`${API_URL}/api/transactions/${id}`, {
    method: 'DELETE',
    headers: { 'Authorization': `Bearer ${token}` }
  });
};
```

---

## 3. Budgets

### GET /api/budgets/
List user's budgets with spending. **Requires Auth.**

**Response (200):**
```json
{
  "data": [
    {
      "id": "budget-uuid",
      "category": "Food",
      "limit_amount": "500.00",
      "current_spending": "350.00",
      "percentage_used": 70.0,
      "period": "monthly",
      "start_date": "2024-12-01",
      "alert_threshold": 80.0,
      "is_active": true
    }
  ],
  "total": 3
}
```

### POST /api/budgets/
Create new budget. **Requires Auth.**

**Request:**
```json
{
  "category": "Food",
  "limit_amount": 500.00,
  "period": "monthly",
  "start_date": "2024-12-01",
  "alert_threshold": 80.0
}
```

### GET /api/budgets/{id}
Get single budget.

### PATCH /api/budgets/{id}
Update budget.

### DELETE /api/budgets/{id}
Delete budget.

### GET /api/budgets/alerts
Get budgets over threshold. **Requires Auth.**

**Response (200):**
```json
[
  {
    "id": "budget-uuid",
    "category": "Food",
    "limit_amount": "500.00",
    "current_spending": "450.00",
    "percentage_used": 90.0,
    "alert_threshold": 80.0
  }
]
```

### 🔌 Frontend Connection (Budgets)
```javascript
// List budgets
const getBudgets = async (token) => {
  const response = await fetch(`${API_URL}/api/budgets/`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
};

// Create budget
const createBudget = async (token, budget) => {
  const response = await fetch(`${API_URL}/api/budgets/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(budget)
  });
  return await response.json();
};

// Get alerts
const getBudgetAlerts = async (token) => {
  const response = await fetch(`${API_URL}/api/budgets/alerts`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
};
```

---

## 4. Merchants

### GET /api/merchants/search?q={query}
Search merchants by name. **Requires Auth.**

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| q | string | Search query (min 2 chars) |
| limit | int | Max results (default 20) |

**Response (200):**
```json
{
  "data": [
    {
      "id": "merchant-uuid",
      "canonical_name": "Starbucks",
      "category": "Food & Drink",
      "subcategory": "Coffee"
    }
  ],
  "total": 1,
  "query": "starbucks"
}
```

### POST /api/merchants/
Create new merchant.

### GET /api/merchants/{id}
Get merchant by ID.

### 🔌 Frontend Connection (Merchants)
```javascript
// Search merchants for autocomplete
const searchMerchants = async (token, query) => {
  const response = await fetch(`${API_URL}/api/merchants/search?q=${query}`, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
  return await response.json();
};
```

---

## 5. WebSocket (Real-time)

### Connect: ws://localhost:8000/ws?token={jwt_token}

**Connection:**
```javascript
const token = await AsyncStorage.getItem('token');
const ws = new WebSocket(`ws://localhost:8000/ws?token=${token}`);

ws.onopen = () => console.log('Connected');
ws.onclose = () => console.log('Disconnected');
ws.onerror = (error) => console.error('Error:', error);

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  
  switch (message.type) {
    case 'connected':
      console.log('User connected:', message.data.user_id);
      break;
    case 'budget_alert':
      showNotification(`Budget Alert: ${message.data.message}`);
      break;
    case 'transaction_created':
      refreshTransactions();
      break;
    case 'anomaly_detected':
      showAnomalyWarning(message.data);
      break;
    case 'subscription_detected':
      showSubscriptionCard(message.data);
      break;
    case 'blockchain_anchored':
      updateTransactionStatus(message.data.transaction_id);
      break;
  }
};
```

**Message Types:**
| Type | Description |
|------|-------------|
| connected | Connection confirmed |
| budget_alert | Budget threshold exceeded |
| transaction_created | New transaction added |
| anomaly_detected | Unusual transaction (P2) |
| subscription_detected | Recurring payment found (P2) |
| blockchain_anchored | Transaction anchored (P3) |

---

## Error Responses

All endpoints return standard error format:

```json
{
  "detail": "Error message here"
}
```

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad Request |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Validation Error |
| 500 | Server Error |

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_integration.py -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```
