import json
import math
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.models.listing import Listing
from app.schemas.listing import ListingCreate, ListingResponse
from app.core.cache import CacheManager

class MarketService:
    
    @staticmethod
    async def get_nearby_listings(
        db: AsyncSession, 
        lat: float, 
        lon: float, 
        radius_km: float
    ) -> List[dict]:
        
        redis = CacheManager.get_client()
        cache_key = f"market:nearby:{round(lat, 3)}:{round(lon, 3)}:{radius_km}"
        
        cached_data = await redis.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        
        # ✅ CORRECTIF : Pré-filtrage SQL (Bounding Box) pour performance
        # 1 degré de latitude ~= 111 km. 
        # On prend une marge large (delta) pour la requête SQL
        delta_deg = (radius_km / 111) * 1.5 # Marge de sécurité
        
        lat_min, lat_max = lat - delta_deg, lat + delta_deg
        lon_min, lon_max = lon - delta_deg, lon + delta_deg

        query = select(Listing).where(
            and_(
                Listing.latitude.between(lat_min, lat_max),
                Listing.longitude.between(lon_min, lon_max)
            )
        )
        
        result = await db.execute(query)
        candidates = result.scalars().all()
        
        nearby = []
        for item in candidates:
            if item.latitude and item.longitude:
                # Calcul précis en Python (Haversine)
                dist = MarketService._calculate_distance(lat, lon, item.latitude, item.longitude)
                if dist <= radius_km:
                    schema = ListingResponse.model_validate(item)
                    data = schema.model_dump(mode='json') 
                    nearby.append(data)
        
        await redis.set(cache_key, json.dumps(nearby), ex=300) # Cache 5 min
        
        return nearby

    @staticmethod
    async def create_listing(db: AsyncSession, listing_in: ListingCreate, partner_id: int) -> Listing:
        db_listing = Listing(**listing_in.model_dump(), partner_id=partner_id)
        db.add(db_listing)
        await db.commit()
        await db.refresh(db_listing)
        
        # Invalidation cache
        redis = CacheManager.get_client()
        keys = await redis.keys("market:nearby:*")
        if keys:
            await redis.delete(*keys)
            
        return db_listing

    @staticmethod
    def _calculate_distance(lat1, lon1, lat2, lon2):
        R = 6371 # Rayon Terre km
        dLat = math.radians(lat2 - lat1)
        dLon = math.radians(lon2 - lon1)
        a = (math.sin(dLat / 2) * math.sin(dLat / 2) +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dLon / 2) * math.sin(dLon / 2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c