from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

# NOTE: Les chemins d'importation sont déduits de la structure du projet (README.md)
# et pourraient nécessiter des ajustements mineurs.
from infrastructure.database import get_db_session
from domain.entities import EspaceVertEntity, UserEntity
# Le snippet mentionnait `from auth import ...`. Un emplacement commun est un dossier de dépendances.
from api.deps.auth import require_any_role
from schema.espaces_verts import EspaceVert # Basé sur README: schemas/espaces_verts.py

router = APIRouter()

def _creer_zones_intelligentes(db: Session, user_id: int, max_zones: int) -> List[EspaceVertEntity]:
    """
    Logique de récupération des "zones intelligentes" (espaces verts) pour un utilisateur.

    Cette fonction récupère les espaces verts associés à l'ID de l'utilisateur depuis la base de données.
    """
    return db.query(EspaceVertEntity).filter(EspaceVertEntity.user_id == user_id).limit(max_zones).all()


@router.get(
    "/api/v1/zones/intelligentes",
    response_model=List[EspaceVert],
    summary="Récupérer les zones intelligentes de l'utilisateur",
    tags=["Zones Intelligentes"]
)
async def zones_intelligentes(
    max_zones: int = Query(8, ge=1, le=12, description="Nombre maximum de zones à retourner."),
    current_user: UserEntity = Depends(require_any_role(["admin", "user"])),
    db: Session = Depends(get_db_session),
):
    """
    Récupère une liste de "zones intelligentes" (espaces verts) pour l'utilisateur authentifié.

    Cette route est protégée par authentification JWT. Pour l'utiliser, vous devez fournir un token valide
    dans l'en-tête `Authorization` sous la forme `Bearer <votre_token>`.
    """
    # On utilise `current_user.id` venant du token pour une requête sécurisée et dynamique.
    zones = _creer_zones_intelligentes(db, current_user.id, max_zones)
    return zones