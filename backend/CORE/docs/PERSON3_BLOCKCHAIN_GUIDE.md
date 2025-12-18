# Person 3 (Blockchain Engineer) - Complete Integration Guide

## Your Role
You build blockchain features: transaction anchoring to smart contracts, Merkle tree generation, IPFS storage for receipts, and transaction verification.

---

## Folder Structure (Create These)

```
app/
├── services/
│   └── blockchain/             # Create this folder
│       ├── __init__.py
│       ├── merkle.py           # Merkle tree generation
│       ├── anchor.py           # Smart contract interaction
│       ├── ipfs.py             # IPFS upload/download
│       └── verify.py           # Transaction verification
│
├── tasks/
│   └── blockchain.py           # ← Modify this file
```

---

## Database Tables You Use

### 1. `merkle_batches` - Track Anchoring Batches
```python
from app.models import MerkleBatch
from app.database import SessionLocal

db = SessionLocal()

# Create new batch
batch = MerkleBatch(
    merkle_root="0x1234abcd...",
    transaction_count=100,
    status="pending",  # pending, anchored, confirmed, failed
    blockchain_tx_hash=None,  # Set after anchoring
    ipfs_cid=None  # Optional IPFS backup
)
db.add(batch)
db.commit()

# Update after blockchain confirmation
batch.status = "confirmed"
batch.blockchain_tx_hash = "0xabc123..."
db.commit()
```

**Schema:**
| Column | Type | Description |
|--------|------|-------------|
| id | UUID | Primary key |
| merkle_root | String(66) | Merkle root hash |
| transaction_count | Integer | Transactions in batch |
| status | String | pending/anchored/confirmed/failed |
| blockchain_tx_hash | String | On-chain transaction hash |
| ipfs_cid | String | IPFS CID for backup |
| created_at | DateTime | Batch creation time |
| anchored_at | DateTime | Blockchain anchor time |

---

### 2. Transaction Fields for Blockchain
```python
from app.models import Transaction

# Update transaction after anchoring
txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
txn.blockchain_hash = "0x1234abcd..."  # Merkle root it belongs to
txn.ipfs_cid = "QmXyz..."              # Receipt IPFS CID
txn.is_anchored = True
db.commit()
```

**Blockchain-Related Transaction Fields:**
| Column | Type | Description |
|--------|------|-------------|
| blockchain_hash | String(66) | Merkle root hash |
| ipfs_cid | String(100) | IPFS CID for receipt |
| is_anchored | Boolean | Whether anchored to chain |

---

## Celery Tasks to Implement

### File: `app/tasks/blockchain.py`

#### 1. `create_merkle_batch()` - Create Merkle Tree
```python
@shared_task
def create_merkle_batch(user_id: str = None):
    """
    Create Merkle batch from unanchored transactions.
    Groups up to 100 transactions into a batch.
    """
    from app.database import SessionLocal
    from app.models import Transaction, MerkleBatch
    import hashlib
    
    db = SessionLocal()
    try:
        # Get unanchored transactions
        query = db.query(Transaction).filter(
            Transaction.is_anchored == False,
            Transaction.is_deleted == False
        )
        if user_id:
            query = query.filter(Transaction.user_id == user_id)
        
        txns = query.limit(100).all()
        
        if len(txns) < 10:  # Minimum batch size
            return {"status": "skipped", "reason": "Not enough transactions"}
        
        # YOUR CODE HERE - Generate Merkle tree
        # leaves = [hash_transaction(txn) for txn in txns]
        # merkle_root = build_merkle_tree(leaves)
        
        # Example hash function
        def hash_transaction(txn):
            data = f"{txn.id}|{txn.amount}|{txn.date}|{txn.user_id}"
            return hashlib.sha256(data.encode()).hexdigest()
        
        leaves = [hash_transaction(txn) for txn in txns]
        
        # Simple Merkle root calculation (implement full tree)
        merkle_root = "0x" + hashlib.sha256(
            "".join(leaves).encode()
        ).hexdigest()
        
        # Create batch record
        batch = MerkleBatch(
            merkle_root=merkle_root,
            transaction_count=len(txns),
            status="pending"
        )
        db.add(batch)
        db.commit()
        
        # Queue anchoring task
        from app.tasks.blockchain import anchor_transaction_batch
        anchor_transaction_batch.delay(
            batch_id=str(batch.id),
            merkle_root=merkle_root,
            transaction_ids=[str(t.id) for t in txns]
        )
        
        return {
            "status": "created",
            "batch_id": str(batch.id),
            "merkle_root": merkle_root,
            "transaction_count": len(txns)
        }
        
    finally:
        db.close()
```

