from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from infrastructure.database import engine, Base
from domain import models
from apscheduler.schedulers.background import BackgroundScheduler
from infrastructure.services.capteur_hybrid_service import run_update

# Création des tables au lancement
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Green Guard API")

# Configuration CORS pour React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Imports des routers
from api.v1.endpoints import (
    espaces_verts, zones, user, auth, capteurs, vegetal, 
    meteo, plants, catalogue, interventions, health, notifications
)

# Branchement des routes
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(user.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(espaces_verts.router, prefix="/api/v1/espaces-verts", tags=["Espaces Verts"])
app.include_router(zones.router, prefix="/api/v1/zones", tags=["Zones Intelligentes"])
app.include_router(capteurs.router, prefix="/api/v1/capteurs", tags=["Capteurs"])
app.include_router(catalogue.router, prefix="/api/v1/catalogue", tags=["Catalogue Botanique"])
app.include_router(interventions.router, prefix="/api/v1/interventions", tags=["Interventions"])
app.include_router(notifications.router, prefix="/api/v1/notifications", tags=["Notifications"])
app.include_router(meteo.router, prefix="/api/v1/meteo", tags=["Météo"])
app.include_router(plants.router, prefix="/api/v1/plants", tags=["Plants"])
app.include_router(vegetal.router, prefix="/api/v1/vegetal", tags=["Végétal"])
app.include_router(health.router, prefix="/api/v1/health", tags=["Health"])

scheduler = BackgroundScheduler()

@app.on_event("startup")
def startup_event():
    # 2. On programme la mise à jour (ex: toutes les 30 minutes)
    # Pour tes tests, tu peux mettre minutes=1 pour voir les changements vite
    scheduler.add_job(run_update, "interval", minutes=2)
    
    # 3. On lance le moteur
    scheduler.start()
    print("SYSTÈME DE SIMULATION ACTIF (Le coeur bat) ")

@app.on_event("shutdown")
def shutdown_event():
    # On arrête proprement le moteur quand on coupe le serveur
    scheduler.shutdown()

@app.get("/")
def health():
    return {"status": "online", "project": "Green Guard"}