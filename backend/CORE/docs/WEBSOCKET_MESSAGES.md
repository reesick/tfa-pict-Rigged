# WebSocket Message Standards

All WebSocket messages follow a standard format for Person 2/3/4 integration.

## Base Format

```json
{
  "type": "message_type",
  "data": { ... },
  "timestamp": "2025-12-18T12:00:00.000000"
}
```

---

## Connection

### Connect
```
ws://localhost:8000/ws?token=<JWT_TOKEN>
```

### Connected Response
```json
{
  "type": "connected",
  "data": {"message": "WebSocket connected", "user_id": "uuid"},
  "timestamp": "2025-12-18T12:00:00.000000"
}
```

---

## Message Types

| Type | Description | Sender |
|------|-------------|--------|
| `connected` | Connection confirmed | Backend |
| `budget_alert` | Budget threshold exceeded | Backend |
| `transaction_created` | New transaction | Backend |
| `transaction_updated` | Transaction modified | Backend |
| `anomaly_detected` | Unusual transaction | Person 2 |
| `subscription_detected` | Recurring payment found | Person 2 |
| `blockchain_anchored` | Transaction anchored | Person 3 |

---

## Message Examples

### Budget Alert
```json
{
  "type": "budget_alert",
  "data": {
    "category": "Food",
    "spent": 850.00,
    "limit": 1000.00,
    "percentage": 85.0,
    "message": "You've spent 85.0% of your Food budget"
  },
  "timestamp": "2025-12-18T12:00:00.000000"
}
```

### Anomaly Detected (Person 2)
```json
{
  "type": "anomaly_detected",
  "data": {
    "transaction_id": "uuid-here",
    "anomaly_score": 0.92,
    "reason": "Unusual spending amount",
    "severity": "high"
  },
  "timestamp": "2025-12-18T12:00:00.000000"
}
```

### Subscription Detected (Person 2)
```json
{
  "type": "subscription_detected",
  "data": {
    "merchant": "Netflix",
    "amount": 15.99,
    "period_days": 30,
    "period_label": "monthly",
    "next_expected_date": "2024-01-15",
    "confidence": 0.95,
    "message": "Detected monthly subscription: Netflix - $15.99"
  },
  "timestamp": "2025-12-18T12:00:00.000000"
}
```

### Blockchain Anchored (Person 3)
```json
{
  "type": "blockchain_anchored",
  "data": {
    "transaction_id": "uuid-here",
    "blockchain_hash": "0x123abc...",
    "ipfs_cid": "Qm123...",
    "message": "Transaction anchored to blockchain"
  },
  "timestamp": "2025-12-18T12:00:00.000000"
}
```

---

## Usage Examples

### Person 2 (ML Engineer)
```python
from app.websocket.manager import manager
from app.websocket.message_types import msg_anomaly_detected, msg_subscription_detected

# Send anomaly alert
message = msg_anomaly_detected(
    transaction_id="txn-uuid",
    anomaly_score=0.92,
    reason="Unusual amount for this merchant"
)
await manager.send_to_user(str(user_id), message)

# Send subscription detection
message = msg_subscription_detected(
    merchant="Netflix",
    amount=15.99,
    period_days=30,
    next_date="2024-01-15",
    confidence=0.95
)
await manager.send_to_user(str(user_id), message)
```

### Person 3 (Blockchain Engineer)
```python
from app.websocket.manager import manager
from app.websocket.message_types import msg_blockchain_anchored

# Send anchoring confirmation
message = msg_blockchain_anchored(
    transaction_id="txn-uuid",
    blockchain_hash="0x123abc...",
    ipfs_cid="Qm123..."
)
await manager.send_to_user(str(user_id), message)
```

### Person 4 (Frontend)
```javascript
const ws = new WebSocket('ws://localhost:8000/ws?token=' + accessToken);

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  
  switch(msg.type) {
    case 'connected':
      console.log('Connected:', msg.data.user_id);
      break;
      
    case 'budget_alert':
      showBudgetNotification(msg.data);
      break;
      
    case 'anomaly_detected':
      showAnomalyWarning(msg.data);
      break;
      
    case 'subscription_detected':
      showSubscriptionCard(msg.data);
      break;
      
    case 'blockchain_anchored':
      updateTransactionStatus(msg.data.transaction_id, 'anchored');
      break;
  }
};
```

---

## Available Message Factories

Import from `app/websocket/message_types.py`:

| Function | Description |
|----------|-------------|
| `msg_connected(user_id)` | Connection confirmation |
| `msg_budget_alert(category, spent, limit, percentage)` | Budget warning |
| `msg_transaction_created(data)` | New transaction |
| `msg_transaction_updated(data)` | Updated transaction |
| `msg_anomaly_detected(txn_id, score, reason)` | Anomaly alert |
| `msg_subscription_detected(merchant, amount, period_days, next_date, confidence)` | Subscription found |
| `msg_blockchain_anchored(txn_id, hash, ipfs_cid)` | Blockchain confirmation |
| `msg_error(message, code)` | Error message |

---

## Connection Manager Methods

```python
from app.websocket.manager import manager

# Check if user is online
if manager.is_connected(str(user_id)):
    # Send message
    await manager.send_to_user(str(user_id), message)

# Broadcast to all users
await manager.broadcast(message)

# Get connection stats
total = manager.total_connections
users = manager.connected_users
```
