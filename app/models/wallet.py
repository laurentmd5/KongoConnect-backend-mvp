from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base_class import Base

class Wallet(Base):
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    
    # ✅ CORRECTIF : Utilisation d'Integer pour éviter les erreurs d'arrondi
    # Stocké en unités FCFA (pas de centimes)
    balance = Column(Integer, default=0)
    frozen_balance = Column(Integer, default=0)

    user = relationship("User", back_populates="wallet")