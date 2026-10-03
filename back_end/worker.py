"""Service worker (ADR-5) : exécute les tâches planifiées hors du processus API.

Lancement : `python worker.py` (service `worker` de docker-compose).
Un seul worker doit tourner : les API peuvent ainsi passer à plusieurs instances
sans exécuter le job en double.
"""
import logging

from apscheduler.schedulers.blocking import BlockingScheduler

from config import settings
from infrastructure.jobs.mise_a_jour_capteurs import INTERVALLE_MINUTES, run_update
from infrastructure.logging_config import configurer_logs

logger = logging.getLogger("greenguard.worker")


def main() -> None:
    configurer_logs(settings.log_level, settings.log_format)
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(run_update, "interval", minutes=INTERVALLE_MINUTES, id="mise_a_jour_capteurs",
                      max_instances=1, coalesce=True)
    logger.info("Worker démarré : premier passage immédiat, puis toutes les %d min.", INTERVALLE_MINUTES)
    run_update()
    scheduler.start()


if __name__ == "__main__":
    main()
