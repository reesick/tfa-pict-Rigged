# SmartFinance AI - Backend Core (Person 1)

## Overview
This is the **core backend** for SmartFinance AI, providing the foundational database architecture, authentication, and REST APIs that all other team members depend on.

## Tech Stack
- **Framework**: FastAPI 0.104+
- **Database**: PostgreSQL 15+
- **ORM**: SQLAlchemy 2.0+
- **Caching**: Redis 7+
- **Task Queue**: Celery 5.3+
- **Authentication**: JWT (PyJWT)
- **Validation**: Pydantic 2.5+

## Project Structure
```
backend/CORE/
├── app/
│   ├── models/          # SQLAlchemy database models
│   ├── schemas/         # Pydantic validation schemas
│   ├── api/             # FastAPI route handlers
│   ├── services/        # Business logic layer
│   ├── utils/           # Helper functions
│   ├── workers/         # Celery background tasks
│   ├── config.py        # Application configuration
│   ├── database.py      # Database connection
│   └── main.py          # FastAPI app entry point
├── alembic/             # Database migrations
├── tests/               # Test suite
├── requirements.txt     # Python dependencies
└── .env.example         # Environment configuration example
```

## Setup Instructions

### Prerequisites
- Python 3.11+
- PostgreSQL 15+
- Redis 7+

### Installation

1. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Setup environment**
```bash
cp .env.example .env
# Edit .env with your database credentials and JWT secret
```

4. **Create database**
```bash
# PostgreSQL
createdb financedb
createuser financeuser -P  # Set password

# Or using psql
psql -U postgres
CREATE DATABASE financedb;
CREATE USER financeuser WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE financedb TO financeuser;
```

5. **Run migrations**
```bash
alembic upgrade head
```

6. **Start the server**
```bash
uvicorn app.main:app --reload --port 8000
```

7. **Access API documentation**
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Running Tests
```bash
pytest tests/ -v --cov=app
```

### Starting Celery Worker
```bash
celery -A app.workers.celery_app worker --loglevel=info
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user
- `POST /api/auth/refresh` - Refresh access token
- `GET /api/auth/me` - Get current user profile

### Transactions
- `GET /api/transactions/` - List transactions (with filters)
- `GET /api/transactions/{id}` - Get single transaction
- `POST /api/transactions/` - Create manual transaction
- `PATCH /api/transactions/{id}` - Update transaction
- `DELETE /api/transactions/{id}` - Delete transaction
- `POST /api/transactions/correct` - Submit user correction

### Budgets
- `GET /api/budgets/` - List budgets with current spending
- `POST /api/budgets/` - Create/update budget
- `DELETE /api/budgets/{id}` - Delete budget

### Merchants
- `GET /api/merchants/search` - Search merchants by name
- `GET /api/merchants/{id}` - Get merchant details

### WebSocket
- `WS /api/ws?token={jwt}` - Real-time updates connection

## Database Schema

Key tables:
- `users` - User accounts and authentication
- `transactions` - Financial transactions with ML metadata
- `merchant_master` - Canonical merchant names and aliases
- `budgets` - User budget tracking
- `portfolio_holdings` - Investment holdings
- `merkle_batches` - Blockchain anchoring batches
- `user_corrections` - ML training feedback

## Integration Points

### For Person 2 (ML/Ingestion)
- Database models: `Transaction`, `MerchantMaster`, `UserCorrection`
- Celery app for background tasks
- WebSocket notification helpers

### For Person 3 (Blockchain)
- Models: `Transaction.blockchain_hash`, `MerkleBatch`
- Database session access

### For Person 4 (Frontend)
- Complete REST API
- WebSocket for real-time updates
- JWT authentication flow

## Development

### Creating a new API endpoint
1. Define Pydantic schema in `app/schemas/`
2. Add route handler in `app/api/`
3. Implement business logic in `app/services/`
4. Write tests in `tests/`

### Database migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migration
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Environment Variables

See `.env.example` for all required configuration:
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `JWT_SECRET` - Secret key for JWT tokens (generate with `openssl rand -hex 32`)
- `CORS_ORIGINS` - Allowed frontend origins

## Performance Targets
- API response time: <500ms (p95)
- Throughput: 1000+ requests/second
- Database query time: <50ms average

## License
Proprietary - SmartFinance AI
