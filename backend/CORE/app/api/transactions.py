"""
Transaction API Endpoints - Simple and Clear
Each endpoint does one thing well with minimal complexity.
"""
from fastapi import APIRouter, Depends, Query, status, UploadFile, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from datetime import date
from uuid import UUID

from app.database import get_db
from app.models.user import User
from app.schemas.transaction import (
    TransactionCreate,
    TransactionUpdate,
    TransactionResponse,
    TransactionListResponse,
    TransactionCorrection,
    TransactionCorrectionResponse,
    TransactionStats
)
from app.services.transaction import TransactionService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/transactions", tags=["Transactions"])


# ==================== HELPER ====================
def to_response(t) -> TransactionResponse:
    """Convert Transaction model to response schema."""
    return TransactionResponse(
        id=str(t.id),
        user_id=str(t.user_id),
        amount=str(t.amount),
        date=t.date,
        merchant_raw=t.merchant_raw,
        merchant=None,  # Simplified: no merchant lookup
        category=t.category,
        description=t.description,
        source=t.source or "manual",
        confidence=t.confidence,
        anomaly_score=t.anomaly_score or 0.0,
        blockchain_hash=t.blockchain_hash,
        ipfs_cid=t.ipfs_cid,
        is_anchored=t.is_anchored or False,
        created_at=t.created_at,
        updated_at=t.updated_at
    )


