# back_end/api/v1/endpoints/vegetal.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from infrastructure.database import get_db_session
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl
from infrastructure.repositories.bilan_hydrique_repository_impl import BilanHydriqueRepositoryImpl
from application.use_cases.vegetal import calculer_etat_global_vegetal, calculer_impact_carbone
from application.dto.vegetal import EtatGlobalVegetalDTO, ImpactCarboneDTO

router = APIRouter(prefix="/vegetal", tags=["Indicateurs Végétaux"])

def get_repos(db: Session = Depends(get_db_session)):
    return {
        "espace_repo": EspaceVertRepositoryImpl(db),
        "bilan_repo": BilanHydriqueRepositoryImpl(db)
    }

@router.get("/etat-global", response_model=EtatGlobalVegetalDTO)
def get_etat_global(
    repos: dict = Depends(get_repos)
):
    """
    Retourne les indicateurs de santé globale du parc (pour le dashboard).
    """
    return calculer_etat_global_vegetal(
        espace_repo=repos["espace_repo"],
        bilan_repo=repos["bilan_repo"]
    )

@router.get("/impact-carbone", response_model=ImpactCarboneDTO)
def get_impact_carbone(
    repos: dict = Depends(get_repos)
):
    """
    Retourne l'estimation de l'impact écologique (O2 produit, CO2 absorbé).
    """
    return calculer_impact_carbone(
        espace_repo=repos["espace_repo"],
        bilan_repo=repos["bilan_repo"]
    )
