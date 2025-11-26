from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.order import OrderStatus

class OrderCreate(BaseModel):
    listing_id: int = Field(..., description="ID du service demandé.")
    delivery_needed: bool = False
    delivery_address: Optional[str] = Field(None, description="Adresse de livraison si pertinent.")
    problem_description: Optional[str] = Field(None, description="Description détaillée du problème par le client.")

class OrderResponse(BaseModel):
    id: int
    client_id: int
    partner_id: int
    listing_id: int
    total_amount: float
    commission_amount: Optional[float] = 0.0
    status: OrderStatus

    # Infos client
    problem_description: Optional[str]

    # Infos IA
    ai_title: Optional[str]
    ai_category: Optional[str]
    ai_tags: Optional[str]

    # Dates importantes
    created_at: datetime
    funded_at: Optional[datetime]
    delivered_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    # Champs optionnels pour éviter les erreurs
    auto_release_at: Optional[datetime] = None
    nudge_step: Optional[int] = 0
    partner_whatsapp: Optional[str] = None
    reminder_1_sent_at: Optional[datetime] = None
    reminder_2_sent_at: Optional[datetime] = None
    reminder_final_sent_at: Optional[datetime] = None
    dispute_reason: Optional[str] = None
    dispute_raised_at: Optional[datetime] = None

    class Config:
        from_attributes = True