from datetime import datetime
from enum import Enum
from sqlalchemy import Column, Integer, ForeignKey, DateTime, Enum as SQLEnum, Text, Index, String
from sqlalchemy.orm import relationship
# Correction d'import pour utiliser la classe de base standard du projet
from app.models.base_class import Base 


class EscrowStatus(str, Enum):
    """Lifecycle of funds in escrow"""
    LOCKED = "LOCKED"         # Funds received from client, waiting for work completion
    RELEASED = "RELEASED"     # Funds transferred to artisan after work validation
    REFUNDED = "REFUNDED"     # Funds returned to client (dispute/cancellation)
    EXPIRED = "EXPIRED"       # Never used (for future audit purposes)


class EscrowAccount(Base):
    """
    Technical account holding client funds during order lifecycle.
    
    Key Invariants:
    1. amount is always > 0 (never created with 0)
    2. order_id is UNIQUE (one account per order)
    3. created_at is immutable (set once at creation)
    4. released_at or refunded_at is set EXACTLY when status changes
    5. reason is populated only for REFUNDED/EXPIRED states
    """
    
    __tablename__ = "escrow_account"
    
    # ===== Primary & Foreign Keys =====
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer,
        # Assurez-vous que l'Order Model est bien 'orders' et non 'order'
        ForeignKey("orders.id", ondelete="CASCADE"), 
        unique=True,
        nullable=False,
        index=True,
        comment="One-to-one relationship with Order"
    )
    
    # ===== Financial Data (FCFA - Integers) =====
    amount = Column(
        Integer,
        nullable=False,
        comment="Amount locked in escrow (in FCFA). Immutable after creation."
    )
    commission_amount = Column(
        Integer,
        default=0,
        nullable=False,
        comment="KoCo commission (typically 5% of amount). Calculated at creation."
    )
    artisan_payout = Column(
        Integer,
        nullable=False,
        comment="Net amount artisan will receive (amount - commission). Immutable."
    )
    
    # ===== Account Lifecycle =====
    status = Column(
        SQLEnum(EscrowStatus),
        default=EscrowStatus.LOCKED,
        nullable=False,
        index=True,
        comment="Current state of funds"
    )
    
    # ===== Audit Timestamps =====
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="When client funds arrived in escrow"
    )
    locked_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        comment="When escrow lock confirmed (same as created_at for now)"
    )
    released_at = Column(
        DateTime,
        nullable=True,
        comment="When funds were transferred to artisan (RELEASED)"
    )
    refunded_at = Column(
        DateTime,
        nullable=True,
        comment="When funds were returned to client (REFUNDED)"
    )
    
    # ===== Audit Trail =====
    reason = Column(
        Text,
        nullable=True,
        comment="Why funds were refunded/expired (for dispute tracking)"
    )
    released_by = Column(
        String(50),
        nullable=True,
        comment="'auto_release' | 'manual_admin' | 'dispute_resolution'"
    )
    
    # ===== Indexes for Performance =====
    __table_args__ = (
        Index('idx_order_id_status', 'order_id', 'status'),
        Index('idx_created_at', 'created_at'),
        Index('idx_status', 'status'),
    )
    
    # ===== Relationships =====
    # La relation backref='escrow_account' sera créée dans order.py
    order = relationship("Order", backref="escrow_account", uselist=False) 
    
    # ===== Helper Methods =====
    
    def is_locked(self) -> bool:
        """Check if funds are currently locked"""
        return self.status == EscrowStatus.LOCKED
    
    def time_locked(self) -> int:
        """Minutes elapsed since escrow lock"""
        return int((datetime.utcnow() - self.locked_at).total_seconds() / 60)
    
    def is_auto_release_ready(self) -> bool:
        """
        Check if eligible for auto-release (called by scheduler).
        
        Conditions:
        1. Status is LOCKED
        2. At least 48 hours (2880 minutes) have passed
        3. No active dispute (checked in scheduler, not here)
        """
        if self.status != EscrowStatus.LOCKED:
            return False
        return self.time_locked() >= 2880 # 48 hours in minutes
    
    def get_summary(self) -> dict:
        """Quick audit summary"""
        return {
            "order_id": self.order_id,
            "status": self.status.value,
            "amount": self.amount,
            "commission": self.commission_amount,
            "artisan_payout": self.artisan_payout,
            "time_locked_minutes": self.time_locked() if self.is_locked() else None,
            "created_at": self.created_at.isoformat(),
            "released_at": self.released_at.isoformat() if self.released_at else None,
            "refunded_at": self.refunded_at.isoformat() if self.refunded_at else None,
        }
    
    def __repr__(self):
        return (
            f"<EscrowAccount order_id={self.order_id} "
            f"amount={self.amount} "
            f"status={self.status.value} "
            f"time_locked={self.time_locked()}min>"
        )