from sqlalchemy import Column, String, Float, Boolean, Integer, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.models.base_class import Base

class Listing(Base):
    partner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    price = Column(Integer, nullable=False) # Prix de base ou horaire
    price_unit = Column(String, default="Prestation") # "Heure", "Jour", "Forfait"
    
    # MVP 1.0 : On se concentre sur les SERVICES.
    # Type est forcé à "SERVICE" par défaut, mais on garde le champ pour la compatibilité future.
    type = Column(String, default="SERVICE") 
    category = Column(String, default="DIVERS") # PLOMBERIE, COIFFURE, MENAGE...
    
    # Géolocalisation (Vital pour la recherche locale)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    
    # Disponibilité (Le "On/Off" de l'artisan)
    is_available = Column(Boolean, default=True)
    
    partner = relationship("User", back_populates="listings")