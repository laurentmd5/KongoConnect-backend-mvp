from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.order import Order, OrderStatus
from app.models.listing import Listing

class OrderService:
    
    @staticmethod
    async def create_order(db: AsyncSession, client_id: int, listing_id: int, problem_description: str = None) -> Order:
        """Crée une nouvelle commande avec validation"""
        # Vérifier le listing
        result = await db.execute(select(Listing).where(Listing.id == listing_id))
        listing = result.scalars().first()
        
        if not listing:
            raise HTTPException(status_code=404, detail="Service introuvable")
        
        # Créer la commande
        new_order = Order(
            client_id=client_id,
            partner_id=listing.partner_id,
            listing_id=listing.id,
            total_amount=listing.price,
            problem_description=problem_description,
            status=OrderStatus.PENDING
        )
        
        db.add(new_order)
        await db.commit()
        await db.refresh(new_order)
        
        return new_order
    
    @staticmethod
    async def get_user_orders(db: AsyncSession, user_id: int) -> list[Order]:
        """Récupère toutes les commandes d'un utilisateur (client ou artisan)"""
        query = select(Order).where(
            (Order.client_id == user_id) | (Order.partner_id == user_id)
        ).order_by(Order.created_at.desc())
        
        result = await db.execute(query)
        return result.scalars().all()