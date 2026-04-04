from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from infrastructure.database import get_db_session
from domain.entities import UserEntity
from domain.entities.zone_intelligente import ZoneIntelligenteEntity
from api.deps.auth import require_any_role
from domain.logic.clustering import executer_clustering_intelligent, calculer_couleur_gauge
from schema.zones import ZoneIntelligenteRead

router = APIRouter()

@router.post(
    "/clustering/rebuild",
    summary="Lancer le recalcul des zones intelligentes",
    status_code=status.HTTP_201_CREATED,
    tags=["Zones Intelligentes"]
)
async def rebuild_zones(
    current_user: UserEntity = Depends(require_any_role(["admin", "manager"])),
    db: Session = Depends(get_db_session)
):
    """
    Lance le recalcul complet des zones intelligentes pour le  authentifié et verifier.
    le code en haut  supprime les anciennes zones et en crée de nouvelles basées sur la configuration du user dans les parametres.

    **Accès :** seulement si role= manager ou admin .
    """
    try:
        zones = executer_clustering_intelligent(db, user_id=current_user.id)
        return {"message": f"{len(zones)} zones intelligentes ont été créées/mises à jour.", "zones": [z.nom for z in zones]}
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

@router.get(
    "/zones",
    response_model=List[ZoneIntelligenteRead],
    summary="Lister les zones intelligentes du user connecter",
    tags=["Zones Intelligentes"]
)
async def lister_zones(
    current_user: UserEntity = Depends(require_any_role(["admin", "user"])),
    db: Session = Depends(get_db_session),
):
    """
    Récupère la liste des zones intelligentes pour le user  authen,
    avec des données prêtes à être affichées .
    """
    zones = db.query(ZoneIntelligenteEntity).filter(ZoneIntelligenteEntity.user_id == current_user.id).all()
    zones_dto = [ZoneIntelligenteRead(**zone.__dict__, couleur_gauge=calculer_couleur_gauge(zone.sante_moyenne)) for zone in zones]
    return zones_dto

    """Cette route est protégée par auth JWT. Pour l'utiliser,il faut verifier si le user est authen avec sont token 
    """
    # On utilise `current_user.id` venant du token pour une requête sécurisée et dynamique.
    zones = _creer_zones_intelligentes(db, current_user.id, max_zones)
    return zones