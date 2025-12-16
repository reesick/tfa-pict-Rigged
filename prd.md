# PERSON 1: CORE BACKEND & DATABASE
## COMPREHENSIVE DEVELOPMENT GUIDE

---

## ROLE OVERVIEW

You are the **Foundation Architect** responsible for building the core infrastructure that every other team member depends on. Your work is **critical** - without a solid backend, the entire project cannot function. You'll create the FastAPI application, design the complete database schema, implement authentication, build REST APIs, set up Docker, and establish the foundation for real-time features.

**Work Allocation:** 25% of total project  
**Timeline:** Weeks 1-3 (Foundation), Ongoing (API additions)  
**Dependencies:** None - you start first  
**Blockers for:** Everyone depends on you

---

## TECH STACK

| Technology | Version | Purpose |
|-----------|---------|---------|
| Python | 3.11+ | Programming language |
| FastAPI | 0.104+ | Async web framework |
| PostgreSQL | 15+ | Relational database |
| SQLAlchemy | 2.0+ | ORM for database |
| Alembic | 1.12+ | Database migrations |
| Redis | 7+ | Caching + message broker |
| Celery | 5.3+ | Background task queue |
| Pydantic | 2.0+ | Data validation |
| PyJWT | 2.8+ | JWT authentication |
| bcrypt | 4.1+ | Password hashing |
| python-dotenv | 1.0+ | Environment config |
| pytest | 7.4+ | Testing framework |
| Docker | 24+ | Containerization |

---

## PROJECT STRUCTURE

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Configuration settings
│   ├── database.py             # Database connection
│   │
│   ├── models/                 # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── transaction.py
│   │   ├── merchant.py
│   │   ├── budget.py
│   │   ├── portfolio.py
│   │   └── blockchain.py
│   │
│   ├── schemas/                # Pydantic schemas
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── transaction.py
│   │   ├── auth.py
│   │   └── budget.py
│   │
│   ├── api/                    # API routes
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── transactions.py
│   │   ├── budgets.py
│   │   ├── merchants.py
│   │   └── websocket.py
│   │
│   ├── services/               # Business logic
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── transaction.py
│   │   └── budget.py
│   │
│   ├── utils/                  # Helper functions
│   │   ├── __init__.py
│   │   ├── dependencies.py     # FastAPI dependencies
│   │   ├── security.py         # Password hashing, JWT
│   │   └── exceptions.py       # Custom exceptions
│   │
│   └── workers/                # Celery tasks
│       ├── __init__.py
│       └── celery_app.py
│
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
│
├── tests/                      # Test suite
│   ├── test_auth.py
│   ├── test_transactions.py
│   └── test_api.py
│
├── requirements.txt
├── .env.example
├── alembic.ini
├── docker-compose.yml
└── Dockerfile
```

---

## PHASE 1: PROJECT SETUP (Days 1-2)

### Step 1.1: Initialize Project

```bash
# Create project directory
mkdir backend && cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Create requirements.txt
cat > requirements.txt << EOF
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
psycopg2-binary==2.9.9
redis==5.0.1
celery==5.3.4
pydantic==2.5.0
pydantic-settings==2.1.0
pyjwt==2.8.0
bcrypt==4.1.1
python-dotenv==1.0.0
python-multipart==0.0.6
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
EOF

# Install dependencies
pip install -r requirements.txt
```

### Step 1.2: Create Project Structure

```bash
mkdir -p app/{models,schemas,api,services,utils,workers}
touch app/{__init__,main,config,database}.py
touch app/models/{__init__,user,transaction,merchant,budget,portfolio,blockchain}.py
touch app/schemas/{__init__,user,transaction,auth,budget}.py
touch app/api/{__init__,auth,transactions,budgets,merchants,websocket}.py
touch app/services/{__init__,auth,transaction,budget}.py
touch app/utils/{__init__,dependencies,security,exceptions}.py
touch app/workers/{__init__,celery_app}.py
```

### Step 1.3: Configuration Setup

**Create `app/config.py`:**
```python
from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    # App Settings
    app_name: str = "SmartFinance AI"
    debug: bool = True
    
    # Database
    database_url: str
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # JWT
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 30
    
    # CORS
    cors_origins: list = ["http://localhost:3000", "http://localhost:8081"]
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()
```

**Create `.env.example`:**
```
DATABASE_URL=postgresql://user:password@localhost:5432/financedb
REDIS_URL=redis://localhost:6379/0
JWT_SECRET=your-secret-key-generate-with-openssl-rand-hex-32
JWT_ALGORITHM=HS256
DEBUG=True
```

---

## PHASE 2: DATABASE SETUP (Days 3-5)

### Step 2.1: Database Connection

**Create `app/database.py`:**
```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

# Create engine
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency for routes
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Step 2.2: Database Models

**RESEARCH REQUIRED:** Study PostgreSQL best practices for:
- JSONB indexing (GIN indexes)
- Full-text search (tsvector)
- Array operations (for aliases)
- Composite indexes for common queries

**Create `app/models/user.py`:**
```python
from sqlalchemy import Column, String, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    phone = Column(String(20))
    full_name = Column(String(255))
    
    # Blockchain
    wallet_addresses = Column(JSONB, default=list)  # ["0x123...", "0x456..."]
    
    # User preferences
    preferences = Column(JSONB, default=dict)  # {currency: "USD", theme: "dark"}
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    portfolios = relationship("PortfolioHolding", back_populates="user")
```

**Create `app/models/transaction.py`:**
```python
from sqlalchemy import Column, String, DateTime, Numeric, Date, ForeignKey, Enum, Float, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base
import enum

class TransactionSource(str, enum.Enum):
    OCR = "ocr"
    SMS = "sms"
    CSV = "csv"
    MANUAL = "manual"

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Core transaction data
    amount = Column(Numeric(12, 2), nullable=False)
    date = Column(Date, nullable=False, index=True)
    merchant_raw = Column(Text)  # Raw extracted text
    merchant_id = Column(UUID(as_uuid=True), ForeignKey("merchant_master.id"))
    category = Column(String(100), index=True)
    
    # Metadata
    source = Column(Enum(TransactionSource), nullable=False)
    ingestion_id = Column(UUID(as_uuid=True))  # Link to ingestion record
    
    # AI/ML data
    confidence = Column(JSONB)  # {overall: 0.95, amount: 0.98, merchant: 0.92}
    anomaly_score = Column(Float, default=0.0, index=True)
    
    # Blockchain
    blockchain_hash = Column(String(64))  # SHA-256 hash
    ipfs_cid = Column(String(100))  # Receipt image CID
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="transactions")
    merchant = relationship("MerchantMaster")
    corrections = relationship("UserCorrection", back_populates="transaction")
    
    # Indexes for common queries
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'date'),
        Index('idx_user_category', 'user_id', 'category'),
        Index('idx_anomaly', 'anomaly_score', postgresql_where="anomaly_score > 0.5"),
    )
```

**Create `app/models/merchant.py`:**
```python
from sqlalchemy import Column, String, Index, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid
from app.database import Base

class MerchantMaster(Base):
    __tablename__ = "merchant_master"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    canonical_name = Column(String(255), nullable=False, unique=True)
    category = Column(String(100), nullable=False, index=True)
    country = Column(String(2))  # ISO country code
    
    # For fuzzy matching
    aliases = Column(ARRAY(String), default=list)  # ["SWGY", "Swiggy", "Swiggy Bangalore"]
    
    # Additional metadata
    tags = Column(JSONB, default=dict)  # {type: "restaurant", cuisine: "indian"}
    
    # GIN index for array contains operations
    __table_args__ = (
        Index('idx_merchant_aliases_gin', 'aliases', postgresql_using='gin'),
    )
```

**Create `app/models/budget.py`:**
```python
from sqlalchemy import Column, String, Date, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.database import Base

class Budget(Base):
    __tablename__ = "budgets"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    category = Column(String(100), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="budgets")
    
    __table_args__ = (
        Index('idx_user_category_budget', 'user_id', 'category'),
    )
```

**Create `app/models/portfolio.py`:**
```python
from sqlalchemy import Column, String, Numeric, DateTime, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime
from app.database import Base
import enum

class AssetType(str, enum.Enum):
    STOCK = "stock"
    CRYPTO = "crypto"
    BOND = "bond"
    MUTUAL_FUND = "mutual_fund"

class PortfolioHolding(Base):
    __tablename__ = "portfolio_holdings"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    asset_type = Column(Enum(AssetType), nullable=False)
    identifier = Column(String(100), nullable=False)  # Ticker or contract address
    units = Column(Numeric(20, 8), nullable=False)
    cost_basis = Column(Numeric(12, 2))
    
    last_valuation = Column(Numeric(12, 2))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
```

**Create additional models for:**
- `app/models/blockchain.py` - MerkleBatch, UserCorrection
- Recurrences (subscriptions)
- Embeddings (vector search - can defer to Person 2)

### Step 2.3: Alembic Setup

```bash
# Initialize Alembic
alembic init alembic

# Edit alembic.ini - set sqlalchemy.url or use env variable
```

**Edit `alembic/env.py`:**
```python
from app.config import get_settings
from app.database import Base
from app.models import *  # Import all models

settings = get_settings()
config.set_main_option("sqlalchemy.url", settings.database_url)
target_metadata = Base.metadata
```

**Create initial migration:**
```bash
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

---

## PHASE 3: AUTHENTICATION SYSTEM (Days 6-7)

### Step 3.1: Security Utilities

**RESEARCH REQUIRED:**
- JWT best practices (access + refresh tokens)
- Password hashing benchmarks (bcrypt rounds)
- Token expiration strategies

**Create `app/utils/security.py`:**
```python
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hash password with bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash"""
    return pwd_context.verify(plain, hashed)

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def create_refresh_token(data: dict) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.refresh_token_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)

def decode_token(token: str) -> dict:
    """Decode and validate JWT"""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None
```

### Step 3.2: Authentication Dependencies

**Create `app/utils/dependencies.py`:**
```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.utils.security import decode_token

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Validate JWT and return current user"""
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive user")
    
    return user
