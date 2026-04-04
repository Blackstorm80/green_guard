# back_end/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.v1.endpoints import meteo, vegetal, capteurs, auth, user, interventions, zones
# Vous pourrez ajouter d'autres routeurs ici (ex: gestion_espaces_verts)
from infrastructure.database import Base, engine

app = FastAPI(
    title="Green Guard API",
    description="API pour la gestion des espaces verts et le calcul de bilan hydrique.",
    version="1.0.0",
)

# Configuration CORS : Permet au frontend (ex: localhost:3000) de discuter avec le backend
origins = [
    "http://localhost:3000",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    # Création des tables au démarrage de l'application.
    # C'est la manière non-bloquante de le faire.
    Base.metadata.create_all(bind=engine)

@app.get("/ping")
def ping():
    return {"status": "ok"}

# Inclusion des routeurs
# Le problème de blocage étant résolu, nous pouvons réactiver tous les routeurs.
app.include_router(meteo.router, prefix="/api/v1")
app.include_router(vegetal.router, prefix="/api/v1")
app.include_router(capteurs.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(interventions.router, prefix="/api/v1")
app.include_router(zones.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API Green Guard !"}