from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.api.auth import get_current_user # Ensure this import path matches your auth file

router = APIRouter()

# --- Schema ---
class WalletConnectRequest(BaseModel):
    wallet_address: str
    wallet_type: str = "metamask" 

# --- Endpoint ---
@router.post("/connect", status_code=status.HTTP_200_OK)
def connect_wallet(
    payload: WalletConnectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user) 
):
    """
    Links a blockchain wallet address to the current user's account.
    """
    try:
        was_added = current_user.add_wallet(payload.wallet_address)
        
        if was_added:
            db.commit()
            db.refresh(current_user)
            return {"status": "connected", "action": "added", "wallets": current_user.wallet_addresses}
        
        return {"status": "connected", "action": "exists", "wallets": current_user.wallet_addresses}

    except Exception as e:
        db.rollback()
        print(f"Error linking wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))