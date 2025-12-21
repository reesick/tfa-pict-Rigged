from pydantic import BaseModel

class WalletConnectRequest(BaseModel):
    wallet_address: str
    wallet_type: str = "metamask" 