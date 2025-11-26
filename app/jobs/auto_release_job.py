from datetime import datetime, timedelta
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.session import AsyncSessionLocal
from app.models.order import Order, OrderStatus
from app.models.escrow_account import EscrowAccount, EscrowStatus
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.services.escrow_service import EscrowService

logger = logging.getLogger(__name__)

async def job_send_reminders():
    """
    Envoie les rappels aux clients pour validation des travaux.
    Statuts: DELIVERED -> REMINDER_1 -> REMINDER_2 -> REMINDER_FINAL
    """
    async with AsyncSessionLocal() as db:
        try:
            # Commandes en attente de validation depuis plus de 24h
            reminder_1_cutoff = datetime.utcnow() - timedelta(hours=24)
            reminder_2_cutoff = datetime.utcnow() - timedelta(hours=36)  
            reminder_final_cutoff = datetime.utcnow() - timedelta(hours=47)

            # 🔔 Rappel 1 (24h)
            orders_reminder_1 = await db.execute(
                select(Order).where(
                    and_(
                        Order.status == OrderStatus.DELIVERED,
                        Order.delivered_at <= reminder_1_cutoff,
                        Order.reminder_1_sent_at.is_(None)
                    )
                )
            )
            
            for order in orders_reminder_1.scalars().all():
                order.status = OrderStatus.REMINDER_1
                order.reminder_1_sent_at = datetime.utcnow()
                logger.info(f"🔔 Rappel 1 envoyé pour commande #{order.id}")

            # 🔔🔔 Rappel 2 (36h)  
            orders_reminder_2 = await db.execute(
                select(Order).where(
                    and_(
                        Order.status == OrderStatus.REMINDER_1,
                        Order.delivered_at <= reminder_2_cutoff,
                        Order.reminder_2_sent_at.is_(None)
                    )
                )
            )
            
            for order in orders_reminder_2.scalars().all():
                order.status = OrderStatus.REMINDER_2
                order.reminder_2_sent_at = datetime.utcnow()
                logger.info(f"🔔🔔 Rappel 2 envoyé pour commande #{order.id}")

            # 🔔🔔🔔 Rappel Final (47h)
            orders_reminder_final = await db.execute(
                select(Order).where(
                    and_(
                        Order.status == OrderStatus.REMINDER_2,
                        Order.delivered_at <= reminder_final_cutoff,
                        Order.reminder_final_sent_at.is_(None)
                    )
                )
            )
            
            for order in orders_reminder_final.scalars().all():
                order.status = OrderStatus.REMINDER_FINAL
                order.reminder_final_sent_at = datetime.utcnow()
                logger.info(f"🔔🔔🔔 Rappel FINAL envoyé pour commande #{order.id}")

            await db.commit()
            logger.info("✅ Tous les rappels traités avec succès")

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Erreur lors de l'envoi des rappels: {e}")

async def job_auto_release():
    """
    Libération automatique des fonds après 48h pour les commandes validées
    par le système (artisan a déclaré fini, client n'a pas répondu).
    """
    async with AsyncSessionLocal() as db:
        try:
            # Commandes éligibles à l'auto-release
            auto_release_cutoff = datetime.utcnow() - timedelta(hours=48)
            
            eligible_orders = await db.execute(
                select(Order).where(
                    and_(
                        Order.status.in_([
                            OrderStatus.DELIVERED,
                            OrderStatus.REMINDER_1, 
                            OrderStatus.REMINDER_2,
                            OrderStatus.REMINDER_FINAL
                        ]),
                        Order.delivered_at <= auto_release_cutoff
                    )
                )
            )

            released_count = 0
            for order in eligible_orders.scalars().all():
                try:
                    # ✅ CORRECTION : Utiliser directement EscrowService
                    # Plus de manipulation de frozen_balance !
                    result = await EscrowService.release_funds(
                        db, order.id, trigger_source="AUTO_RELEASE"
                    )
                    
                    released_count += 1
                    logger.info(f"✅ Auto-release réussie pour commande #{order.id}: {result}")
                    
                except Exception as e:
                    logger.error(f"❌ Erreur auto-release commande #{order.id}: {e}")
                    continue

            await db.commit()
            logger.info(f"🎉 Auto-release terminée: {released_count} commandes traitées")

        except Exception as e:
            await db.rollback()
            logger.error(f"❌ Erreur critique dans job_auto_release: {e}")