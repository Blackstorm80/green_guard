# back_end/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from back_end.api.v1.endpoints import catalogue_plantes
# Vous pourrez ajouter d'autres routeurs ici (ex: gestion_espaces_verts)
from back_end.infrastructure.database import Base, engine

# Création des tables au démarrage (pour le dev, idéalement utiliser Alembic plus tard)
Base.metadata.create_all(bind=engine)

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

# Inclusion des routeurs
app.include_router(catalogue_plantes.router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Bienvenue sur l'API Green Guard !"}