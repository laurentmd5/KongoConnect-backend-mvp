from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.wallet import Wallet
from app.models.transaction import Transaction

class WalletService:
    
    @staticmethod
    async def get_balance(db: AsyncSession, user_id: int) -> Wallet:
        """Récupère le wallet d'un utilisateur"""
        result = await db.execute(select(Wallet).where(Wallet.user_id == user_id))
        wallet = result.scalars().first()
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet introuvable")
            
        return wallet
    
    @staticmethod
    async def deposit(db: AsyncSession, user_id: int, amount: int) -> dict:
        """Dépose de l'argent sur le wallet (simulation pour MVP)"""
        wallet = await WalletService.get_balance(db, user_id)
        
        # Crédit du wallet
        wallet.balance += amount
        
        # Trace comptable
        tx = Transaction(
            wallet_id=wallet.id,
            amount=amount,
            type="DEPOSIT",
            reference=f"DEP-{user_id}"
        )
        db.add(tx)
        
        await db.commit()
        return {"status": "Dépôt réussi", "new_balance": wallet.balance}
    
    @staticmethod
    async def withdraw(db: AsyncSession, user_id: int, amount: int) -> dict:
        """Retrait d'argent du wallet"""
        wallet = await WalletService.get_balance(db, user_id)
        
        # Vérification solde
        if wallet.balance < amount:
            raise HTTPException(status_code=400, detail="Solde insuffisant")
        
        # Débit du wallet
        wallet.balance -= amount
        
        # Trace comptable
        tx = Transaction(
            wallet_id=wallet.id,
            amount=-amount,
            type="WITHDRAWAL", 
            reference=f"WITH-{user_id}"
        )
        db.add(tx)
        
        await db.commit()
        return {"status": "Retrait réussi", "new_balance": wallet.balance}