```

### Step 3.3: Auth API Endpoints

**Create `app/schemas/auth.py`:**
```python
from pydantic import BaseModel, EmailStr, constr

class UserRegister(BaseModel):
    email: EmailStr
    password: constr(min_length=8)
    full_name: str
    phone: str | None = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    phone: str | None
    is_verified: bool
    
    class Config:
        from_attributes = True
```

**Create `app/api/auth.py`:**
```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserRegister, UserLogin, TokenResponse, UserResponse
from app.utils.security import hash_password, verify_password, create_access_token, create_refresh_token
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    """Register new user"""
    # Check if user exists
    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    user = User(
        email=data.email,
        hashed_password=hash_password(data.password),
        full_name=data.full_name,
        phone=data.phone
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Generate tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {"access_token": access_token, "refresh_token": refresh_token}

@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    """Login user"""
    user = db.query(User).filter(User.email == data.email).first()
    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is inactive")
    
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return {"access_token": access_token, "refresh_token": refresh_token}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user
```

---

## PHASE 4: TRANSACTION APIs (Days 8-10)

### Step 4.1: Transaction Schemas

**Create `app/schemas/transaction.py`:**
```python
from pydantic import BaseModel, UUID4, condecimal
from datetime import date
from typing import Optional

class TransactionBase(BaseModel):
    amount: condecimal(max_digits=12, decimal_places=2)
    date: date
    merchant_raw: str
    category: str
    source: str

class TransactionCreate(TransactionBase):
    pass

class TransactionResponse(TransactionBase):
    id: UUID4
    user_id: UUID4
    merchant_id: UUID4 | None
    confidence: dict | None
    anomaly_score: float
    blockchain_hash: str | None
    ipfs_cid: str | None
    created_at: datetime
    
    class Config:
        from_attributes = True

class TransactionCorrection(BaseModel):
    transaction_id: UUID4
    new_category: str
    reason: str | None = None
```

### Step 4.2: Transaction Endpoints

**Create `app/api/transactions.py`:**
```python
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List
from datetime import date
from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import TransactionResponse, TransactionCorrection
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])

