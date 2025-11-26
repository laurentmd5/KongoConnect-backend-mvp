from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.sql import func
from app.models.base_class import Base

class Transaction(Base):
    """Grand Livre comptable pour l'audit."""
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)

    # Integer pour cohérence
    amount = Column(Integer, nullable=False)

    # DEPOSIT, WITHDRAWAL, ESCROW_LOCK, ESCROW_RELEASE, COMMISSION
    type = Column(String, nullable=False)

    status = Column(String, default="SUCCESS")
    reference = Column(String)

    created_at = Column(DateTime(timezone=True), server_default=func.now())