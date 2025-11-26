from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from sqlalchemy import select
from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.listing import Listing
from app.schemas.listing import ListingCreate, ListingResponse
from app.services.market_service import MarketService

router = APIRouter()

@router.post("/", response_model=ListingResponse)
async def create_listing(
    listing_in: ListingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Créer un nouveau service/produit."""
    # Création directe avec contrôle des champs pour éviter les erreurs de parsing
    new_listing = Listing(
        title=listing_in.title,
        description=listing_in.description or "",
        price=listing_in.price,
        category=listing_in.category,
        type=listing_in.type,
        partner_id=current_user.id,
        price_unit=listing_in.price_unit,
        latitude=listing_in.latitude,
        longitude=listing_in.longitude
    )
    
    db.add(new_listing)
    await db.commit()
    await db.refresh(new_listing)
    return new_listing

@router.get("/nearby", response_model=List[ListingResponse])
async def get_nearby(
    lat: float,
    lon: float,
    radius: float = 10.0,
    db: AsyncSession = Depends(get_db)
):
    return await MarketService.get_nearby_listings(db, lat, lon, radius)

@router.get("/", response_model=List[ListingResponse])
async def get_all_listings(
    db: AsyncSession = Depends(get_db)
):
    """Récupère tous les listings disponibles"""
    result = await db.execute(select(Listing).where(Listing.is_available == True))
    return result.scalars().all()