#### 2. `anchor_transaction_batch()` - Submit to Blockchain
```python
@shared_task(bind=True, max_retries=3)
def anchor_transaction_batch(self, batch_id: str, merkle_root: str, transaction_ids: list):
    """
    Anchor Merkle root to blockchain.
    Called after batch is created.
    """
    from app.database import SessionLocal
    from app.models import Transaction, MerkleBatch
    from app.websocket.manager import manager
    from app.websocket.message_types import msg_blockchain_anchored
    import asyncio
    
    db = SessionLocal()
    try:
        batch = db.query(MerkleBatch).filter(MerkleBatch.id == batch_id).first()
        
        # YOUR CODE HERE - Submit to smart contract
        # web3 = Web3(Web3.HTTPProvider(ETHEREUM_RPC))
        # contract = web3.eth.contract(address=CONTRACT_ADDRESS, abi=ABI)
        # tx_hash = contract.functions.anchor(merkle_root).transact({
        #     'from': WALLET_ADDRESS,
        #     'gas': 100000
        # })
        # receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Placeholder - replace with actual blockchain call
        blockchain_tx_hash = "0x" + "a" * 64  # Your real tx hash
        
        # Update batch
        batch.status = "anchored"
        batch.blockchain_tx_hash = blockchain_tx_hash
        batch.anchored_at = datetime.utcnow()
        
        # Update all transactions in batch
        for txn_id in transaction_ids:
            txn = db.query(Transaction).filter(Transaction.id == txn_id).first()
            if txn:
                txn.blockchain_hash = merkle_root
                txn.is_anchored = True
                
                # Notify user
                message = msg_blockchain_anchored(
                    transaction_id=str(txn.id),
                    blockchain_hash=blockchain_tx_hash,
                    ipfs_cid=txn.ipfs_cid
                )
                asyncio.run(manager.send_to_user(str(txn.user_id), message))
        
        db.commit()
        
        return {
            "status": "anchored",
            "batch_id": batch_id,
            "tx_hash": blockchain_tx_hash,
            "transactions_anchored": len(transaction_ids)
        }
        
    except Exception as e:
        batch.status = "failed"
        db.commit()
        raise self.retry(exc=e)
    finally:
        db.close()
```

#### 3. `upload_to_ipfs()` - Store Receipt on IPFS
```python
@shared_task
def upload_to_ipfs(user_id: str, transaction_id: str, file_path: str):
    """
    Upload receipt image to IPFS.
    Called when user uploads receipt.
    """
    from app.database import SessionLocal
    from app.models import Transaction
    
    db = SessionLocal()
    try:
        txn = db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id
        ).first()
        
        if not txn:
            return {"error": "Transaction not found"}
        
        # YOUR CODE HERE - Upload to IPFS
        # import ipfshttpclient
        # client = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
        # result = client.add(file_path)
        # ipfs_cid = result['Hash']
        
        # Placeholder
        ipfs_cid = "Qm" + "x" * 44  # Your real CID
        
        # Update transaction
        txn.ipfs_cid = ipfs_cid
        db.commit()
        
        return {
            "status": "uploaded",
            "transaction_id": transaction_id,
            "ipfs_cid": ipfs_cid
        }
        
    finally:
        db.close()
```

