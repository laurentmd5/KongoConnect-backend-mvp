from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.order import Order, OrderStatus
from app.models.wallet import Wallet
from app.models.user import User

class EscrowService:
    
    @staticmethod
    async def create_order(db: AsyncSession, listing, client_id: int, delivery_needed: bool, address: str) -> Order:
        # Calcul montant (Listing Price * 1 pour l'instant)
        amount = listing.price 
        
        new_order = Order(
            client_id=client_id,
            partner_id=listing.partner_id,
            listing_id=listing.id,
            total_amount=amount,
            status=OrderStatus.PENDING,
            delivery_needed=delivery_needed,
            delivery_address=address
        )
        db.add(new_order)
        await db.commit()
        await db.refresh(new_order)
        return new_order

    @staticmethod
    async def fund_order(db: AsyncSession, order_id: int, client_id: int):
        """Le client paie -> KoCo bloque les fonds"""
        # 1. Récupérer la commande
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalars().first()
        
        if not order or order.client_id != client_id:
            raise HTTPException(status_code=404, detail="Commande introuvable")
        
        if order.status != OrderStatus.ACCEPTED:
             # Pour le MVP, on accepte de payer directement si PENDING
             pass

        # 2. Récupérer Wallet Client
        w_res = await db.execute(select(Wallet).where(Wallet.user_id == client_id))
        client_wallet = w_res.scalars().first()

        # 3. Vérifier Solde (Simulation: on suppose qu'il a chargé son compte via Mobile Money juste avant)
        # Dans la vraie vie, ici on appellerait l'API MTN/Airtel pour débiter le client
        # Pour ce MVP Backend, on vérifie juste le solde interne
        if client_wallet.balance < order.total_amount:
            raise HTTPException(status_code=400, detail="Solde insuffisant. Rechargez votre compte.")

        # 4. Mouvement d'argent (Atomic)
        client_wallet.balance -= order.total_amount
        client_wallet.frozen_balance += order.total_amount # L'argent reste chez le client mais est bloqué
        # Alternative : Transférer vers un Wallet KoCo Escrow central.
        
        order.status = OrderStatus.FUNDED
        await db.commit()
        await db.refresh(order)
        return order

    @staticmethod
    async def release_funds(db: AsyncSession, order_id: int, client_id: int):
        """Le client valide -> L'artisan reçoit l'argent"""
        result = await db.execute(select(Order).where(Order.id == order_id))
        order = result.scalars().first()

        if not order or order.client_id != client_id:
            raise HTTPException(status_code=403, detail="Non autorisé")
        
        if order.status != OrderStatus.FUNDED and order.status != OrderStatus.DELIVERED:
            raise HTTPException(status_code=400, detail="Statut incorrect pour libération")

        # Récupérer les Wallets
        c_res = await db.execute(select(Wallet).where(Wallet.user_id == order.client_id))
        client_wallet = c_res.scalars().first()
        
        p_res = await db.execute(select(Wallet).where(Wallet.user_id == order.partner_id))
        partner_wallet = p_res.scalars().first()

        # Libération
        amount = order.total_amount
        commission = int(amount * 0.05) # 5% Comm
        net_pay = amount - commission

        client_wallet.frozen_balance -= amount # On débloque
        partner_wallet.balance += net_pay      # On paie l'artisan
        
        # Le Wallet Admin prendrait la commission ici (non implémenté pour simplicité)

        order.status = OrderStatus.COMPLETED
        await db.commit()
        await db.refresh(order)
        return order