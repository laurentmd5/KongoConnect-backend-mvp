"""
NotificationService - Envoyer des notifications SMS/WhatsApp

Pour l'MVP: Simple logging (prêt pour Twilio/AWS SNS plus tard)
"""

import logging

logger = logging.getLogger(__name__)


class NotificationService:
    """Service centralisé pour toutes les notifications"""
    
    @staticmethod
    async def send_reminder(user_id: int, message: str, reminder_type: str):
        """
        Envoyer un rappel (J+1, J+3, J+5)
        
        Args:
            user_id: ID de l'utilisateur (artisan) recevant le rappel
            message: Contenu du message
            reminder_type: Type ('REMINDER_1', 'REMINDER_2', 'REMINDER_FINAL')
        
        TODO: Intégrer avec provider SMS:
            - Twilio
            - AWS SNS
            - Vonage
        """
        logger.info(f"📱 [{reminder_type}] Utilisateur {user_id}: {message}")
    
    @staticmethod
    async def send_payment_notification(user_id: int, amount: int, order_id: int, currency: str = "FCFA"):
        """
        Notifier qu'un paiement a été reçu et bloqué en escrow
        """
        message = f"💳 {amount} {currency} bloqués pour commande #{order_id}"
        logger.info(f"📱 Utilisateur {user_id}: {message}")
    
    @staticmethod
    async def send_completion_notification(user_id: int, amount: int, order_id: int, currency: str = "FCFA"):
        """
        Notifier que les fonds ont été débloqués et transférés
        """
        message = f"✅ {amount} {currency} crédités (commande #{order_id} complétée)"
        logger.info(f"📱 Utilisateur {user_id}: {message}")
    
    @staticmethod
    async def send_dispute_notification(user_id: int, order_id: int, reason: str):
        """
        Notifier qu'un litige a été soulevé
        """
        message = f"🚨 Litige sur commande #{order_id}: {reason}"
        logger.info(f"📱 Utilisateur {user_id}: {message}")
    
    @staticmethod
    async def send_refund_notification(user_id: int, amount: int, order_id: int, currency: str = "FCFA"):
        """
        Notifier d'un remboursement
        """
        message = f"💰 {amount} {currency} remboursés (commande #{order_id})"
        logger.info(f"📱 Utilisateur {user_id}: {message}")
    
    @staticmethod
    async def send_excessive_balance_warning(user_id: int, amount: int, currency: str = "FCFA"):
        """
        Notifier que le solde disponible est excessif (> 7 jours).
        Encourager le retrait pour conformité légale.
        """
        message = f"⚠️  Vous avez {amount} {currency} disponibles. Veuillez retirer (compliance BEAC)"
        logger.info(f"📱 Utilisateur {user_id}: {message}")