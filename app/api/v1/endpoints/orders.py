from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.listing import Listing
from app.models.order import Order
from app.schemas.order import OrderCreate, OrderResponse
from app.services.escrow_service import EscrowService

router = APIRouter()

@router.post("/", response_model=OrderResponse)
async def create_order(
    order_in: OrderCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Vérifier si le listing existe
    res = await db.execute(select(Listing).where(Listing.id == order_in.listing_id))
    listing = res.scalars().first()
    if not listing:
        raise HTTPException(status_code=404, detail="Service/Produit introuvable")

    return await EscrowService.create_order(
        db, listing, current_user.id, order_in.delivery_needed, order_in.delivery_address
    )

@router.post("/{order_id}/pay", response_model=OrderResponse)
async def pay_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Le client déclenche le séquestre (bloque les fonds)"""
    return await EscrowService.fund_order(db, order_id, current_user.id)

@router.post("/{order_id}/release", response_model=OrderResponse)
async def validate_order(
    order_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Le client valide le travail fini"""
    return await EscrowService.release_funds(db, order_id, current_user.id)

@router.get("/", response_model=List[OrderResponse])
async def my_orders(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Récupère les commandes où je suis client OU vendeur
    query = select(Order).where(
        (Order.client_id == current_user.id) | (Order.partner_id == current_user.id)
    )
    res = await db.execute(query)
    return res.scalars().all()