from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.wallet import Wallet
from app.schemas.wallet import WalletResponse, WalletDepositRequest, WalletWithdrawRequest
from app.services.wallet_service import WalletService

router = APIRouter()

@router.get("/me", response_model=WalletResponse)
async def get_my_wallet(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Récupère le wallet de l'utilisateur connecté."""
    return await WalletService.get_balance(db, current_user.id)

@router.post("/deposit")
async def deposit_to_wallet(
    deposit_in: WalletDepositRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Dépose de l'argent sur le wallet"""
    return await WalletService.deposit(db, current_user.id, deposit_in.amount)

@router.post("/withdraw")
async def withdraw_from_wallet(
    withdraw_in: WalletWithdrawRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Retrait d'argent du wallet"""
    return await WalletService.withdraw(db, current_user.id, withdraw_in.amount)