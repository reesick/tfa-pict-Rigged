# Person 2 (ML Engineer) - Complete Integration Guide

## Your Role
You build the AI/ML features: transaction categorization, anomaly detection, subscription pattern detection, and receipt OCR.

---

## Folder Structure (Create These)

```
app/
├── services/
│   └── ml/                     # Create this folder
│       ├── __init__.py
│       ├── categorizer.py      # Transaction auto-categorization
│       ├── anomaly.py          # Anomaly detection model
│       ├── subscription.py     # Subscription pattern detection
│       ├── ocr.py              # Receipt OCR processing
│       └── embeddings.py       # Vector embedding generation
│
├── tasks/
│   ├── process_transaction.py  # ← Modify this file
│   └── ml.py                   # Create for ML-specific tasks
```

---

## Database Tables You Use

### 1. `embeddings` - Store Transaction Vectors
```python
from app.models import Embedding
from app.database import SessionLocal

db = SessionLocal()

# Create embedding for transaction
embedding = Embedding(
    transaction_id="txn-uuid",
    vector=[0.23, -0.45, 0.67, ...],  # Your 384-dim vector
    model_version="sentence-transformers-v1"
)
db.add(embedding)
db.commit()

# Query embeddings
embeddings = db.query(Embedding).filter(
    Embedding.model_version == "sentence-transformers-v1"
).all()
```

**Schema:**
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| transaction_id | UUID | FK to transactions |
| vector | JSON | Vector as list of floats |
| model_version | String | Model identifier |
| created_at | DateTime | Timestamp |

---

### 2. `recurrences` - Store Detected Subscriptions
```python
from app.models import Recurrence
from datetime import date

# Store detected subscription
recurrence = Recurrence(
    user_id="user-uuid",
    merchant_id="merchant-uuid",  # Optional
    amount_mean=15.99,
    amount_std=0.5,
    period_days=30,  # monthly
    next_expected_date=date(2024, 1, 15),
    confidence=0.92,
    status="active"  # active, paused, cancelled
)
db.add(recurrence)
db.commit()
```

**Schema:**
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | FK to users |
| merchant_id | UUID | FK to merchants (optional) |
| amount_mean | Decimal | Average amount |
| amount_std | Decimal | Standard deviation |
| period_days | Integer | Days between occurrences |
| next_expected_date | Date | Predicted next charge |
| confidence | Float | Detection confidence 0-1 |
| status | String | active/paused/cancelled |

---

## Celery Tasks to Implement

### File: `app/tasks/process_transaction.py`

#### 1. `process_new_transaction()` - Main ML Pipeline
```python
@shared_task(bind=True, max_retries=3)
def process_new_transaction(self, transaction_id: str):
    """
    Process new transaction through ML pipeline.
    Called immediately after transaction creation.
    
    Steps:
    1. Fetch transaction from DB
    2. Run merchant extraction (if raw text)
    3. Auto-categorize
    4. Calculate anomaly score
    5. Generate embedding
    6. Update transaction
    7. Send notification if anomaly
    """
    from app.database import SessionLocal
    from app.models import Transaction, Embedding
    from app.websocket.manager import manager
    from app.websocket.message_types import msg_anomaly_detected
    
    db = SessionLocal()
    try:
        # 1. Fetch transaction
        txn = db.query(Transaction).filter(Transaction.id == transaction_id).first()
        if not txn:
            return {"error": "Transaction not found"}
        
        # 2. YOUR ML CODE HERE - Merchant extraction
        # extracted_merchant = your_ocr_model(txn.merchant_raw)
        
        # 3. YOUR ML CODE HERE - Categorization
        # predicted_category = your_categorizer(txn.merchant_raw, txn.amount)
        # txn.category = predicted_category
        
        # 4. YOUR ML CODE HERE - Anomaly detection
        # anomaly_score = your_anomaly_model(txn)
        # txn.anomaly_score = anomaly_score
        
        # 5. YOUR ML CODE HERE - Generate embedding
        # vector = your_embedding_model(txn.merchant_raw + txn.description)
        # embedding = Embedding(transaction_id=txn.id, vector=vector)
        # db.add(embedding)
        
        # 6. Update confidence scores
        # txn.confidence = {"category": 0.95, "merchant": 0.87}
        
        db.commit()
        
        # 7. Send anomaly notification if score > threshold
        if txn.anomaly_score and float(txn.anomaly_score) > 0.7:
            import asyncio
            message = msg_anomaly_detected(
                transaction_id=str(txn.id),
                anomaly_score=float(txn.anomaly_score),
                reason="Unusual spending pattern detected"
            )
            asyncio.run(manager.send_to_user(str(txn.user_id), message))
        
        return {"status": "completed", "transaction_id": transaction_id}
        
    except Exception as e:
        raise self.retry(exc=e)
    finally:
        db.close()
```

