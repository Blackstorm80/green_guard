# back_end/api/v1/endpoints/vegetal.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from api.deps.auth import exiger_role
from application.dto.vegetal import EtatGlobalVegetalDTO, ImpactCarboneDTO
from application.use_cases.vegetal import calculer_etat_global_vegetal, calculer_impact_carbone
from domain.logic.droits import ROLES_GESTION
from domain.models import User
from infrastructure.database import get_db
from infrastructure.repositories.bilan_hydrique_repository_impl import BilanHydriqueRepositoryImpl
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl

router = APIRouter()
gestionnaire = exiger_role(*ROLES_GESTION)

def get_repos(db: Session = Depends(get_db)):
    return {
        "espace_repo": EspaceVertRepositoryImpl(db),
        "bilan_repo": BilanHydriqueRepositoryImpl(db)
    }

@router.get("/etat-global", response_model=EtatGlobalVegetalDTO)
def get_etat_global(
    repos: dict = Depends(get_repos),
    current_user: User = Depends(gestionnaire),
):
    """
    Retourne les indicateurs de santé globale du patrimoine de l'organisation.
    """
    return calculer_etat_global_vegetal(
        organisation_id=current_user.organisation_id,
        espace_repo=repos["espace_repo"],
        bilan_repo=repos["bilan_repo"]
    )

@router.get("/impact-carbone", response_model=ImpactCarboneDTO)
def get_impact_carbone(
    repos: dict = Depends(get_repos),
    current_user: User = Depends(gestionnaire),
):
    """
    Retourne l'estimation de l'impact écologique (O2 produit, CO2 absorbé) de l'organisation.
    """
    return calculer_impact_carbone(
        organisation_id=current_user.organisation_id,
        espace_repo=repos["espace_repo"],
        bilan_repo=repos["bilan_repo"]
    )
