from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Enum
from sqlalchemy.orm import relationship
import enum
from app.models.base_class import Base

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    FUNDED = "FUNDED"
    IN_PROGRESS = "IN_PROGRESS"
    DELIVERED = "DELIVERED"
    COMPLETED = "COMPLETED"
    DISPUTED = "DISPUTED"

class Order(Base):
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    partner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)
    
    # ✅ CORRECTIF : Integer pour le montant
    total_amount = Column(Integer, nullable=False)
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)
    
    delivery_needed = Column(Boolean, default=False)
    delivery_address = Column(String, nullable=True)

    client = relationship("User", foreign_keys=[client_id], back_populates="orders_client")
    partner = relationship("User", foreign_keys=[partner_id], back_populates="orders_partner")
    listing = relationship("Listing")