# ==================== LIST ====================
@router.get("/", response_model=TransactionListResponse, summary="List transactions")
def list_transactions(
    since: Optional[date] = Query(None, description="Start date"),
    until: Optional[date] = Query(None, description="End date"),
    category: Optional[str] = Query(None, description="Category filter"),
    source: Optional[str] = Query(None, description="Source filter"),
    min_amount: Optional[float] = Query(None, description="Min amount"),
    max_amount: Optional[float] = Query(None, description="Max amount"),
    search: Optional[str] = Query(None, min_length=2, description="Search in merchant/description"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get paginated list of transactions with optional filters and search."""
    service = TransactionService(db)
    transactions, total = service.list_all(
        user_id=current_user.id,
        limit=limit,
        offset=offset,
        since=since,
        until=until,
        category=category,
        source=source,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search
    )
    
    return TransactionListResponse(
        data=[to_response(t) for t in transactions],
        total=total,
        limit=limit,
        offset=offset,
        has_more=offset + len(transactions) < total
    )


# ==================== GET STATS ====================
@router.get("/stats", response_model=TransactionStats, summary="Get statistics")
def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transaction statistics for current user."""
    service = TransactionService(db)
    return TransactionStats(**service.get_stats(current_user.id))


# ==================== GET ONE ====================
@router.get("/{transaction_id}", response_model=TransactionResponse, summary="Get transaction")
def get_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a single transaction by ID."""
    service = TransactionService(db)
    transaction = service.get_by_id(transaction_id, current_user.id)
    return to_response(transaction)


# ==================== CREATE ====================
@router.post("/", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED, summary="Create transaction")
def create_transaction(
    data: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new transaction."""
    service = TransactionService(db)
    transaction = service.create(
        user_id=current_user.id,
        amount=data.amount,
        transaction_date=data.transaction_date,
        source=data.source,
        merchant_raw=data.merchant_raw,
        category=data.category,
        description=data.description
    )
    
    # Check budget alert if category is set
    if data.category:
        try:
            from app.services.budget import BudgetService
            budget_service = BudgetService(db)
            alerts = budget_service.get_alerts(current_user.id)
            
            # Find alert for this category
            for alert in alerts:
                if alert["category"] == data.category:
                    # Queue notification task (async, non-blocking)
                    from app.tasks.notifications import send_budget_alert
                    send_budget_alert.delay(str(current_user.id), alert)
                    break
        except Exception:
            pass  # Don't block transaction on alert errors
    
    return to_response(transaction)


# ==================== UPDATE ====================
@router.patch("/{transaction_id}", response_model=TransactionResponse, summary="Update transaction")
def update_transaction(
    transaction_id: UUID,
    data: TransactionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update a transaction (partial update)."""
    service = TransactionService(db)
    
    # Build updates dict from provided values
    updates = {}
    if data.amount is not None:
        updates['amount'] = data.amount
    if data.transaction_date is not None:
        updates['date'] = data.transaction_date
    if data.merchant_raw is not None:
        updates['merchant_raw'] = data.merchant_raw
    if data.category is not None:
        updates['category'] = data.category
    if data.description is not None:
        updates['description'] = data.description
    
    transaction = service.update(transaction_id, current_user.id, **updates)
    return to_response(transaction)


# ==================== DELETE ====================
@router.delete("/{transaction_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete transaction")
def delete_transaction(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a transaction."""
    service = TransactionService(db)
    service.delete(transaction_id, current_user.id)


# ==================== CORRECT ====================
@router.post("/{transaction_id}/correct", response_model=TransactionCorrectionResponse, summary="Correct transaction")
def correct_transaction(
    transaction_id: UUID,
    data: TransactionCorrection,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit a user correction for ML training."""
    service = TransactionService(db)
    transaction, correction = service.add_correction(
        transaction_id=transaction_id,
        user_id=current_user.id,
        field=data.field_corrected,
        new_value=data.new_value,
        reason=data.correction_reason
    )
    
    return TransactionCorrectionResponse(
        message="Transaction corrected",
        transaction_id=str(transaction.id),
        field_corrected=data.field_corrected,
        old_value=correction.old_value,
        new_value=data.new_value
    )


# ==================== CSV UPLOAD ====================
@router.post("/upload", status_code=status.HTTP_202_ACCEPTED, summary="Upload CSV")
async def upload_csv(
    file: UploadFile,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload CSV file of transactions for batch processing.
    
    CSV format:
    date,amount,merchant,category,description
    2024-01-15,50.00,Starbucks,Food,Coffee
    
    Processing happens in background via Celery.
    """
    import tempfile
    import os
    
    # Validate file type
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format")
    
    # Save to temp file
    content = await file.read()
    temp_path = os.path.join(tempfile.gettempdir(), f"upload_{current_user.id}_{file.filename}")
    with open(temp_path, 'wb') as f:
        f.write(content)
    
    # Queue batch processing
    try:
        from app.tasks.process_transaction import batch_process_csv
        task = batch_process_csv.delay(str(current_user.id), temp_path)
        task_id = task.id
    except Exception:
        task_id = "queued"  # Celery not running
    
    return {
        "message": "CSV upload accepted for processing",
        "filename": file.filename,
        "task_id": task_id,
        "status": "processing"
    }


# ==================== EXPORT ====================
@router.get("/export", summary="Export transactions")
def export_transactions(
    format: str = Query("csv", description="Export format: csv or json"),
    since: Optional[date] = Query(None),
    until: Optional[date] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export transactions as CSV or JSON.
    
    Returns downloadable file content.
    """
    from fastapi.responses import Response
    import csv
    import io
    import json as json_lib
    
    service = TransactionService(db)
    transactions, _ = service.list_all(
        user_id=current_user.id,
        limit=10000,  # Max export
        offset=0,
        since=since,
        until=until
    )
    
    if format == "json":
        data = [
            {
                "id": str(t.id),
                "date": str(t.date),
                "amount": str(t.amount),
                "merchant": t.merchant_raw,
                "category": t.category,
                "description": t.description
            }
            for t in transactions
        ]
        return Response(
            content=json_lib.dumps(data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=transactions.json"}
        )
    
    # CSV format (default)
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["date", "amount", "merchant", "category", "description"])
    
    for t in transactions:
        writer.writerow([
            str(t.date),
            str(t.amount),
            t.merchant_raw or "",
            t.category or "",
            t.description or ""
        ])
    
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=transactions.csv"}
    )