@router.get("/", response_model=List[TransactionResponse])
def list_transactions(
    since: date | None = Query(None),
    until: date | None = Query(None),
    category: str | None = Query(None),
    source: str | None = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List user transactions with filters"""
    query = db.query(Transaction).filter(Transaction.user_id == current_user.id)
    
    if since:
        query = query.filter(Transaction.date >= since)
    if until:
        query = query.filter(Transaction.date <= until)
    if category:
        query = query.filter(Transaction.category == category)
    if source:
        query = query.filter(Transaction.source == source)
    
    query = query.order_by(Transaction.date.desc())
    transactions = query.offset(offset).limit(limit).all()
    
    return transactions

@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get single transaction"""
    txn = db.query(Transaction).filter(
        and_(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id
        )
    ).first()
    
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return txn

@router.post("/correct")
def correct_transaction(
    data: TransactionCorrection,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """User corrects transaction category (for active learning)"""
    txn = db.query(Transaction).filter(
        and_(
            Transaction.id == data.transaction_id,
            Transaction.user_id == current_user.id
        )
    ).first()
    
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Store correction for Person 2's ML training
    old_category = txn.category
    txn.category = data.new_category
    
    # Create correction record (Person 2's table)
    # correction = UserCorrection(...)
    # db.add(correction)
    
    db.commit()
    
    return {"message": "Transaction corrected", "old": old_category, "new": data.new_category}
```

---

## PHASE 5: BUDGET & MERCHANT APIs (Days 11-12)

### Step 5.1: Budget Endpoints

**Create `app/api/budgets.py`:**
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, and_
from typing import List
from datetime import date
from app.database import get_db
from app.models.budget import Budget
from app.models.transaction import Transaction
from app.models.user import User
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/budgets", tags=["Budgets"])

@router.get("/")
def list_budgets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user budgets with current spending"""
    budgets = db.query(Budget).filter(Budget.user_id == current_user.id).all()
    
    result = []
    for budget in budgets:
        # Calculate current spending
        spent = db.query(func.sum(Transaction.amount)).filter(
            and_(
                Transaction.user_id == current_user.id,
                Transaction.category == budget.category,
                Transaction.date >= budget.start_date,
                Transaction.date <= budget.end_date
            )
        ).scalar() or 0
        
        result.append({
            "id": str(budget.id),
            "category": budget.category,
            "amount": float(budget.amount),
            "spent": float(spent),
            "remaining": float(budget.amount - spent),
            "percentage": (spent / budget.amount * 100) if budget.amount > 0 else 0,
            "start_date": budget.start_date,
            "end_date": budget.end_date
        })
    
    return result

@router.post("/")
def create_budget(
    category: str,
    amount: float,
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create or update budget"""
    # Check if budget exists for this category
    existing = db.query(Budget).filter(
        and_(
            Budget.user_id == current_user.id,
            Budget.category == category
        )
    ).first()
    
    if existing:
        existing.amount = amount
        existing.start_date = start_date
        existing.end_date = end_date
        db.commit()
        return {"message": "Budget updated", "id": str(existing.id)}
    
    budget = Budget(
        user_id=current_user.id,
        category=category,
        amount=amount,
        start_date=start_date,
        end_date=end_date
    )
    db.add(budget)
    db.commit()
    
    return {"message": "Budget created", "id": str(budget.id)}
```

### Step 5.2: Merchant Search Endpoint

**Create `app/api/merchants.py`:**
```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.merchant import MerchantMaster

router = APIRouter(prefix="/merchants", tags=["Merchants"])

@router.get("/search")
def search_merchants(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, le=50),
    db: Session = Depends(get_db)
):
    """Fuzzy search merchants by name or alias"""
    # Simple LIKE search (Person 2 will implement fuzzy matching)
    merchants = db.query(MerchantMaster).filter(
        or_(
            MerchantMaster.canonical_name.ilike(f"%{q}%"),
            MerchantMaster.aliases.any(q)
        )
    ).limit(limit).all()
    
    return [{
        "id": str(m.id),
        "name": m.canonical_name,
        "category": m.category,
        "aliases": m.aliases
    } for m in merchants]
```

---

## PHASE 6: WEBSOCKET REAL-TIME UPDATES (Days 13-14)

### Step 6.1: WebSocket Setup

**RESEARCH REQUIRED:**
- FastAPI WebSocket patterns
- Connection management (multiple clients)
- Redis pub/sub for scaling

**Create `app/api/websocket.py`:**
```python
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from typing import Dict
import json
from app.utils.dependencies import get_current_user
from app.models.user import User

router = APIRouter()

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, user_id: str, message: dict):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(json.dumps(message))

manager = ConnectionManager()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    """WebSocket endpoint for real-time updates"""
    # Validate token (simplified - in production use proper auth)
    from app.utils.security import decode_token
    payload = decode_token(token)
    if not payload:
        await websocket.close(code=1008)
        return
    
    user_id = payload.get("sub")
    await manager.connect(user_id, websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            # Handle incoming messages if needed (ping/pong)
            await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(user_id)

# Helper function for Person 2 to push updates
async def notify_transaction_update(user_id: str, transaction_data: dict):
    """Called by Person 2 when transaction is processed"""
    await manager.send_personal_message(user_id, {
        "type": "transaction_update",
        "data": transaction_data
    })
```

---

## PHASE 7: DOCKER & CELERY SETUP (Days 15-16)

### Step 7.1: Docker Compose

**Create `docker-compose.yml`:**
```yaml
version: '3.8'

services:
  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: financeuser
      POSTGRES_PASSWORD: financepass
      POSTGRES_DB: financedb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U financeuser"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  backend:
    build: .
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - .:/app
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://financeuser:financepass@postgres:5432/financedb
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery_worker:
    build: .
    command: celery -A app.workers.celery_app worker --loglevel=info
    volumes:
      - .:/app
    environment:
      - DATABASE_URL=postgresql://financeuser:financepass@postgres:5432/financedb
      - REDIS_URL=redis://redis:6379/0
    depends_on:
      - postgres
      - redis

volumes:
  postgres_data:
  redis_data:
```

**Create `Dockerfile`:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run migrations on startup (production: separate init container)
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

### Step 7.2: Celery Configuration

**Create `app/workers/celery_app.py`:**
```python
from celery import Celery
from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "finance_tasks",
    broker=settings.redis_url,
    backend=settings.redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)

# Import tasks (Person 2 will add OCR tasks here)
# from app.workers import ocr_tasks
```

---

## PHASE 8: MAIN APP SETUP (Days 17-18)

### Step 8.1: FastAPI Application

**Create `app/main.py`:**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import get_settings
from app.api import auth, transactions, budgets, merchants, websocket
from app.database import engine, Base

settings = get_settings()

# Create tables (in production, use Alembic)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    description="AI-Powered Personal Finance Assistant",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(transactions.router)
app.include_router(budgets.router)
app.include_router(merchants.router)
app.include_router(websocket.router)

@app.get("/")
def root():
    return {"message": "SmartFinance AI API", "status": "operational"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "connected"}
```

### Step 8.2: Run Application

```bash
# Start services
docker-compose up -d postgres redis

# Run migrations
alembic upgrade head

# Start FastAPI
uvicorn app.main:app --reload --port 8000

# Start Celery (separate terminal)
celery -A app.workers.celery_app worker --loglevel=info

# Access API docs
# http://localhost:8000/docs
```

---

## PHASE 9: TESTING (Days 19-20)

### Step 9.1: Test Setup

**Create `tests/conftest.py`:**
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Test database
TEST_DATABASE_URL = "postgresql://test:test@localhost:5432/testdb"
engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def test_user(client):
    response = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "testpass123",
        "full_name": "Test User"
    })
    return response.json()
```

### Step 9.2: Test Cases

**Create `tests/test_auth.py`:**
```python
def test_register(client):
    response = client.post("/auth/register", json={
        "email": "newuser@example.com",
        "password": "password123",
        "full_name": "New User"
    })
    assert response.status_code == 201
    assert "access_token" in response.json()

def test_login(client, test_user):
    response = client.post("/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123"
    })
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_get_me(client, test_user):
    token = test_user["access_token"]
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"
```

**Create `tests/test_transactions.py`:**
```python
def test_list_transactions(client, test_user):
    token = test_user["access_token"]
    response = client.get("/transactions/", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

**Run tests:**
```bash
pytest tests/ -v --cov=app
```

---

## DELIVERABLES CHECKLIST

### Database (✓ Complete these)
- [ ] All 8+ table models created
- [ ] Indexes optimized (GIN, composite)
- [ ] Foreign keys with proper cascades
- [ ] Alembic migrations working
- [ ] Seed data script for merchants

### Authentication (✓ Complete these)
- [ ] JWT access + refresh tokens
- [ ] Password hashing (bcrypt)
- [ ] Register endpoint
- [ ] Login endpoint
- [ ] Get current user endpoint
- [ ] Token refresh endpoint

### Transaction APIs (✓ Complete these)
- [ ] List transactions with filters
- [ ] Get single transaction
- [ ] Transaction correction endpoint
- [ ] Pagination working

### Budget APIs (✓ Complete these)
- [ ] List budgets with spending
- [ ] Create/update budget
- [ ] Budget status calculation

### Merchant APIs (✓ Complete these)
- [ ] Merchant search endpoint
- [ ] Admin merchant add endpoint

### Real-Time (✓ Complete these)
- [ ] WebSocket connection setup
- [ ] Connection manager
- [ ] Push notification helper

### Infrastructure (✓ Complete these)
- [ ] Docker Compose with Postgres, Redis
- [ ] Dockerfile for backend
- [ ] Celery worker setup
- [ ] Health check endpoint
- [ ] CORS configuration
- [ ] Environment config

### Testing (✓ Complete these)
- [ ] Test database setup
- [ ] Auth tests (3+ cases)
- [ ] Transaction tests (3+ cases)
- [ ] Budget tests (2+ cases)
- [ ] 70%+ code coverage

---

## INTEGRATION POINTS

### For Person 2 (Ingestion & ML)
**You provide:**
- Database session (`get_db`)
- Transaction model for inserting
- MerchantMaster table for matching
- User model for associating data
- Celery app for OCR tasks

**You receive:**
- Transaction data to store
- Merchant matches to link
- Classification results to save

### For Person 3 (Blockchain)
**You provide:**
- Transaction model with hash/CID fields
- Database write access for blockchain metadata
- MerkleBatch table for anchoring records

**You receive:**
- Blockchain hashes to store
- IPFS CIDs to store
- Anchoring status updates

### For Person 4 (Frontend)
**You provide:**
- OpenAPI docs at `/docs`
- All REST endpoints
- WebSocket for real-time
- JWT authentication flow

**You receive:**
- API requests
- Transaction corrections
- User preferences

---

## RESEARCH TASKS

### Must Research Separately:
1. **PostgreSQL Performance Tuning**
   - GIN index strategies for JSONB
   - Query optimization for date ranges
   - Connection pooling best practices

2. **JWT Security**
   - Token rotation strategies
   - Refresh token security
   - Rate limiting for auth endpoints

3. **WebSocket Scaling**
   - Redis pub/sub for multi-instance
   - Connection state management
   - Reconnection handling

4. **Docker Production**
   - Multi-stage builds
   - Security scanning
   - Secrets management

---

## TIMELINE

| Week | Tasks |
|------|-------|
| Week 1 | Setup, database models, migrations |
| Week 2 | Authentication, transaction APIs |
| Week 3 | Budget/merchant APIs, WebSocket, Docker |
| Ongoing | API additions, testing, optimization |

---

## SUCCESS CRITERIA

✅ All APIs documented in Swagger  
✅ Database schema complete with indexes  
✅ Authentication working with JWT  
✅ Docker stack runs locally  
✅ Tests passing with 70%+ coverage  
✅ Person 2/3/4 can integrate smoothly  
✅ API response time <500ms p95  

**YOU ARE THE FOUNDATION. BUILD IT SOLID.**





# PERSON 2: TRANSACTION INGESTION & AI/ML
## STRATEGIC DEVELOPMENT GUIDE (NO CODE)

---

## YOUR MISSION

Transform messy real-world inputs (receipts, SMS, CSVs) into clean, categorized transactions with 95%+ accuracy. Build the intelligence that makes this app "smart". **35% of total project work - the most complex role.**

---

## WHAT YOU'LL BUILD

1. **OCR Receipt Processor** - Extract amount, date, merchant from photos
2. **SMS/UPI Parser** - Parse bank notifications automatically  
3. **CSV Importer** - Handle various bank statement formats
4. **Rule-Based Matcher** - Fast fuzzy merchant matching
5. **AI Classifier** - DistilBERT model for categorization
6. **Anomaly Detector** - Flag suspicious transactions
7. **Subscription Detector** - Identify recurring charges
8. **Savings Optimizer** - Generate actionable recommendations
9. **Vector Search** - Semantic transaction queries
10. **Investment Calculators** - SIP, Monte Carlo simulations

---

## PHASE 1: OCR PIPELINE (Days 1-7)

### What To Do
Build system that turns receipt photos into structured transaction data

### How To Do It Efficiently

**Step 1: Choose OCR Engine**
- **RESEARCH SEPARATELY:** Compare PaddleOCR vs Tesseract vs Google Vision API
- Decision factors: Accuracy on Indian receipts, speed, cost, offline capability
- **Recommendation:** PaddleOCR (free, 95%+ accuracy, works offline)

**Step 2: Image Preprocessing**
- Resize to 1600px width (PaddleOCR optimal)
- Convert to grayscale
- Apply Gaussian blur (reduce noise)
- Adaptive thresholding for contrast
- Optional: Deskew if receipts tilted
- **Why:** Raw photos have poor quality - preprocessing doubles OCR accuracy

**Step 3: Text Extraction Strategy**
- Run OCR → Get text + confidence scores + bounding boxes
- Store raw text for debugging
- Track per-character confidence
- **Output:** JSON with lines, positions, confidence

**Step 4: Field Parsing Logic**
- **Amount extraction:** Multiple regex patterns (₹, Rs, INR, $, USD) + Total/Amount keywords + generic decimal patterns
- **Date extraction:** Use dateutil library for format flexibility + fallback to today if not found
- **Merchant extraction:** Heuristic - top 3-5 lines with high confidence + prefer ALL CAPS text + prioritize longer strings
- **Confidence scoring:** Weighted average of field confidences

**Step 5: Integration**
- Create Celery background task (don't block API)
- Save temp image to /tmp
- Run OCR in worker
- Create transaction draft in database
- Call Person 3's IPFS upload
- Notify Person 1's WebSocket
- Clean up temp file
- **Why async:** OCR takes 3-5 seconds, don't make user wait

**Step 6: API Endpoint**
- POST /api/ingest/image (accepts multipart file)
- Return ingestion_id immediately
- GET /status/{ingestion_id} for polling
- Handle errors gracefully

**Testing Strategy:**
- Create dataset of 50 receipt images (clean, noisy, tilted, low-light)
- Manually label ground truth
- Measure per-field accuracy
- Target: 90%+ amount, 85%+ date, 80%+ merchant

---

## PHASE 2: SMS PARSER (Days 8-10)

### What To Do
Parse bank SMS/UPI messages into transactions

### How To Do It Efficiently

**Step 1: Template Library**
- **RESEARCH SEPARATELY:** Collect 20+ real SMS samples from HDFC, ICICI, SBI, Axis, Paytm, PhonePe, GPay
- Create regex patterns per bank
- Structure: amount_pattern, merchant_pattern, date_pattern, txn_id_pattern
- Store in JSON config file for easy updates

**Step 2: Bank Detection**
- Check SMS text for bank keywords (hdfc, icici, paytm)
- Match sender ID if available
- Fallback to generic parser

**Step 3: Generic Fallback**
- When template doesn't match, extract what you can
- Always prioritize amount (most reliable field)
- Date defaults to today
- Merchant marked as "Unknown"
- Lower confidence score

**Step 4: Truncated SMS Handling**
- SMS limit is 160 chars - banks split long messages
- Logic: If SMS < 100 chars AND no amount found, check for recent SMS from same sender within 2 min
- Concatenate and re-parse
- **Why:** Improves accuracy from 60% to 90% for truncated messages

**Step 5: Mobile Integration**
- **Android:** Background service monitors incoming SMS
- **iOS:** User manually forwards (iOS limitations)
- Auto-detect bank SMS, show notification
- One-tap confirm/reject

**Efficient Development:**
- Start with 3 major banks (HDFC, ICICI, UPI)
- Add more templates incrementally
- Use regex tester for fast iteration
- Create SMS simulator for testing

---

## PHASE 3: MERCHANT MATCHING (Days 11-13)

### What To Do
Match raw merchant text to canonical names with fuzzy logic

### How To Do It Efficiently

**Step 1: Text Normalization**
- Lowercase everything
- Remove special characters
- Strip common suffixes (Pvt Ltd, Inc, LLC)
- Remove extra whitespace
- **Critical:** This step doubles match rate

**Step 2: Exact Matching (Fast Path)**
- Check if normalized text exists in merchant_master aliases array
- Use PostgreSQL GIN index (instant lookup)
- If found: return merchant_id, category, 98% confidence
- **Why first:** 70% of transactions hit this path, saves AI costs

**Step 3: Fuzzy Matching (Fallback)**
- **RESEARCH SEPARATELY:** RapidFuzz library benchmarks vs FuzzyWuzzy
- Use token_set_ratio algorithm (handles word order)
- Compare against all aliases for all merchants
- Threshold: 85% similarity
- **Optimization:** Pre-filter candidates using first 3 characters

**Step 4: Performance Optimization**
- Cache frequent matches in Redis (TTL 24h)
- Pre-compute n-grams for merchants
- Batch matching where possible
- **Target:** <50ms per match

**Step 5: Confidence Scoring**
- Exact match: 0.95-0.98
- Fuzzy 95%+: 0.90-0.95  
- Fuzzy 85-95%: 0.75-0.90
- Below 85%: Flag for AI classification

**Master Table Maintenance:**
- Seed with 500+ common merchants (manual research)
- Add aliases discovered from user corrections
- Person 1 provides admin API for updates

---

## PHASE 4: AI CLASSIFICATION (Days 14-20)

### What To Do
Train ML model to categorize unknown merchants

### How To Do It Efficiently

**Step 1: Model Selection**
- **RESEARCH SEPARATELY:** DistilBERT vs BERT vs LightGBM hybrid
- **Recommendation:** DistilBERT (6x faster than BERT, 97% accuracy, 66M params)
- Alternative: Sentence-Transformers + LightGBM (even faster inference)

**Step 2: Training Data Collection**
- Bootstrap from Person 1's merchant_master (labeled categories)
- Add user corrections from user_corrections table
- Augment with synthetic data (GPT-generated merchant names)
- **Target:** 10,000+ labeled examples, balanced classes

**Step 3: Feature Engineering**
- Primary: Merchant text (embeddings)
- Secondary: Amount bucket (micro/typical/large), Hour of day, Day of week, Location (if available from SMS)
- **Why:** Context improves accuracy 5-10%

**Step 4: Fine-Tuning Strategy**
- Load pre-trained DistilBERT
- Add classification head (10 categories)
- Train 3 epochs, learning rate 2e-5
- Use class weights for imbalance
- Early stopping on validation loss
- **Total training time:** 2-3 hours on CPU, 15 min on GPU

**Step 5: Inference Optimization**
- Quantize model (FP32 → INT8, 4x faster)
- Batch predictions when possible
- Cache predictions for identical merchants
- **Target:** <100ms per prediction

**Step 6: Active Learning Loop**
- Weekly: Query user_corrections table
- Retrain on 500+ new corrections
- A/B test new model on 10% traffic
- If accuracy improves, promote to production
- **Why:** Continuous improvement without manual labeling

**Step 7: API Design**
- POST /classify (merchant_text, amount, optional context)
- Return: category, confidence, all_probabilities
- Called by Person 1 when rule-based matching fails

---

## PHASE 5: ANOMALY DETECTION (Days 21-23)

### What To Do
Flag suspicious transactions for fraud prevention

### How To Do It Efficiently

**Step 1: Feature Engineering**
- Amount z-score (vs user's category average)
- Merchant novelty (first-time = suspicious)
- Transaction time (3 AM more suspicious than 3 PM)
- Velocity (3 purchases in 10 min = suspicious)
- Location change (if GPS available)
- Typical spending day (Saturday shopping normal, Tuesday unusual)

**Step 2: Model Choice**
- **RESEARCH SEPARATELY:** IsolationForest vs One-Class SVM vs Autoencoder
- **Recommendation:** IsolationForest (no labeled fraud data needed, fast)
- Alternative: LightGBM if you get labeled data

**Step 3: Training Strategy**
- Train on user's historical "normal" transactions
- Assumption: 99% of past transactions are legitimate
- Model learns normal patterns
- **Per-user models:** Each user gets personalized detector

**Step 4: Scoring System**
- Anomaly score 0.0-1.0
- 0.0-0.5: Normal
- 0.5-0.7: Monitor  
- 0.7-0.85: Alert user
- 0.85+: Immediate push notification
- **Adjustable thresholds:** Based on false positive feedback

**Step 5: Alert Integration**
- High score → Person 1's WebSocket → Person 4's push notification
- Notification includes: merchant, amount, time, "Was this you?" buttons
- User feedback updates model

**Testing:**
- Inject synthetic anomalies (large amounts, weird times)
- Measure true positive rate vs false positive rate
- Target: 80% detection, <2% false positives

---

## PHASE 6: SUBSCRIPTION DETECTION (Days 24-25)

### What To Do
Automatically identify recurring charges

### How To Do It Efficiently

**Step 1: Pattern Recognition**
- For each merchant, compute intervals between transactions
- Calculate: median_interval, coefficient_of_variation
- Classification rules:
  - Monthly: 28-32 days, CV < 0.2
  - Quarterly: 88-95 days, CV < 0.2
  - Annual: 360-370 days, CV < 0.25
- Amount variation < 5% (fixed subscriptions) or < 40% (variable like utilities)

**Step 2: Confidence Scoring**
- Need 3+ occurrences minimum
- Tighter intervals = higher confidence
- Consistent amounts = higher confidence
- Formula: confidence = (1 - CV) * min(occurrence_count/5, 1)

**Step 3: Database Schema**
- Store in recurrences table
- Track: merchant_id, amount_mean, period_days, next_expected_date, confidence
- Update on new transaction

**Step 4: Proactive Alerts**
- 3 days before next_expected_date: Send reminder
- Show annual cost (amount * 12 or 4 or 1)
- Provide cancellation deeplinks (Person 4's UI)

**Step 5: Optimization**
- Run nightly job, not real-time
- Only process active users
- Cache results in Redis

---

## PHASE 7: SAVINGS OPTIMIZER (Days 26-28)

### What To Do
Analyze spending, suggest actionable savings

### How To Do It Efficiently

**Step 1: Financial Baseline**
- Detect income: Regular large deposits matching salary patterns
- Fixed expenses: Sum of detected subscriptions + manual rent/loans
- Discretionary: Total - Fixed
- Savings rate: (Income - Total) / Income
- **Target:** Compare to 20% benchmark

**Step 2: Optimization Algorithm**
- **RESEARCH SEPARATELY:** Linear programming vs heuristic approach
- **Recommendation:** Weighted heuristic (simpler, "good enough")
- Calculate gap: target_savings - current_savings
- Allocate reductions across categories proportionally
- Weight by user preferences (food harder to cut than entertainment)

**Step 3: Scenario Generation**
- Conservative: 5-10% reduction spread across all categories
- Moderate: 15-20% reduction focusing on top 3 categories
- Aggressive: 30% reduction in discretionary spending
- Calculate estimated pain score per scenario

**Step 4: Actionable Recommendations**
- Convert percentages to concrete actions
- Instead of "Reduce food 15%", say "Pack lunch 2x/week, saves $40/month"
- Link to resources (meal plans, alternatives)
- **Why:** Specific actions 3x more likely to be followed

**Step 5: Tracking & Feedback**
- Users mark accepted recommendations
- Track if spending actually decreased
- Measure savings realization rate
- Refine recommendations based on success

---

## PHASE 8: INVESTMENT CALCULATORS (Days 29-30)

### What To Do
Build SIP calculator and Monte Carlo simulator

### How To Do It Efficiently

**SIP Calculator:**
- Formula: FV = P * [((1+r)^n - 1) / r] * (1+r)
- Where: P=monthly investment, r=monthly return, n=months
- Real-time updates as user adjusts sliders
- Show: total invested, returns earned, final value
- **Simple math, powerful impact**

**Monte Carlo Simulation:**
- For each asset class: mean_return, volatility (from historical data)
- Run 10,000 simulations:
  - Each month: sample return from normal distribution
  - Compound over investment horizon
  - Store final portfolio value
- Calculate percentiles: 10th (pessimistic), 50th (median), 90th (optimistic)
- Visualize as fan chart showing outcome range
- **Why:** Communicates uncertainty better than single projection

**Optimization:**
- Pre-compute simulations, don't run on every request
- Cache results for common inputs
- Parallelize simulations (embarrassingly parallel)

---

## PHASE 9: VECTOR SEARCH (Days 31-33)

### What To Do
Enable semantic transaction search

### How To Do It Efficiently

**Step 1: Embedding Model**
- **RESEARCH SEPARATELY:** sentence-transformers models comparison
- **Recommendation:** all-MiniLM-L6-v2 (384 dims, fast, good quality)
- Alternative: all-mpnet-base-v2 (better quality, slower)

**Step 2: Embedding Pipeline**
- For each transaction: Concatenate merchant + category + amount_bucket
- Generate embedding (384-dim vector)
- Store in embeddings table
- **Batch process:** 1000 transactions in 10 seconds

**Step 3: Index Building**
- **RESEARCH SEPARATELY:** FAISS vs Pinecone vs Weaviate
- **Recommendation:** FAISS Flat (exact search, < 1M vectors)
- Alternative: FAISS IVF (faster, slight quality loss, > 1M vectors)
- Load index in memory on startup

**Step 4: Query Processing**
- User query: "food with friends last month"
- Embed query → Search index → Get top-k nearest neighbors
- Apply post-filters (date range, category, amount)
- Re-rank by recency
- **Target:** <500ms end-to-end

**Step 5: Hybrid Search**
- Combine vector similarity with keyword matching
- Query classifier: "restaurants July" = keywords, "food with friends" = semantic
- Weighted fusion of both approaches

---

## DELIVERABLES CHECKLIST

### OCR Pipeline
- [ ] Receipt preprocessing (resize, grayscale, threshold)
- [ ] PaddleOCR integration
- [ ] Amount extraction (90%+ accuracy)
- [ ] Date extraction (85%+ accuracy)
- [ ] Merchant extraction
- [ ] Celery task implementation
- [ ] API endpoints (/ingest/image, /status)

### SMS Parser
- [ ] Template library (5+ banks)
- [ ] Bank detection logic
- [ ] Generic fallback parser
- [ ] Truncated message handling
- [ ] API endpoint (/ingest/text)

### CSV Importer
- [ ] Column detection algorithm
- [ ] Date format flexibility
- [ ] Batch processing
- [ ] Error handling
- [ ] API endpoint (/ingest/file)

### Merchant Matching
- [ ] Text normalization
- [ ] Exact matching (GIN index)
- [ ] Fuzzy matching (RapidFuzz)
- [ ] Confidence scoring
- [ ] Redis caching

### AI Classifier
- [ ] DistilBERT model training
- [ ] Feature engineering
- [ ] Inference optimization
- [ ] Active learning loop
- [ ] API endpoint (/classify)

### Anomaly Detector
- [ ] Feature extraction
- [ ] IsolationForest training
- [ ] Per-user models
- [ ] Alert triggering
- [ ] API endpoint (/anomalies)

### Subscription Detector
- [ ] Pattern recognition algorithm
- [ ] Recurrences table population
- [ ] Next charge prediction
- [ ] API endpoint (/subscriptions)

### Savings Optimizer
- [ ] Financial baseline calculation
- [ ] Optimization algorithm
- [ ] Recommendation generation
- [ ] API endpoint (/savings/optimize)

### Investment Tools
- [ ] SIP calculator
- [ ] Monte Carlo simulator
- [ ] API endpoints (/sip/simulate)

### Vector Search
- [ ] Embedding generation
- [ ] FAISS index building
- [ ] Query processing
- [ ] API endpoint (/transactions/search)

---

## INTEGRATION POINTS

**With Person 1 (Backend):**
- **You receive:** Database access, Transaction model, Merchant_master table, Celery setup
- **You provide:** Ingestion APIs, Classification API, ML insights

**With Person 3 (Blockchain):**
- **You receive:** IPFS upload function (for receipt storage)
- **You provide:** Receipt images, Transaction data for hashing

**With Person 4 (Frontend):**
- **You receive:** API requests (receipt uploads, SMS text, CSV files)
- **You provide:** Processing status, Categorized transactions, ML insights

---

## RESEARCH TASKS

### Must Research Separately:

1. **OCR Libraries:** PaddleOCR vs Tesseract vs Cloud APIs
   - Accuracy on Indian receipts
   - Performance benchmarks
   - Offline capability

2. **Fuzzy Matching:** RapidFuzz vs FuzzyWuzzy
   - Speed comparison
   - Algorithm differences (Levenshtein vs token-based)

3. **ML Models:** DistilBERT vs BERT-tiny vs Sentence-Transformers+LightGBM
   - Accuracy vs speed tradeoff
   - Fine-tuning requirements
   - Resource usage

4. **Anomaly Detection:** IsolationForest vs One-Class SVM vs Autoencoder
   - Unsupervised vs supervised
   - False positive rates

5. **Vector Databases:** FAISS vs Pinecone vs Weaviate
   - Exact vs approximate search
   - Scaling characteristics
   - Cost considerations

6. **Bank SMS Formats:** Collect real examples
   - HDFC, ICICI, SBI, Axis, Kotak
   - Paytm, PhonePe, GPay, Amazon Pay
   - Document patterns in shared doc

---

## TIMELINE

| Week | Tasks |
|------|-------|
| Week 1-2 | OCR pipeline, SMS parser, CSV importer |
| Week 3 | Merchant matching, start AI classifier |
| Week 4-5 | AI classifier training, active learning |
| Week 6 | Anomaly detection, subscription detector |
| Week 7 | Savings optimizer, investment calculators |
| Week 8 | Vector search, testing, optimization |

---

## SUCCESS METRICS

**Accuracy:**
- [ ] 95%+ overall categorization accuracy
- [ ] 90%+ OCR field extraction rate
- [ ] 85%+ SMS parsing success rate
- [ ] 90%+ subscription detection accuracy

**Performance:**
- [ ] <100ms AI classification inference
- [ ] <50ms merchant fuzzy matching
- [ ] <500ms semantic search queries
- [ ] <5 second OCR processing

**User Experience:**
- [ ] <5% user correction rate
- [ ] 85%+ auto-categorization (no AI needed)
- [ ] 0% false positive fraud alerts (after tuning)

**YOU ARE THE BRAIN. MAKE IT SMART.**




# PERSON 3: BLOCKCHAIN & WEB3
## STRATEGIC DEVELOPMENT GUIDE (NO CODE)

---

## YOUR MISSION

Build decentralized features that set this app apart: immutable audit trails, IPFS receipt storage, smart contract savings vaults, and DeFi portfolio tracking. **20% of project work - specialized blockchain expertise.**

---

## WHAT YOU'LL BUILD

1. **Smart Contract Audit Trail** - Store Merkle roots on Polygon
2. **IPFS Receipt Storage** - Decentralized, encrypted image storage  
3. **Savings Vault Contract** - Time-locked stablecoin deposits with yield
4. **DeFi Portfolio Tracker** - Multi-chain asset aggregation
5. **Transaction Hashing System** - SHA-256 with Merkle trees
6. **Verification System** - Generate proofs for auditors

---

## PHASE 1: SMART CONTRACT DEVELOPMENT (Days 1-7)

### What To Do
Create two Solidity contracts: AuditContract and SavingsVault

### How To Do It Efficiently

**RESEARCH SEPARATELY:**
- Solidity 0.8.20+ security best practices
- OpenZeppelin contract libraries
- Gas optimization techniques
- Polygon deployment process
- Smart contract audit tools (Slither, Mythril)

**AuditContract Design:**
- **Purpose:** Store Merkle roots of transaction batches
- **Core Function:** `storeRootHash(bytes32 rootHash, uint256 timestamp, uint32 txCount)`
- **Storage:** Mapping or array of RootEntry structs
- **Events:** Emit `BatchAnchored(bytes32 root, uint256 timestamp, uint32 count)`
- **Access Control:** Only backend wallet can call (Ownable pattern)
- **Gas Optimization:** Pack struct fields, use events instead of storage where possible

**SavingsVault Design:**
- **Purpose:** Lock user stablecoins until unlock date
- **Core Functions:**
  - `deposit(address token, uint256 amount, uint256 unlockTimestamp)`
  - `withdraw()` - checks block.timestamp >= user's unlock time
  - `emergencyWithdraw()` - 5% penalty to treasury
- **Storage:** Mapping user → DepositInfo struct (amount, token, unlockTime)
- **Yield Integration (Optional):** Deposit to Aave, withdraw principal+interest
- **Security Patterns:**
  - Checks-Effects-Interactions pattern
  - ReentrancyGuard from OpenZeppelin
  - SafeERC20 for token transfers
  - Time-lock enforcement in modifier

**Development Environment:**
- Use Hardhat or Foundry framework
- Write comprehensive test suite (100% coverage target)
- Test edge cases: zero amounts, past timestamps, reentrancy attacks
- Deploy to Polygon Mumbai testnet first
- Run Slither and Mythril automated scanners
- **Budget time for professional audit before mainnet (~$5K-15K)**

**Gas Optimization Checklist:**
- Use `uint256` instead of smaller uints (EVM word size)
- Pack struct variables efficiently
- Use `calldata` instead of `memory` for read-only arrays
- Minimize storage writes (most expensive operation)
- Batch operations where possible
- Target: <$0.10 per transaction on Polygon

---

## PHASE 2: IPFS INTEGRATION (Days 8-10)

### What To Do
Store encrypted receipt images on IPFS via Pinata

### How To Do It Efficiently

**RESEARCH SEPARATELY:**
- IPFS vs Arweave vs Filecoin (permanence vs cost)
- Pinata vs Web3.Storage vs NFT.Storage
- AES-256 encryption best practices
- Content addressing fundamentals

**Architecture Decision:**
- **Choice:** Pinata (reliable, free tier, HTTP API, good docs)
- **Alternative:** Self-hosted IPFS node (more decentralized, but maintenance)

**Encryption Strategy:**
- **Client-side encryption (Person 4 handles):**
  - Generate random AES-256 key per receipt
  - Encrypt image before upload
  - Store encrypted key in database (encrypted with user's master key)
- **Why client-side:** IPFS is public - encryption ensures privacy

**Upload Flow:**
1. Person 2's OCR worker calls your `upload_to_ipfs(image_path, user_id)`
2. Read image file
3. Encrypt with AES-256 (assume already encrypted from frontend)
4. Upload to Pinata via HTTP API
5. Receive CID (Content Identifier)
6. Return CID to Person 2
7. Person 2 stores CID in transaction table

**Pinata Setup:**
- Create account, get API keys
- Use pinFileToIPFS endpoint
- Add metadata: user_id (hashed), upload_date
- Configure pinning policy (pin for 7 years minimum)

**Retrieval Flow:**
1. Person 4 requests receipt via Person 1's API
2. Person 1 calls your `get_from_ipfs(cid, encryption_key)`
3. Fetch from Pinata gateway: `https://gateway.pinata.cloud/ipfs/{CID}`
4. Decrypt with key
5. Return image bytes
6. Cache in Redis (1 hour TTL) for repeated views

**Error Handling:**
- IPFS node offline: Return placeholder image
- CID not found: Return error, log for investigation
- Timeout: Retry 3 times with exponential backoff

**Cost Management:**
- Pinata free tier: 1GB storage, enough for 5000+ receipts
- Monitor usage via dashboard
- Implement cleanup: Delete receipts >7 years old

---

## PHASE 3: MERKLE TREE & TRANSACTION HASHING (Days 11-13)

### What To Do
Hash transactions and build Merkle trees for efficient verification

### How To Do It Efficiently

**RESEARCH SEPARATELY:**
- Merkle tree construction algorithms
- SHA-256 vs keccak256 (Ethereum native)
- Proof generation optimization
- Binary tree vs Patricia trie

**Transaction Hashing:**
- **Hash Input:** Concatenate: date + amount + merchant + category + transaction_id
- **Algorithm:** SHA-256 (standard, widely supported)
- **Timing:** When transaction finalized (categorized)
- **Storage:** Store hash in transactions.blockchain_hash field

**Merkle Tree Construction:**
- **Trigger:** Nightly cron job (midnight UTC)
- **Process:**
  1. Query all transactions created in past 24h
  2. Extract their hashes
  3. Build binary Merkle tree:
     - Pair hashes, hash together recursively
     - If odd number, duplicate last hash
     - Continue until single root hash
  4. Store tree structure (for proof generation)
- **Library:** Use existing implementation (don't reinvent)
  - Python: `pymerkle` or manual with hashlib
  - JavaScript: `merkletreejs`

**Anchoring to Blockchain:**
- After Merkle root computed:
  1. Create transaction calling `AuditContract.storeRootHash()`
  2. Include: root hash, timestamp, transaction count
  3. Sign with backend wallet
  4. Submit to Polygon
  5. Wait for confirmation
  6. Store blockchain tx ID in `merkle_batches` table
- **Gas management:** Estimate gas, use 1.2x multiplier for safety
- **Error handling:** Retry failed transactions, alert on repeated failures

**Proof Generation:**
- When user requests proof for transaction:
  1. Find which batch contains this transaction
  2. Retrieve tree structure from database
  3. Generate Merkle proof (sibling hashes path to root)
  4. Return: transaction hash, proof array, root hash
- **Verification (user/auditor side):**
  1. Hash transaction data
  2. Use proof to recompute root
  3. Check root matches on-chain value

---

## PHASE 4: DEFI PORTFOLIO INTEGRATION (Days 14-17)

### What To Do
Track user's crypto holdings across multiple chains

### How To Do It Efficiently

**RESEARCH SEPARATELY:**
- The Graph vs Covalent API vs Alchemy
- Multi-chain RPC endpoints
- DeFi protocol integration (Aave, Uniswap, etc.)
- Price oracle options (Chainlink, CoinGecko)

**Architecture Decision:**
- **Primary:** Covalent API (unified API, 100+ chains, free tier)
- **Alternative:** The Graph (more decentralized, protocol-specific subgraphs)

**Data Sources:**
- **Token Balances:** Covalent `/address/{address}/balances_v2/`
- **DeFi Positions:** Covalent `/address/{address}/stacks/{protocol}/`
- **Transaction History:** Covalent `/address/{address}/transactions_v2/`
- **Prices:** CoinGecko API (free, 10-50 req/min)

**Wallet Management:**
- User adds wallet addresses via Person 4's UI
- Store in users.wallet_addresses JSONB array
- Support multiple addresses per user
- Validate address format (0x... for EVM chains)
- **Never request private keys**

**Data Fetching Flow:**
1. Nightly job queries users with wallet addresses
2. For each wallet:
   - Fetch balances (Covalent)
   - Identify DeFi positions (check supported protocols)
   - Fetch current prices (CoinGecko)
   - Calculate USD value
3. Store in portfolio_holdings table:
   - asset_type: 'crypto'
   - identifier: token address or ticker
   - units: balance
   - last_valuation: USD value
4. Cache results (24h)

**Multi-Chain Support:**
- **Priority chains:** Ethereum, Polygon, BSC, Arbitrum, Optimism
- **Implementation:** Loop through chains per address
- **Optimization:** Parallel requests (asyncio or threading)
- **Deduplication:** Same token on multiple chains counted separately

**DeFi Protocols:**
- **Lending:** Aave (supplied, borrowed)
- **DEX:** Uniswap (LP positions)
- **Staking:** Lido, Rocket Pool
- **Query strategy:** Check token holdings for protocol-specific tokens (aTokens, LP tokens)

**API Endpoints:**
- GET /portfolio/defi/{user_id} - Returns aggregated holdings
- POST /portfolio/wallet - Add wallet address
- DELETE /portfolio/wallet/{address} - Remove wallet

**Performance:**
- Batch API calls
- Implement rate limiting (respect API limits)
- Cache aggressively
- Display data freshness timestamp

---

## PHASE 5: WEB3.PY BACKEND INTEGRATION (Days 18-19)

### What To Do
Connect backend Python to blockchain for contract interactions

### How To Do It Efficiently

**Setup:**
- Install web3.py library
- Configure RPC endpoints:
  - **Testnet:** Alchemy Polygon Mumbai (free tier)
  - **Mainnet:** Alchemy Polygon (paid, or Infura)
- Store backend wallet private key in environment variable (NEVER in code)

**Contract Interaction Patterns:**
- Load contract ABI (from Hardhat/Foundry build)
- Create contract instance with web3.eth.contract()
- **Read operations (free):** `contract.functions.functionName().call()`
- **Write operations (costs gas):** 
  - Build transaction
  - Sign with private key
  - Send transaction
  - Wait for receipt

**Transaction Building:**
```
Build tx → Estimate gas → Set gas price → Sign → Send → Wait for confirmation
```

**Gas Price Strategy:**
- **Polygon:** Gas usually <0.01 MATIC (~$0.001)
- Fetch current gas price from network
- Use 1.2x multiplier for faster confirmation
- Monitor: If gas spikes, queue and retry later

**Error Handling:**
- Transaction reverted: Log reason, alert admin
- RPC timeout: Retry with different endpoint
- Nonce conflicts: Implement nonce management
- Gas estimation failed: Use fallback value

**Security:**
- Private key in environment variable or secret manager
- Never log private key
- Use separate wallet for backend (not personal funds)
- Implement spending limits (only fund what's needed)

---

## PHASE 6: TESTING & DEPLOYMENT (Days 20-21)

### What To Do
Comprehensive testing and secure deployment

### How To Do It Efficiently

**Smart Contract Testing:**
- **Unit tests:** Test each function in isolation
- **Integration tests:** Test contract interactions
- **Edge cases:** Zero values, overflows, reentrancy
- **Gas tests:** Measure and optimize
- **Coverage:** Use solidity-coverage (target 100%)

**Automated Security Scanning:**
- **Slither:** Static analysis (run in CI/CD)
- **Mythril:** Symbolic execution
- **Manticore:** Deep analysis (slower)
- Fix all HIGH and MEDIUM findings

**Manual Security Review:**
- Check access control on all functions
- Verify checks-effects-interactions pattern
- Review external calls
- Validate time-lock logic
- Test emergency scenarios

**Testnet Deployment:**
1. Deploy to Polygon Mumbai
2. Verify contracts on PolygonScan
3. Test all functions manually
4. Integration test with backend
5. Share contract addresses with team

**Mainnet Deployment Checklist:**
- [ ] All tests passing
- [ ] Security audit completed (if budget allows)
- [ ] Automated scanners clean
- [ ] Testnet tested for 1+ week
- [ ] Deployment script tested
- [ ] Backend wallet funded (0.1 MATIC for gas)
- [ ] Contract verified on PolygonScan
- [ ] Multi-sig setup for contract ownership (recommended)

**Monitoring:**
- Track contract events (BatchAnchored, Deposits, Withdrawals)
- Monitor gas usage
- Alert on failed transactions
- Dashboard showing anchoring status

---

## DELIVERABLES CHECKLIST

### Smart Contracts
- [ ] AuditContract written and tested
- [ ] SavingsVault written and tested
- [ ] 100% test coverage
- [ ] Slither/Mythril clean
- [ ] Deployed to testnet
- [ ] (Optional) Professional audit

### IPFS Integration
- [ ] Pinata account setup
- [ ] Upload function (accepts image, returns CID)
- [ ] Retrieval function (accepts CID, returns image)
- [ ] Encryption/decryption (coordinate with Person 4)
- [ ] Error handling

### Transaction Hashing
- [ ] Hash generation function
- [ ] Merkle tree builder
- [ ] Nightly anchoring job (Celery task)
- [ ] Proof generation function
- [ ] Blockchain interaction (Web3.py)

### DeFi Portfolio
- [ ] Covalent API integration
- [ ] Multi-chain support (5+ chains)
- [ ] Token balance fetching
- [ ] DeFi position detection
- [ ] Price fetching
- [ ] Database storage
- [ ] API endpoints

### Backend Integration
- [ ] Web3.py setup
- [ ] Contract ABIs loaded
- [ ] RPC endpoint configuration
- [ ] Transaction signing
- [ ] Error handling
- [ ] Gas management

---

## INTEGRATION POINTS

**With Person 1 (Backend):**
- **You receive:** Database access, API framework, Celery setup
- **You provide:** IPFS functions, blockchain metadata fields, DeFi data

**With Person 2 (Ingestion):**
- **You receive:** Receipt images from OCR
- **You provide:** upload_to_ipfs() function, Transaction hashes

**With Person 4 (Frontend):**
- **You receive:** Wallet addresses, deposit requests
- **You provide:** Contract ABIs, Audit proofs, DeFi holdings

---

## RESEARCH TASKS

### Must Research Separately:

1. **Smart Contract Security**
   - Comprehensive audit checklist
   - Common vulnerabilities (reentrancy, overflow, access control)
   - Gas optimization patterns
   - Testing frameworks (Hardhat vs Foundry)

2. **IPFS/Pinata**
   - Pinning strategies
   - Cost analysis
   - Gateway reliability
   - Encryption best practices

3. **DeFi Data Providers**
   - Covalent vs The Graph comparison
   - API rate limits and costs
   - Protocol coverage
   - Data freshness

4. **Multi-Chain Strategy**
   - RPC endpoint providers (Alchemy, Infura, Ankr)
   - Chain-specific considerations
   - Cross-chain transaction tracking

5. **Web3.py Advanced**
   - Nonce management
   - Transaction queuing
   - Gas price strategies
   - Error recovery

---

## TIMELINE

| Week | Tasks |
|------|-------|
| Week 1 | Smart contract development |
| Week 2 | IPFS integration, transaction hashing |
| Week 3 | DeFi portfolio, Web3.py setup |
| Week 4 | Testing, testnet deployment, documentation |

---

## SUCCESS CRITERIA

**Functionality:**
- [ ] 100% of transactions anchored within 24h
- [ ] 100% of receipts retrievable from IPFS
- [ ] Accurate DeFi holdings across 5+ chains
- [ ] Vault deposits/withdrawals working correctly

**Security:**
- [ ] Clean automated security scans
- [ ] No critical vulnerabilities
- [ ] Private keys secure
- [ ] Smart contracts audited (if budget allows)

**Performance:**
- [ ] <$0.10 per anchoring transaction
- [ ] <2s IPFS upload/retrieval
- [ ] <5s DeFi portfolio refresh per wallet

**YOU ARE THE TRUST LAYER. BUILD IT SECURE.**


# PERSON 4: REACT NATIVE FRONTEND
## STRATEGIC DEVELOPMENT GUIDE (NO CODE)

---

## YOUR MISSION

Build the beautiful, intuitive mobile app (iOS + Android) that users interact with daily. Consume all backend APIs, integrate Web3 wallets, create smooth UX. **20% of project work - UI/UX excellence required.**

---

## WHAT YOU'LL BUILD

1. **Authentication Screens** - Login, register, biometric auth
2. **Transaction Dashboard** - List, filter, search, inline correction
3. **Receipt Camera** - Capture, crop, upload with preview
4. **Budget Tracker** - Visual progress, alerts, charts
5. **Investment Planner** - SIP calculator, Monte Carlo viz, portfolio
6. **Wallet Integration** - WalletConnect, DeFi holdings, savings vault
7. **Real-Time Notifications** - WebSocket, push notifications
8. **Offline Mode** - Local database, sync when online

---

## TECH STACK DECISIONS

**RESEARCH SEPARATELY:**
- React Native vs Flutter vs Native (iOS/Android separate)
- Expo vs React Native CLI
- Navigation libraries (React Navigation vs React Native Navigation)
- State management (Zustand vs Redux vs Context API)
- UI libraries (React Native Paper vs NativeBase vs custom)

**Recommendations:**
- **Framework:** React Native CLI (more control than Expo)
- **Navigation:** React Navigation 6 (most popular, good docs)
- **State:** Zustand (lightweight, simple, performant)
- **UI:** React Native Paper + custom Tailwind-like utils
- **Charts:** Victory Native (declarative, flexible)
- **Wallet:** WalletConnect 2.0 + Wagmi equivalent

---

## PHASE 1: PROJECT SETUP & ARCHITECTURE (Days 1-3)

### What To Do
Initialize React Native project with proper architecture

### How To Do It Efficiently

**Project Initialization:**
```
npx react-native init SmartFinanceApp
cd SmartFinanceApp
```

**Folder Structure:**
```
src/
├── screens/        # Screen components
├── components/     # Reusable components
├── navigation/     # Navigation setup
├── store/          # Zustand stores
├── services/       # API calls, storage
├── hooks/          # Custom hooks
├── utils/          # Helper functions
├── constants/      # Colors, sizes, strings
└── types/          # TypeScript types
```

**Essential Dependencies:**
- @react-navigation/native + stack/bottom-tabs
- zustand (state management)
- axios (API calls)
- react-native-paper (UI components)
- react-native-vector-icons
- react-native-biometrics
- @react-native-camera/camera
- react-native-image-crop-picker
- victory-native (charts)
- @walletconnect/react-native
- @react-native-async-storage/async-storage
- react-native-push-notification

**TypeScript Setup:**
- Enable strict mode
- Define interfaces for all API responses
- Create types for navigation routes
- **Why TypeScript:** Catches bugs early, better autocomplete

**Environment Configuration:**
- Create .env for API URLs
- Different configs for dev/staging/prod
- Use react-native-config

---

## PHASE 2: AUTHENTICATION FLOW (Days 4-6)

### What To Do
Build login, register, biometric auth

### How To Do It Efficiently

**Screen Components:**
1. **Welcome Screen** - App logo, "Get Started" button
2. **Login Screen** - Email + password, biometric option, "Forgot password"
3. **Register Screen** - Email, password, name, phone, terms checkbox
4. **OTP Verification** (optional) - 6-digit code input

**API Integration:**
- Call Person 1's POST /auth/register
- Call Person 1's POST /auth/login
- Store JWT tokens in secure storage
- **Token Storage:** react-native-keychain (iOS Keychain, Android Keystore)

**Biometric Authentication:**
- Use react-native-biometrics
- Check if biometric available (Face ID, Touch ID, Fingerprint)
- Store preference "use biometrics" in AsyncStorage
- On app launch: Show biometric prompt if enabled
- On success: Auto-login with stored token
- **Fallback:** PIN entry if biometrics fail

**Session Management:**
- Store access token (1h expiry)
- Store refresh token (30d expiry)
- Axios interceptor: Auto-refresh on 401 errors
- On refresh fail: Force logout

**Navigation Setup:**
- Auth Navigator (stack): Welcome → Login → Register
- App Navigator (bottom tabs): Dashboard, Budgets, Invest, Profile
- Root Navigator: Auth or App based on token existence

**UX Considerations:**
- Loading indicators during API calls
- Error messages with retry options
- Form validation (email format, password strength)
- Remember me checkbox

---

## PHASE 3: TRANSACTION DASHBOARD (Days 7-10)

### What To Do
Core screen showing all transactions with filters

### How To Do It Efficiently

**UI Layout:**
- Header: Date range selector, search icon, filter icon
- List: FlatList with transactions (virtualized for performance)
- Each item: Date, merchant, amount, category badge, receipt thumbnail
- Pull-to-refresh
- Floating action button: "Add Transaction"

**Data Fetching:**
- On mount: Call Person 1's GET /transactions?limit=50
- Implement pagination (load more on scroll end)
- Cache in Zustand store
- **Optimization:** React.memo for transaction items

**Filtering System:**
- Bottom sheet with filter options:
  - Date range picker (This month, Last month, Custom)
  - Category multi-select
  - Amount range slider
  - Source checkboxes (OCR, SMS, CSV, Manual)
- Apply filters → New API call with query params
- Show active filters as removable chips

**Search Functionality:**
- Search bar in header
- Debounced input (300ms)
- Two modes:
  - Simple: Local filter if loaded, else API call with ?q=
  - Semantic: Call Person 2's /transactions/search
- Show search suggestions as user types

**Inline Correction:**
- Tap category badge → Bottom sheet with all categories
- Select new category → Optimistic update
- Call Person 1's POST /transactions/correct
- On error: Revert change, show toast

**Real-Time Updates:**
- WebSocket connection to Person 1's /ws endpoint
- On "transaction_update" event: Insert into list
- Show toast: "New transaction: $XX at Merchant"
- Animate new item entry

**Offline Support:**
- Store recent transactions in SQLite (react-native-sqlite-storage)
- Show cached data when offline
- Display offline indicator
- Queue corrections, sync when online

---

## PHASE 4: RECEIPT CAPTURE (Days 11-12)

### What To Do
Camera interface for receipt photos with OCR preview

### How To Do It Efficiently

**Camera Screen:**
- Use @react-native-camera/camera
- Full-screen camera view
- Capture button (center bottom)
- Flash toggle, gallery button
- **UX:** Show guide frame for receipt alignment

**Image Processing:**
- On capture: Get image URI
- Show preview with crop controls (react-native-image-crop-picker)
- Allow rotation, zoom
- Confirm button

**Upload Flow:**
1. User confirms image
2. Show loading: "Processing receipt..."
3. Upload to Person 2's POST /api/ingest/image
4. Receive ingestion_id
5. Navigate to "Processing" screen
6. Poll Person 2's GET /status/{ingestion_id} every 2 seconds
7. On complete: Show extracted data
8. Allow corrections before saving
9. Navigate to transaction detail

**Edge Cases:**
- Low light: Prompt to enable flash
- Blurry image: Warn, suggest retake
- Upload failure: Save to queue, retry later
- Large images: Compress before upload (react-native-image-resizer)

**Batch Upload:**
- Allow selecting multiple photos from gallery
- Show progress: "2 of 5 uploaded"
- Queue processing
- Notify when all complete

---

## PHASE 5: BUDGET TRACKER (Days 13-15)

### What To Do
Visualize spending vs budgets with alerts

### How To Do It Efficiently

**Budget Overview Screen:**
- List of budget categories (cards)
- Each card shows:
  - Category icon + name
  - Progress bar (animated)
  - $XX spent of $YY budget
  - Percentage (color-coded: green < 80%, yellow 80-100%, red > 100%)
- Tap card: Drill down to transactions in that category

**Budget Creation/Edit:**
- Modal: Select category, enter amount, pick dates
- Suggest amount based on last 3 months average
- Quick presets: "Monthly", "Quarterly", "Yearly"

**Visual Charts:**
- Spending trend line chart (Victory Native)
  - X-axis: Days of month
  - Y-axis: Cumulative spending
  - Reference line: Budget divided by days
- Category breakdown pie chart
  - Interactive: Tap slice to drill down
  - Legend with percentages

**Alerts UI:**
- Notification badge on budgets tab
- Alert section at top of screen
- Each alert: "⚠️ 85% of Food budget used" with action button
- Action: View category, Adjust budget, See recommendations

**Savings Recommendations:**
- Fetch from Person 2's POST /savings/optimize
- Display as cards:
  - "Pack lunch 2x/week → Save $40/month"
  - Accept/Reject buttons
- Track accepted recommendations

**Performance:**
- Use memoization for chart re-renders
- Debounce budget input changes
- Cache chart data

---

## PHASE 6: INVESTMENT PLANNER (Days 16-18)

### What To Do
SIP calculator, Monte Carlo viz, portfolio tracker

### How To Do It Efficiently

**Risk Profile Questionnaire:**
- Multi-step form (10-15 questions)
- Question types: Multiple choice, slider, yes/no
- Progress indicator
- Submit to Person 2's POST /risk-profile
- Display result: Conservative/Balanced/Aggressive with explanation
- Show recommended asset allocation (pie chart)

**SIP Calculator:**
- Input fields:
  - Monthly amount (slider + text input)
  - Expected return (slider, 8-15%)
  - Time period (slider, 1-30 years)
- Real-time calculation as user adjusts
- Display:
  - Large animated number: Final value
  - Breakdown: Invested vs Returns
  - Bar chart: Year-wise growth
- Share button: Generate image to share

**Monte Carlo Simulation:**
- Call Person 2's POST /sip/simulate
- Display fan chart (Victory Native area charts)
- Three lines: Pessimistic (10th), Median (50th), Optimistic (90th)
- Color-coded shaded areas
- Tap-to-explore: Show value at any year

**Portfolio Tracker:**
- Manual entry: Ticker, quantity, cost basis
- OR: Broker API integration (if available)
- Display holdings as cards:
  - Asset name, current value, cost, P/L, % return
- Total portfolio value (large card at top)
- Asset allocation pie chart
- Compare to target allocation

**DeFi Integration:**
- Button: "Connect Wallet"
- Trigger WalletConnect flow
- On connect: Call Person 3's GET /portfolio/defi/{user_id}
- Display crypto holdings alongside traditional
- Show: Token, chain, balance, USD value
- Unified net worth calculation

---

## PHASE 7: WALLET INTEGRATION (Days 19-21)

### What To Do
WalletConnect for Web3 features

### How To Do It Efficiently

**RESEARCH SEPARATELY:**
- WalletConnect 2.0 documentation
- React Native implementation
- Deep linking setup (for wallet apps)
- Transaction signing flow

**WalletConnect Setup:**
- Install @walletconnect/react-native
- Configure with project ID (from WalletConnect Cloud)
- Setup deep linking for iOS/Android

**Connection Flow:**
1. User taps "Connect Wallet"
2. Show modal with QR code OR list of wallets
3. User scans with wallet app (MetaMask, Trust, etc.)
4. Wallet app prompts approval
5. On success: Store session, display address
6. Fetch balance, show in UI

**Address Display:**
- Truncate: 0x1234...5678 (first 6 + last 4 chars)
- Copy button
- Identicon or ENS avatar
- Disconnect option

**Savings Vault UI:**
- Display vault balance (from blockchain)
- Show unlock date with countdown
- Deposit form:
  - Amount input
  - Date picker (unlock date)
  - Token selector (USDC, DAI, USDT)
- Deposit button: Triggers two transactions
  - 1. Token approval
  - 2. Vault deposit
- Show transaction status: Pending, Confirmed, Failed
- Links to PolygonScan

**Audit Trail Viewer:**
- "Verify Transactions" section
- Shows: Last anchored date, # of transactions
- Button: "Generate Proof" for selected transaction
- Call Person 3's GET /audit/proof/{transaction_id}
- Display Merkle proof in modal
- QR code for sharing
- Link to blockchain explorer

**Transaction Signing:**
- Use wallet.signTransaction() or sendTransaction()
- Show clear prompt: "Sign to deposit $XX into vault"
- Handle user rejection gracefully
- Display gas fee estimate

---

## PHASE 8: NOTIFICATIONS & REAL-TIME (Days 22-23)

### What To Do
WebSocket + push notifications

### How To Do It Efficiently

**WebSocket Connection:**
- Connect on app foreground
- Pass JWT token in connection URL
- Reconnect on disconnect (exponential backoff)
- Listen for events:
  - transaction_update
  - budget_alert
  - anomaly_alert
  - subscription_reminder

**Push Notifications:**
- Setup: react-native-push-notification
- Request permission on onboarding
- Store FCM/APNS token on backend
- Handle notification types:
  - Transaction detected: Show amount, merchant
  - Budget alert: Category, percentage used
  - Fraud alert: "Unusual transaction, verify?"
  - Subscription renewal: "Netflix renews tomorrow"

**Notification Actions:**
- iOS/Android notification actions
- Fraud alert: "Yes, it was me" / "Report fraud" buttons
- Tap notification: Deep link to relevant screen

**Notification Settings:**
- Screen: Toggle per event type
- Frequency: Real-time, Daily digest, Weekly
- Quiet hours: Start time, End time
- Critical alerts bypass quiet hours

**In-App Notifications:**
- Toast messages for non-critical events
- Banner for important alerts
- Notification center: List of recent notifications

---

## PHASE 9: OFFLINE MODE & SYNC (Days 24-25)

### What To Do
Local database, queue actions, sync when online

### How To Do It Efficiently

**Local Database:**
- Use react-native-sqlite-storage
- Mirror backend schema (simplified)
- Tables: transactions, budgets, user_profile
- Store last 3 months of data

**Sync Strategy:**
- On app launch (if online): Full sync
- Periodic sync: Every 15 minutes (background task)
- On reconnect: Immediate sync
- Delta sync: Only fetch changes since last sync

**Offline Actions:**
- Queue in SQLite "pending_actions" table
- Action types: transaction_correction, budget_update, new_transaction
- On reconnect: Process queue sequentially
- Handle conflicts: Server wins, notify user

**Offline Indicator:**
- Banner at top: "Offline - changes will sync"
- Icon in header
- Disable features requiring real-time (wallet, portfolio)

**Performance:**
- Index SQLite tables properly
- Batch inserts for sync
- Throttle sync requests

---

## PHASE 10: POLISH & OPTIMIZATION (Days 26-30)

### What To Do
Animations, dark mode, accessibility, performance

### How To Do It Efficiently

**Animations:**
- React Native Animated or Reanimated 2
- Micro-animations:
  - Button press scale
  - List item slide-in
  - Chart transitions
  - Loading skeletons
- Celebration animations (Lottie) for milestones

**Dark Mode:**
- Detect system theme
- Manual toggle in settings
- Two color palettes
- Persist preference
- Smooth transition

**Accessibility:**
- accessibilityLabel on all touchables
- accessibilityHint for complex interactions
- Support screen readers (TalkBack, VoiceOver)
- Minimum touch target: 44x44 points
- Color contrast ratios (WCAG AA)
- Font scaling support

**Performance Optimization:**
- FlatList optimization: getItemLayout, keyExtractor
- Image optimization: Fast Image library, caching
- Reduce re-renders: React.memo, useMemo, useCallback
- Code splitting: Lazy load screens
- Bundle size: Analyze with react-native-bundle-visualizer

**Error Boundaries:**
- Catch JS errors
- Show friendly error screen
- Send error reports to Sentry
- Restart app option

**Splash Screen:**
- Custom branded splash
- Smooth transition to app

**App Icons & Branding:**
- Design app icon
- Generate all sizes (iOS, Android)
- Launch screen

---

## DELIVERABLES CHECKLIST

### Authentication
- [ ] Login/Register screens
- [ ] Biometric authentication
- [ ] Token management
- [ ] Session handling

### Transaction Dashboard
- [ ] List with pagination
- [ ] Filters and search
- [ ] Inline correction
- [ ] Real-time updates
- [ ] Offline support

### Receipt Capture
- [ ] Camera interface
- [ ] Image crop/rotate
- [ ] Upload with progress
- [ ] OCR result display

### Budget Tracker
- [ ] Budget list with progress
- [ ] Charts (trend, pie)
- [ ] Alerts display
- [ ] Recommendations

### Investment Planner
- [ ] Risk questionnaire
- [ ] SIP calculator
- [ ] Monte Carlo visualization
- [ ] Portfolio tracker

### Wallet Integration
- [ ] WalletConnect setup
- [ ] Address display
- [ ] Savings vault UI
- [ ] Transaction signing
- [ ] Audit trail viewer

### Notifications
- [ ] WebSocket connection
- [ ] Push notifications
- [ ] Notification settings
- [ ] In-app alerts

### Polish
- [ ] Dark mode
- [ ] Animations
- [ ] Accessibility
- [ ] Error handling

---

## INTEGRATION POINTS

**With Person 1 (Backend):**
- **You consume:** All REST APIs, WebSocket endpoint
- **You provide:** User interactions, corrections

**With Person 2 (Ingestion/ML):**
- **You consume:** Ingestion APIs, ML endpoints, semantic search
- **You provide:** Receipt images, SMS text, CSV files

**With Person 3 (Blockchain):**
- **You consume:** Contract ABIs, DeFi data, audit proofs
- **You provide:** Wallet addresses, transaction signing

---

## RESEARCH TASKS

### Must Research Separately:

1. **React Native Performance**
   - FlatList optimization techniques
   - Image caching strategies
   - Navigation performance
   - Bundle size reduction

2. **WalletConnect Integration**
   - Complete implementation guide
   - Deep linking setup (iOS/Android)
   - Transaction signing patterns
   - Error handling

3. **Offline-First Architecture**
   - SQLite best practices
   - Sync strategies
   - Conflict resolution
   - Queue management

4. **Native Modules**
   - Biometrics (Face ID, Touch ID)
   - Camera access
   - Push notifications
   - Background tasks

5. **Charts & Visualizations**
   - Victory Native performance
   - Alternatives (react-native-chart-kit, react-native-svg-charts)
   - Animation strategies

---

## TIMELINE

| Week | Tasks |
|------|-------|
| Week 1 | Setup, architecture, authentication |
| Week 2 | Transaction dashboard, receipt capture |
| Week 3 | Budget tracker, charts |
| Week 4 | Investment planner, portfolio |
| Week 5 | Wallet integration, Web3 features |
| Week 6 | Notifications, offline mode |
| Week 7 | Polish, animations, accessibility, testing |

---

## SUCCESS CRITERIA

**Functionality:**
- [ ] All core features working iOS + Android
- [ ] Offline mode functional
- [ ] Real-time updates working
- [ ] Wallet connection stable

**Performance:**
- [ ] <3s app launch time
- [ ] Smooth 60 FPS scrolling
- [ ] <2s screen transitions
- [ ] <100MB app size

**UX:**
- [ ] Intuitive navigation
- [ ] Helpful error messages
- [ ] Accessible to all users
- [ ] Delightful animations

**YOU ARE THE FACE. MAKE IT BEAUTIFUL.**
