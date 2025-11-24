from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.schemas.listing import ListingCreate, ListingResponse
from app.services.market_service import MarketService

router = APIRouter()

@router.post("/", response_model=ListingResponse)
async def create_listing(
    listing_in: ListingCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return await MarketService.create_listing(db, listing_in, current_user.id)

@router.get("/nearby", response_model=List[ListingResponse])
async def get_nearby(
    lat: float,
    lon: float,
    radius: float = 10.0,
    db: AsyncSession = Depends(get_db)
):
    return await MarketService.get_nearby_listings(db, lat, lon, radius)