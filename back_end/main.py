import logging
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.deps.auth import EN_TETE_CSRF
from api.middleware import installer_middlewares
from api.v1.endpoints import (
    auth,
    capteurs,
    catalogue,
    espaces_verts,
    health,
    interventions,
    meteo,
    notifications,
    user,
    vegetal,
    zones,
)
from config import settings
from infrastructure.jobs.mise_a_jour_capteurs import INTERVALLE_MINUTES, run_update
from infrastructure.logging_config import configurer_logs

configurer_logs(settings.log_level, settings.log_format)
logger = logging.getLogger("greenguard")

# Le schéma de la base est géré exclusivement par Alembic (`alembic upgrade head`).
# Les tâches planifiées tournent dans le service worker (worker.py) ; ENABLE_SCHEDULER=true
# ne sert qu'au développement local sans worker.


@asynccontextmanager
async def lifespan(_: FastAPI):
    scheduler = None
    if settings.enable_scheduler:
        scheduler = BackgroundScheduler(timezone="UTC")
        scheduler.add_job(run_update, "interval", minutes=INTERVALLE_MINUTES, id="mise_a_jour_capteurs",
                          max_instances=1, coalesce=True)
        scheduler.start()
        logger.info("Scheduler intégré démarré (mode développement).")
    yield
    if scheduler:
        scheduler.shutdown()


app = FastAPI(title="GreenGuard API", version="0.9.0", lifespan=lifespan)

installer_middlewares(app)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,  # cookie de session
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", EN_TETE_CSRF],
    expose_headers=["X-Request-ID", "Retry-After"],
)

# ADR-1 : le préfixe d'un router est défini ici et nulle part ailleurs.
API = "/api/v1"
app.include_router(auth.router, prefix=f"{API}/auth", tags=["Auth"])
app.include_router(user.router, prefix=f"{API}/users", tags=["Utilisateurs"])
app.include_router(espaces_verts.router, prefix=f"{API}/espaces-verts", tags=["Espaces verts"])
app.include_router(zones.router, prefix=f"{API}/zones", tags=["Zones intelligentes"])
app.include_router(capteurs.router, prefix=f"{API}/capteurs", tags=["Capteurs"])
app.include_router(catalogue.router, prefix=f"{API}/catalogue", tags=["Catalogue botanique"])
app.include_router(interventions.router, prefix=f"{API}/interventions", tags=["Interventions"])
app.include_router(notifications.router, prefix=f"{API}/notifications", tags=["Notifications"])
app.include_router(meteo.router, prefix=f"{API}/meteo", tags=["Météo"])
app.include_router(vegetal.router, prefix=f"{API}/vegetal", tags=["Indicateurs végétaux"])
app.include_router(health.router, prefix=f"{API}/health", tags=["Santé"])


@app.get("/", include_in_schema=False)
def racine():
    return {"status": "online", "project": "GreenGuard"}
