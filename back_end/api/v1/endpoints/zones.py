from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from application.dto.zone_intelligente import ZoneIntelligenteDTO
from application.dto.user import UserDTO
from infrastructure.database import get_db_session
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl
from domain.ports.espace_vert_repository import IEspaceVertRepository
from application.use_cases.zones_intelligentes import creer_zones_intelligentes
from api.deps.auth import get_current_user

router = APIRouter(prefix="/zones", tags=["zones intelligentes"])

@router.get("/intelligentes", response_model=List[ZoneIntelligenteDTO])
async def zones_intelligentes(
    max_zones: int = Query(8, ge=1, le=12, description="Nombre max de zones à afficher"),
    current_user: UserDTO = Depends(get_current_user),
    db: Session = Depends(get_db_session),
):
    """
    Clustering dynamique complet avec K-Means
    
    **Logique automatique** :
    - &lt;5 espaces → 1 zone globale
    - 5-15 → par ville  
    - 16-50 → par quartier (2km rayon)
    - >50 → K-Means
    """
    repo: IEspaceVertRepository = EspaceVertRepositoryImpl(db)
    zones = creer_zones_intelligentes(repo, current_user.id, max_zones)
    return zones