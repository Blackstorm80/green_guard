# back_end/api/v1/endpoints/interventions.py
from fastapi import APIRouter, Depends, Query
from typing import List

from application.dto.intervention import InterventionsUrgentesDTO
from application.dto.user import UserDTO
from application.use_cases.interventions import lister_interventions_urgentes
from api.deps.auth import get_current_user
from domain.ports.capteurs import ICapteurService
from domain.ports.espace_vert_repository import IEspaceVertRepository
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl
from api.v1.endpoints.capteurs import get_capteur_service

router = APIRouter(prefix="/interventions", tags=["Interventions"])

def get_espace_repo() -> IEspaceVertRepository:
    # Retourne une implémentation "fake". Plus tard, on injectera la session DB.
    return EspaceVertRepositoryImpl()

@router.get("/urgent", response_model=InterventionsUrgentesDTO)
async def get_interventions_urgentes(
    limit: int = Query(5, ge=1, le=20, description="Nombre maximum d'interventions à retourner."),
    depuis_heures: int = Query(24, ge=1, le=168, description="Période de recherche en heures."),
    current_user: UserDTO = Depends(get_current_user),
    capteur_service: ICapteurService = Depends(get_capteur_service),
    espace_repo: IEspaceVertRepository = Depends(get_espace_repo),
):
    """Liste les interventions urgentes pour le dashboard (colonne de droite)."""
    return lister_interventions_urgentes(
        user=current_user,
        capteur_service=capteur_service,
        espace_repo=espace_repo,
        limit=limit,
        depuis_heures=depuis_heures
    )