from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.order import OrderStatus

class OrderBase(BaseModel):
    listing_id: int
    quantity: int = 1 # Optionnel pour la v2
    delivery_needed: bool = False
    delivery_address: Optional[str] = None

class OrderCreate(OrderBase):
    pass

class OrderResponse(OrderBase):
    id: int
    client_id: int
    partner_id: int
    total_amount: int # En Integer (FCFA)
    status: OrderStatus
    created_at: datetime

    class Config:
        from_attributes = True