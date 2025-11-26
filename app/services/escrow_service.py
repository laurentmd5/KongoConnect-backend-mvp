from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.order import Order, OrderStatus
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.models.escrow_account import EscrowAccount, EscrowStatus # NOUVEAU
import math

class EscrowService:

    COMMISSION_RATE = 0.05 # 5% de commission KoCo

    @staticmethod
    async def accept_order(db: AsyncSession, order_id: int, partner_id: int):
        """L'artisan accepte la commande (PENDING -> ACCEPTED)."""
        order = await db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Commande introuvable")
        if order.partner_id != partner_id:
            raise HTTPException(status_code=403, detail="Non autorisé")
        if order.status != OrderStatus.PENDING:
            raise HTTPException(status_code=400, detail="Statut invalide pour acceptation.")

        order.status = OrderStatus.ACCEPTED
        await db.commit()
        return {"status": "Commande acceptée. En attente de paiement du client.", "new_status": "ACCEPTED"}

    @staticmethod
    async def lock_funds(db: AsyncSession, order_id: int, client_id: int):
        """
        Bloque les fonds en créant un EscrowAccount.
        NOTE: Utilise des entiers (FCFA) pour la comptabilité d'entiercement.
        """
        order = await db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Commande introuvable")
        if order.client_id != client_id:
            raise HTTPException(status_code=403, detail="Non autorisé")
        
        # Le paiement ne doit être accepté que si la commande est ACCEPTED (ou FUNDED si re-appel)
        if order.status not in [OrderStatus.ACCEPTED, OrderStatus.FUNDED]:
             raise HTTPException(status_code=400, detail=f"Statut invalide pour paiement: {order.status.value}.")

        # Si déjà FUNDED, pas de re-débit
        if order.status == OrderStatus.FUNDED:
             return {"status": "Fonds déjà sécurisés", "new_status": "FUNDED"}
        
        # Le montant total est en Float dans l'Order model, 
        # mais on le convertit en entier FCFA pour Escrow.
        amount_float = order.total_amount
        amount_int = int(round(amount_float)) # Montant total FCFA (entier)
        
        commission = int(round(amount_float * EscrowService.COMMISSION_RATE))
        net_pay = amount_int - commission

        # 1. Vérif Solde Client
        q_client = await db.execute(select(Wallet).where(Wallet.user_id == client_id))
        client_wallet = q_client.scalars().first()

        # On vérifie le solde en FCFA (int)
        if not client_wallet or client_wallet.balance < amount_int: 
            raise HTTPException(status_code=400, detail="Solde insuffisant. Veuillez recharger.")

        # --- FLUX ATOMIQUE CRITIQUE ---
        
        # 2. Débiter client (utilise l'entier)
        client_wallet.balance -= amount_int
        
        # 3. Créer l'EscrowAccount avec les entiers
        escrow = EscrowAccount(
            order_id=order.id,
            amount=amount_int,
            commission_amount=commission,
            artisan_payout=net_pay,
            status=EscrowStatus.LOCKED,
            locked_at=datetime.utcnow()
        )
        db.add(escrow)

        # 4. Marquer commande FUNDED + Timestamps
        order.status = OrderStatus.FUNDED
        order.funded_at = datetime.utcnow()
        order.commission_amount = commission # Optionnel: stocker aussi la commission dans Order (Float vs Int)

        # 5. Trace (Débit client)
        tx = Transaction(
            wallet_id=client_wallet.id,
            order_id=order.id,
            # Le montant de transaction doit aussi être un entier négatif
            amount=-amount_int, 
            type="ESCROW_LOCK",
            reference=f"ORD-{order.id}-LOCK"
        )
        db.add(tx)
        
        await db.commit()
        return {"status": "Fonds sécurisés en escrow", "new_status": "FUNDED", "escrow_id": escrow.id, "amount_locked": amount_int}

    @staticmethod
    async def start_work(db: AsyncSession, order_id: int, partner_id: int):
        """L'artisan démarre le travail (FUNDED -> IN_PROGRESS)."""
        order = await db.get(Order, order_id)
        if not order:
            raise HTTPException(status_code=404, detail="Commande introuvable")
        if order.partner_id != partner_id:
            raise HTTPException(status_code=403, detail="Non autorisé")
        
        if order.status != OrderStatus.FUNDED:
            raise HTTPException(status_code=400, detail=f"Statut invalide: {order.status.value}. Doit être FUNDED pour démarrer le travail.")

        order.status = OrderStatus.IN_PROGRESS
        await db.commit()
        return {"status": "Travail en cours.", "new_status": "IN_PROGRESS"}


    @staticmethod
    async def declare_job_finished(db: AsyncSession, order_id: int, partner_id: int):
        """L'artisan déclare avoir fini. Le chrono 48h démarre."""
        order = await db.get(Order, order_id)

        if not order:
            raise HTTPException(status_code=404, detail="Commande introuvable")
        if order.partner_id != partner_id:
            raise HTTPException(status_code=403, detail="Non autorisé")

        valid_statuses = [OrderStatus.IN_PROGRESS, OrderStatus.FUNDED, OrderStatus.ACCEPTED]
        if order.status not in valid_statuses:
             raise HTTPException(status_code=400, detail=f"Statut invalide ({order.status.value}). Doit être {', '.join([s.value for s in valid_statuses])}.")

        order.status = OrderStatus.DELIVERED
        order.delivered_at = datetime.utcnow() # Timestamp critique

        await db.commit()
        return {"status": "Travail déclaré fini. Validation client attendue sous 48h."}

    @staticmethod
    async def release_funds(db: AsyncSession, order_id: int, trigger_source: str = "CLIENT"):
        """
        Libération des fonds du compte Escrow vers l'artisan.
        """
        order = await db.get(Order, order_id)
        # Utiliser `order.escrow_account` si la relation est bien configurée, 
        # sinon requête explicite:
        q_escrow = await db.execute(select(EscrowAccount).where(EscrowAccount.order_id == order_id))
        escrow = q_escrow.scalars().first()
        
        if not order or not escrow:
            raise HTTPException(status_code=404, detail="Commande ou Escrow introuvable")

        valid_release_statuses = [
            OrderStatus.DELIVERED, 
            OrderStatus.REMINDER_1, 
            OrderStatus.REMINDER_2, 
            OrderStatus.REMINDER_FINAL
        ]
        
        if order.status not in valid_release_statuses:
            raise HTTPException(status_code=400, detail=f"Libération impossible: statut invalide ({order.status.value}).")

        if escrow.status != EscrowStatus.LOCKED:
             raise HTTPException(status_code=400, detail=f"Fonds déjà libérés ou autre état Escrow: {escrow.status.value}.")

        # Récupération du wallet partenaire
        q_partner = await db.execute(select(Wallet).where(Wallet.user_id == order.partner_id))
        partner_wallet = q_partner.scalars().first()
        
        # --- FLUX ATOMIQUE CRITIQUE DE LIBÉRATION ---
        
        # 1. On crédite l'artisan (Net - Entier)
        net_pay = escrow.artisan_payout
        
        # Vérif existence wallet
        if not partner_wallet:
            raise HTTPException(status_code=500, detail="Portefeuille artisan introuvable.")

        partner_wallet.balance += net_pay

        # 2. Mise à jour de l'EscrowAccount
        escrow.status = EscrowStatus.RELEASED
        escrow.released_at = datetime.utcnow()
        escrow.released_by = trigger_source # Utilise le champ Audit

        # 3. Mise à jour de l'Order
        order.status = OrderStatus.COMPLETED
        order.completed_at = datetime.utcnow()
        order.commission_amount = escrow.commission_amount # Copie de l'entier

        # 4. Trace Artisan (Crédit - Entier)
        tx_pay = Transaction(
            wallet_id=partner_wallet.id,
            order_id=order.id,
            amount=net_pay,
            type="ESCROW_RELEASE",
            description=f"Paiement reçu (Source: {trigger_source})"
        )
        db.add(tx_pay)
        
        await db.commit()
        return {"status": "Fonds libérés", "amount_paid": net_pay, "commission": escrow.commission_amount}