#### 4. `process_pending_batches()` - Monitor Confirmations
```python
@shared_task
def process_pending_batches():
    """
    Check pending batches for blockchain confirmation.
    Runs every 5 minutes via Celery Beat.
    """
    from app.database import SessionLocal
    from app.models import MerkleBatch
    
    db = SessionLocal()
    try:
        pending = db.query(MerkleBatch).filter(
            MerkleBatch.status == "anchored"
        ).all()
        
        for batch in pending:
            # YOUR CODE HERE - Check blockchain confirmation
            # web3 = Web3(...)
            # receipt = web3.eth.get_transaction_receipt(batch.blockchain_tx_hash)
            # if receipt and receipt.blockNumber:
            #     confirmations = web3.eth.block_number - receipt.blockNumber
            #     if confirmations >= 6:  # 6 confirmations
            #         batch.status = "confirmed"
            
            pass  # Implement confirmation check
        
        db.commit()
        return {"status": "completed", "checked": len(pending)}
        
    finally:
        db.close()
```

---

## WebSocket Notifications

### Send Anchoring Confirmation
```python
from app.websocket.manager import manager
from app.websocket.message_types import msg_blockchain_anchored
import asyncio

message = msg_blockchain_anchored(
    transaction_id="txn-uuid",
    blockchain_hash="0x1234abcd...",
    ipfs_cid="QmXyz..."
)

# In async context
await manager.send_to_user(str(user_id), message)

# In sync context (Celery task)
asyncio.run(manager.send_to_user(str(user_id), message))
```

---

## Celery Queues & Beat Schedule

### Queues
| Queue | Use For | Priority |
|-------|---------|----------|
| `scheduled` | Batch creation, monitoring | 3 |
| `low_priority` | IPFS uploads | 1 |

```python
from app.celery_app import celery_app

@celery_app.task(queue='scheduled')
def nightly_batch():
    pass

@celery_app.task(queue='low_priority')
def bulk_ipfs_upload():
    pass
```

### Beat Schedule (Already Configured)
| Task | Schedule |
|------|----------|
| `process_pending_batches` | Every 5 minutes |
| Batch creation | 2 AM daily (add to schedule) |

---

## Transaction Verification API

Add these endpoints for users to verify their transactions:

### `GET /api/transactions/{id}/verify`
```python
# In app/api/transactions.py

@router.get("/{transaction_id}/verify")
def verify_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify transaction is on blockchain."""
    txn = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()
    
    if not txn:
        raise NotFoundException("Transaction not found")
    
    if not txn.is_anchored:
        return {"verified": False, "reason": "Not yet anchored"}
    
    # YOUR CODE - Verify on blockchain
    # is_valid = verify_merkle_proof(txn, txn.blockchain_hash)
    
    return {
        "verified": True,
        "blockchain_hash": txn.blockchain_hash,
        "ipfs_cid": txn.ipfs_cid,
        "anchored_at": txn.updated_at
    }
```

---

## Transaction Flow

```
┌─────────────────────────────────────────────────────┐
│  1. Transactions Created (is_anchored = False)      │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│  2. create_merkle_batch() - Nightly at 2 AM         │
│     - Groups 100 unanchored transactions            │
│     - Generates Merkle tree                         │
│     - Creates MerkleBatch record (status=pending)   │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│  3. anchor_transaction_batch()                      │
│     - Submits merkle_root to smart contract         │
│     - Updates batch (status=anchored)               │
│     - Updates transactions (is_anchored=True)       │
│     - Sends WebSocket notifications                 │
└─────────────────────┬───────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────┐
│  4. process_pending_batches() - Every 5 min         │
│     - Checks for 6+ confirmations                   │
│     - Updates batch (status=confirmed)              │
└─────────────────────────────────────────────────────┘
```

---

## Testing

```bash
# Test blockchain task imports
python -c "from app.tasks.blockchain import anchor_transaction_batch, create_merkle_batch; print('OK')"

# Test MerkleBatch model
python -c "from app.models import MerkleBatch; print('OK')"
```
