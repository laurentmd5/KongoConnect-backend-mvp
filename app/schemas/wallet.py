from pydantic import BaseModel

class WalletResponse(BaseModel):
    balance: int
    frozen_balance: int
    currency: str = "FCFA"

    class Config:
        from_attributes = True