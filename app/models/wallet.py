from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from app.models.base_class import Base

class Wallet(Base):
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # Integer pour cohérence avec EscrowAccount
    balance = Column(Integer, default=0)
    
    # Devise (Pour la clarté comptable, par défaut XAF pour Congo)
    currency = Column(String, default="XAF")

    user = relationship("User", back_populates="wallet")