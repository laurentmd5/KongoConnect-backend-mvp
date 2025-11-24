from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.wallet import WalletResponse

router = APIRouter()

@router.get("/me", response_model=WalletResponse)
async def get_my_wallet(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Le wallet est déjà chargé via la relation User, mais pour être sûr du solde frais :
    res = await db.execute(select(Wallet).where(Wallet.user_id == current_user.id))
    return res.scalars().first()