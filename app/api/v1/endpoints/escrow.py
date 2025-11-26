from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.escrow_account import EscrowAccount
from app.models.order import Order
from sqlalchemy import select, and_

router = APIRouter()

@router.get("/")
async def get_my_escrows(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer les escrows de l'artisan"""
    query = select(EscrowAccount).join(
        Order, EscrowAccount.order_id == Order.id
    ).where(
        and_(
            Order.partner_id == current_user.id,
            EscrowAccount.status == "LOCKED"
        )
    ).order_by(EscrowAccount.created_at.desc())
    
    result = await db.execute(query)
    escrows = result.scalars().all()
    
    return escrows
