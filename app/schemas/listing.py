from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ListingBase(BaseModel):
    title: str
    description: Optional[str] = None
    price: int  # Integer ici aussi
    price_unit: str = "Unité"
    type: str 
    category: str = "all"
    latitude: Optional[float] = None
    longitude: Optional[float] = None

class ListingCreate(ListingBase):
    pass

class ListingResponse(ListingBase):
    id: int
    partner_id: int
    created_at: datetime
    class Config:
        from_attributes = True