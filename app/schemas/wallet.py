from pydantic import BaseModel, Field

class WalletResponse(BaseModel):
    balance: int
    currency: str = "FCFA"

    class Config:
        from_attributes = True

class WalletDepositRequest(BaseModel):
    amount: int = Field(..., gt=0, description="Montant à déposer en FCFA")

class WalletWithdrawRequest(BaseModel):
    amount: int = Field(..., gt=0, description="Montant à retirer en FCFA")