#### 2. `detect_subscriptions()` - Nightly Subscription Scan
```python
@shared_task
def detect_subscriptions():
    """
    Detect recurring transactions for all users.
    Runs nightly at 1 AM via Celery Beat.
    """
    from app.database import SessionLocal
    from app.models import User, Transaction, Recurrence
    from app.websocket.manager import manager
    from app.websocket.message_types import msg_subscription_detected
    from sqlalchemy import func
    from datetime import date, timedelta
    
    db = SessionLocal()
    try:
        users = db.query(User).filter(User.is_active == True).all()
        
        for user in users:
            # Get last 90 days of transactions
            since = date.today() - timedelta(days=90)
            txns = db.query(Transaction).filter(
                Transaction.user_id == user.id,
                Transaction.date >= since,
                Transaction.is_deleted == False
            ).all()
            
            # YOUR ML CODE HERE - Pattern detection
            # patterns = detect_recurring_patterns(txns)
            # 
            # for pattern in patterns:
            #     # Check if already exists
            #     existing = db.query(Recurrence).filter(
            #         Recurrence.user_id == user.id,
            #         Recurrence.merchant_id == pattern.merchant_id
            #     ).first()
            #     
            #     if not existing:
            #         recurrence = Recurrence(
            #             user_id=user.id,
            #             merchant_id=pattern.merchant_id,
            #             amount_mean=pattern.avg_amount,
            #             period_days=pattern.period,
            #             next_expected_date=pattern.next_date,
            #             confidence=pattern.confidence
            #         )
            #         db.add(recurrence)
            #         
            #         # Notify user
            #         message = msg_subscription_detected(
            #             merchant=pattern.merchant_name,
            #             amount=pattern.avg_amount,
            #             period_days=pattern.period,
            #             next_date=str(pattern.next_date),
            #             confidence=pattern.confidence
            #         )
            #         asyncio.run(manager.send_to_user(str(user.id), message))
            
            db.commit()
        
        return {"status": "completed"}
    finally:
        db.close()
```

---

## WebSocket Notifications

### Send Anomaly Alert
```python
from app.websocket.manager import manager
from app.websocket.message_types import msg_anomaly_detected
import asyncio

message = msg_anomaly_detected(
    transaction_id="txn-uuid",
    anomaly_score=0.92,
    reason="Amount 5x higher than usual for this merchant"
)

# In async context
await manager.send_to_user(str(user_id), message)

# In sync context (Celery task)
asyncio.run(manager.send_to_user(str(user_id), message))
```

### Send Subscription Detection
```python
from app.websocket.message_types import msg_subscription_detected

message = msg_subscription_detected(
    merchant="Netflix",
    amount=15.99,
    period_days=30,
    next_date="2024-01-15",
    confidence=0.95
)
await manager.send_to_user(str(user_id), message)
```

---

## Celery Queues

| Queue | Use For | Priority |
|-------|---------|----------|
| `high_priority` | OCR, real-time categorization | 10 |
| `default` | Normal ML tasks | 5 |
| `low_priority` | Batch retraining, embeddings | 1 |

```python
from app.celery_app import celery_app

# OCR task - high priority
@celery_app.task(queue='high_priority')
def process_receipt_ocr(image_path: str):
    pass

# Batch embedding generation - low priority
@celery_app.task(queue='low_priority')
def regenerate_all_embeddings():
    pass
```

---

## API Endpoints You Use

### Get User Corrections (for ML training)
```
POST /api/transactions/{id}/correct
```
Users correct your predictions. Use these for model retraining.

**Request:**
```json
{
  "field": "category",
  "new_value": "Entertainment",
  "reason": "This was a movie ticket"
}
```

### Query Corrections for Training
```python
from app.models import UserCorrection

corrections = db.query(UserCorrection).filter(
    UserCorrection.field_corrected == "category"
).all()

# Training data format
training_data = [
    {"input": c.old_value, "output": c.new_value}
    for c in corrections
]
```

### Fuzzy Merchant Matching
```
GET /api/merchants/search?q=starbucks
```
Use for merchant normalization.

---

## Testing Your ML Code

```bash
# Run ML-related tests
pytest tests/test_phase3_budget_websocket.py -v

# Test task imports
python -c "from app.tasks.process_transaction import process_new_transaction, detect_subscriptions; print('OK')"
```
