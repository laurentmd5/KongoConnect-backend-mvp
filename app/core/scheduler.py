from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.jobs.auto_release_job import job_send_reminders, job_auto_release
import logging

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service centralisant la gestion du scheduler APScheduler"""
    
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
    
    def start(self):
        """Démarrer le scheduler avec tous les jobs"""
        try:
            # Job 1: Envoyer les rappels (toutes les 6 heures)
            self.scheduler.add_job(
                job_send_reminders,
                trigger=IntervalTrigger(hours=6),
                id='job_send_reminders',
                name='Envoyer rappels J+1, J+3, J+5',
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            logger.info("✅ Job 'send_reminders' ajouté (toutes les 6h)")
            
            # Job 2: Débloquer les fonds après 48h (toutes les heures)
            self.scheduler.add_job(
                job_auto_release,
                trigger=IntervalTrigger(hours=1),
                id='job_auto_release',
                name='Débloquer fonds après 48h',
                replace_existing=True,
                max_instances=1,
                coalesce=True
            )
            logger.info("✅ Job 'auto_release' ajouté (toutes les 1h)")
            
            # Démarrer le scheduler
            self.scheduler.start()
            logger.info("🚀 SchedulerService démarré avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du démarrage du Scheduler: {e}")
            raise
    
    def stop(self):
        """Arrêter le scheduler proprement"""
        try:
            if self.scheduler.running:
                self.scheduler.shutdown(wait=False)
                logger.info("🛑 SchedulerService arrêté")
        except Exception as e:
            logger.error(f"❌ Erreur lors de l'arrêt du Scheduler: {e}")
    
    def get_job(self, job_id: str):
        """Récupérer un job par ID"""
        return self.scheduler.get_job(job_id)
    
    def pause_job(self, job_id: str):
        """Mettre en pause un job"""
        job = self.get_job(job_id)
        if job:
            job.pause()
            logger.info(f"⏸️  Job {job_id} mis en pause")
    
    def resume_job(self, job_id: str):
        """Reprendre un job en pause"""
        job = self.get_job(job_id)
        if job:
            job.resume()
            logger.info(f"▶️  Job {job_id} repris")


# Instance globale
scheduler_service = SchedulerService()