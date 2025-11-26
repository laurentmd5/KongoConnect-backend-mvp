from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.transaction import Transaction
from sqlalchemy import select

router = APIRouter()

@router.get("/")
async def get_my_transactions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupérer l'historique des transactions de l'utilisateur"""
    query = select(Transaction).where(
        Transaction.wallet_id == current_user.wallet.id
    ).order_by(Transaction.created_at.desc())
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    return transactions
