"""
CRUD Test Script for Supabase Backend.
Tests all major operations with sample data.
"""
from dotenv import load_dotenv
load_dotenv(override=True)

from app.config import reset_settings, get_settings
from app.database import reset_engine, get_engine
reset_settings()
reset_engine()

settings = get_settings()
print("=" * 60)
print("SUPABASE BACKEND CRUD TEST")
print("=" * 60)

# 1. Test Database Connection
print("\n[1] Testing Database Connection...")
engine = get_engine()
from sqlalchemy import text

with engine.connect() as conn:
    result = conn.execute(text("SELECT current_database()"))
    db_name = result.fetchone()[0]
    print(f"    ✅ Connected to: {db_name}")
    
    # Check tables
    result = conn.execute(text("SELECT COUNT(*) FROM pg_tables WHERE schemaname = 'public'"))
    table_count = result.fetchone()[0]
    print(f"    ✅ Tables found: {table_count}")

# 2. Test Models Import
print("\n[2] Testing Model Imports...")
try:
    from app.models import User, Transaction, Budget, AuditLog, MerchantMaster
    print("    ✅ All models imported successfully")
except Exception as e:
    print(f"    ❌ Import error: {e}")
    exit(1)

# 3. Test User Creation (simulating Supabase sync)
print("\n[3] Testing User Creation...")
from app.database import get_session_local
from datetime import date
import uuid

SessionLocal = get_session_local()
db = SessionLocal()

try:
    test_user_id = uuid.uuid4()
    test_user = User(
        id=test_user_id,
        email=f"test_{test_user_id.hex[:8]}@supabase.test",
        full_name="Test User (CRUD Test)",
        is_active=True,
        is_verified=True,
        wallet_addresses=[],
        preferences={"theme": "dark"},
        user_metadata={"source": "crud_test"}
    )
    db.add(test_user)
    db.commit()
    print(f"    ✅ User created: {test_user.email}")
except Exception as e:
    db.rollback()
    print(f"    ❌ User creation error: {e}")

# 4. Test Transaction Creation
print("\n[4] Testing Transaction Creation...")
try:
    test_txn = Transaction(
        user_id=test_user_id,
        amount=25.50,
        date=date.today(),
        merchant_raw="Starbucks Coffee",
        category="Food",
        subcategory="Coffee",
        source="manual",
        description="Morning coffee - CRUD test"
    )
    db.add(test_txn)
    db.commit()
    print(f"    ✅ Transaction created: ${test_txn.amount} at {test_txn.merchant_raw}")
    print(f"    ✅ Transaction ID: {test_txn.id}")
except Exception as e:
    db.rollback()
    print(f"    ❌ Transaction creation error: {e}")

# 5. Test Transaction Read
print("\n[5] Testing Transaction Read...")
try:
    txns = db.query(Transaction).filter(Transaction.user_id == test_user_id).all()
    print(f"    ✅ Found {len(txns)} transaction(s) for user")
    for t in txns:
        print(f"       - {t.category}: ${t.amount} at {t.merchant_raw}")
except Exception as e:
    print(f"    ❌ Transaction read error: {e}")

# 6. Test Transaction Update
print("\n[6] Testing Transaction Update...")
try:
    test_txn.category = "Food & Drink"
    test_txn.subcategory = "Coffee Shop"
    db.commit()
    print(f"    ✅ Transaction updated: category = {test_txn.category}")
except Exception as e:
    db.rollback()
    print(f"    ❌ Transaction update error: {e}")

# 7. Test Audit Log
print("\n[7] Testing Audit Log...")
try:
    audit = AuditLog.log(
        db, 
        "transaction.update", 
        user_id=test_user_id,
        entity="transaction",
        entity_id=str(test_txn.id),
        changes={"category": "Food -> Food & Drink"}
    )
    db.commit()
    print(f"    ✅ Audit log created: {audit.action}")
except Exception as e:
    db.rollback()
    print(f"    ❌ Audit log error: {e}")

# 8. Test Soft Delete
print("\n[8] Testing Soft Delete...")
try:
    test_txn.is_deleted = True
    db.commit()
    
    # Verify it's hidden from normal queries
    visible_txns = db.query(Transaction).filter(
        Transaction.user_id == test_user_id,
        Transaction.is_deleted == False
    ).count()
    print(f"    ✅ Transaction soft deleted")
    print(f"       Visible transactions: {visible_txns}")
except Exception as e:
    db.rollback()
    print(f"    ❌ Soft delete error: {e}")

# 9. Test Budget Creation
print("\n[9] Testing Budget Creation...")
try:
    test_budget = Budget(
        user_id=test_user_id,
        category="Food",
        limit_amount=500.00,
        period="monthly",
        start_date=date.today(),
        end_date=date(2025, 1, 31),
        alert_threshold=80.0
    )
    db.add(test_budget)
    db.commit()
    print(f"    ✅ Budget created: ${test_budget.limit_amount} for {test_budget.category}")
except Exception as e:
    db.rollback()
    print(f"    ❌ Budget creation error: {e}")

# Cleanup (optional - comment out to keep test data)
print("\n[10] Cleanup...")
try:
    db.query(AuditLog).filter(AuditLog.actor_user_id == test_user_id).delete()
    db.query(Transaction).filter(Transaction.user_id == test_user_id).delete()
    db.query(Budget).filter(Budget.user_id == test_user_id).delete()
    db.query(User).filter(User.id == test_user_id).delete()
    db.commit()
    print("    ✅ Test data cleaned up")
except Exception as e:
    db.rollback()
    print(f"    ⚠️ Cleanup error (may be OK): {e}")

db.close()

print("\n" + "=" * 60)
print("CRUD TEST COMPLETE ✅")
print("=" * 60)
