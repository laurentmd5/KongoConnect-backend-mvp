from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.escrow_account import EscrowStatus

class EscrowAccountBase(BaseModel):
    """Schéma de base pour EscrowAccount"""
    order_id: int = Field(..., description="ID de la commande associée")
    amount: int = Field(..., ge=1, description="Montant séquestré en FCFA (entier)")
    commission_amount: int = Field(..., ge=0, description="Commission KoCo en FCFA")
    artisan_payout: int = Field(..., ge=1, description="Paiement net artisan en FCFA")

class EscrowAccountCreate(EscrowAccountBase):
    """Schéma pour création d'EscrowAccount (utilisé en interne)"""
    pass

class EscrowAccountResponse(EscrowAccountBase):
    """Schéma de réponse pour EscrowAccount"""
    id: int
    status: EscrowStatus
    created_at: datetime
    locked_at: datetime
    released_at: Optional[datetime] = None
    refunded_at: Optional[datetime] = None
    reason: Optional[str] = None
    released_by: Optional[str] = None

    class Config:
        from_attributes = True

class EscrowAccountSummary(BaseModel):
    """Schéma simplifié pour affichage rapide"""
    order_id: int
    status: EscrowStatus
    amount: int
    time_locked_minutes: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True

class EscrowReleaseRequest(BaseModel):
    """Schéma pour demande de libération manuelle"""
    trigger_source: str = Field("manual", description="Source du déclenchement")
    reason: Optional[str] = Field(None, description="Raison de la libération")

class EscrowRefundRequest(BaseModel):
    """Schéma pour demande de remboursement (litige)"""
    reason: str = Field(..., min_length=10, description="Raison détaillée du remboursement")
    refunded_by: str = Field(..., description="Qui initie le remboursement")