from fastapi import APIRouter
from app.api.v1.endpoints import auth, market, orders, wallet

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(market.router, prefix="/market", tags=["Marketplace"])
api_router.include_router(orders.router, prefix="/orders", tags=["Orders & Escrow"])
api_router.include_router(wallet.router, prefix="/wallet", tags=["Wallet"])