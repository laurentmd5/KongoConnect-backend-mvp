from typing import Any, ClassVar
from sqlalchemy.orm import declarative_base, declared_attr, Mapped
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func


class Base:
    """Classe de base pour tous les modèles SQLAlchemy 2.0"""
    
    # Permet à SQLAlchemy de ne pas mapper les annotations sans Mapped[]
    __allow_unmapped__ = True
    
    # Génère automatiquement le nom de table en minuscule + s (User -> users)
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower() + "s"

    id: Mapped[int] = Column(Integer, primary_key=True, index=True)
    created_at: Mapped[Any] = Column(DateTime(timezone=True), server_default=func.now())


# Créer la base déclarative
Base = declarative_base(cls=Base)

