from sqlalchemy import Column, String, Boolean, Enum
from sqlalchemy.orm import relationship
import enum
from app.models.base_class import Base

class UserRole(str, enum.Enum):
    CLIENT = "CLIENT"
    ARTISAN = "ARTISAN"
    VENDEUR = "VENDEUR"
    ADMIN = "ADMIN"

class User(Base):
    phone = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    role = Column(Enum(UserRole), default=UserRole.CLIENT)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)

    wallet = relationship("Wallet", back_populates="user", uselist=False, cascade="all, delete-orphan")
    listings = relationship("Listing", back_populates="partner")
    orders_client = relationship("Order", foreign_keys="Order.client_id", back_populates="client")
    orders_partner = relationship("Order", foreign_keys="Order.partner_id", back_populates="partner")