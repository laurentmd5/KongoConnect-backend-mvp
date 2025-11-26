from sqlalchemy import Column, Integer, Float, String, ForeignKey, Enum, DateTime, Text, Index, Boolean  # ⬅️ AJOUTE Boolean ici
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.base_class import Base
from datetime import datetime

class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"       # En attente validation artisan
    ACCEPTED = "ACCEPTED"     # Artisan a accepté
    FUNDED = "FUNDED"         # Client a payé -> Argent bloqué (Escrow)
    IN_PROGRESS = "IN_PROGRESS"  # Travail en cours
    DELIVERED = "DELIVERED"   # Artisan déclare "Fini" / Chrono 48h (Nudge)
    
    # --- Nouveaux Statuts de Rappels pour le Chrono 48h ---
    REMINDER_1 = "REMINDER_1"
    REMINDER_2 = "REMINDER_2"
    REMINDER_FINAL = "REMINDER_FINAL"
    
    COMPLETED = "COMPLETED"   # Argent libéré (Validé par client OU Auto-Release)
    DISPUTED = "DISPUTED"     # Litige ouvert
    CANCELLED = "CANCELLED"   # Annulé avant travaux

class Order(Base):
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, index=True)
    delivery_needed = Column(Boolean, default=False)    
    delivery_address = Column(String(500), nullable=True)
    
    client_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    partner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False)

    # Finance
    total_amount = Column(Float, nullable=False)
    commission_amount = Column(Float, default=0.0)

    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING)

    # --- INPUT/OUTPUT IA ---
    problem_description = Column(Text, nullable=True)
    ai_title = Column(String, nullable=True)
    ai_category = Column(String, nullable=True)
    ai_tags = Column(String, nullable=True)

    # Deep Linking WhatsApp
    partner_whatsapp = Column(String, nullable=True)

    # --- TIMESTAMPS CRITIQUES ---
    funded_at = Column(DateTime, nullable=True)
    delivered_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    # --- SUIVI DES RAPPELS ---
    reminder_1_sent_at = Column(DateTime, nullable=True)
    reminder_2_sent_at = Column(DateTime, nullable=True)
    reminder_final_sent_at = Column(DateTime, nullable=True)

    # --- LITIGE ---
    dispute_reason = Column(Text, nullable=True)
    dispute_raised_at = Column(DateTime, nullable=True)

    # Relations
    client = relationship("User", foreign_keys=[client_id], back_populates="orders_client")
    partner = relationship("User", foreign_keys=[partner_id], back_populates="orders_partner")
    listing = relationship("Listing")
    
    # Index pour optimiser les requêtes du Scheduler
    __table_args__ = (
        Index('idx_order_status', 'status'),
        Index('idx_order_funded_at', 'funded_at'),
    )

    def time_in_escrow_minutes(self) -> int:
        """Calcul le temps en minutes depuis le financement."""
        if not self.funded_at:
            return 0
        return int((datetime.utcnow() - self.funded_at).total_seconds() / 60)