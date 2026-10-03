from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from api.deps.auth import get_current_user, require_any_role
from application.use_cases.zones import reconstruire_zones
from domain.logic.clustering import calculer_couleur_gauge
from domain.models import User, ZoneIntelligente
from infrastructure.database import get_db
from schema.zones import ReconstructionZonesRead, ZoneIntelligenteRead

router = APIRouter()


@router.post("/clustering/rebuild", response_model=ReconstructionZonesRead, status_code=status.HTTP_201_CREATED)
def rebuild_zones(
    current_user: User = Depends(require_any_role(["admin", "manager", "user"])),
    db: Session = Depends(get_db),
):
    """Recalcule les zones intelligentes de l'utilisateur à partir de ses espaces."""
    try:
        zones = reconstruire_zones(db, user_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e)) from e
    return {"message": f"{len(zones)} zone(s) intelligente(s) recalculée(s).", "zones": [z.nom for z in zones]}


@router.get("/", response_model=list[ZoneIntelligenteRead])
def lister_zones(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Zones intelligentes de l'utilisateur, prêtes à afficher."""
    zones = (
        db.query(ZoneIntelligente)
        .filter(ZoneIntelligente.user_id == current_user.id)
        .order_by(ZoneIntelligente.id)
        .all()
    )
    return [
        ZoneIntelligenteRead(
            id=z.id,
            nom=z.nom,
            sante_moyenne=z.sante_moyenne,
            nb_espaces=z.nb_espaces,
            centroid_lat=z.centroid_lat,
            centroid_lon=z.centroid_lon,
            rayon_km=z.rayon_km,
            granularite=z.granularite,
            couleur_gauge=calculer_couleur_gauge(z.sante_moyenne),
        )
        for z in zones
    ]
