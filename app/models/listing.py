from sqlalchemy import Column, String, Integer, Float, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base_class import Base

class Listing(Base):
    partner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    
    # ✅ CORRECTIF : Integer pour le prix
    price = Column(Integer, nullable=False) 
    price_unit = Column(String, default="Unité")
    type = Column(String, nullable=False) # SERVICE / PRODUCT
    category = Column(String, default="all")
    
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    is_flash_offer = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=True)

    partner = relationship("User", back_populates="listings")
    