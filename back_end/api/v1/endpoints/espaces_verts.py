from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from api.deps.auth import exiger_role, get_current_user
from api.v1.endpoints.meteo import ERREUR_METEO, get_meteo_service
from application.dto.prevision import PrevisionDTO
from application.use_cases.bilans_hydriques import historique_des_bilans
from application.use_cases.prevision import prevision_de_l_espace
from application.use_cases.secheresse import evaluer_espace, restrictions_en_vigueur
from config import settings
from domain import models
from domain.logic.droits import ROLES_GESTION
from domain.logic.prevision import PrevisionImpossibleError, PrevisionMeteoIncompleteError
from domain.logic.secheresse import regles_depuis_parametres
from domain.ports.meteo import IMeteoService, MeteoIndisponibleError
from infrastructure.database import get_db
from infrastructure.repositories.bilan_hydrique_repository_impl import BilanHydriqueRepositoryImpl
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl
from infrastructure.repositories.restriction_secheresse_repository_impl import RestrictionSecheresseRepositoryImpl
from schema.bilans_hydriques import BilanHydriqueRead
from schema.espaces_verts import EspaceVertCreate, EspaceVertRead, EspaceVertUpdate

router = APIRouter()
gestionnaire = exiger_role(*ROLES_GESTION)


def _espace_de_l_organisation(espace_id: int, db: Session, user: models.User) -> models.EspaceVert:
    """404 aussi bien pour un espace inexistant que pour celui d'une autre organisation (pas de fuite d'existence)."""
    espace = EspaceVertRepositoryImpl(db).get_pour_organisation(espace_id, user.organisation_id)
    if espace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Espace vert introuvable")
    return espace


@router.get("/", response_model=list[EspaceVertRead])
def get_espaces_verts(db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)):
    """Patrimoine de l'organisation de l'utilisateur connecté."""
    return EspaceVertRepositoryImpl(db).list_par_organisation(current_user.organisation_id)


@router.post("/", response_model=EspaceVertRead, status_code=status.HTTP_201_CREATED)
def create_espace_vert(
    espace_data: EspaceVertCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(gestionnaire),
):
    """Crée un espace vert dans l'organisation de l'utilisateur connecté."""
    espace = models.EspaceVert(**espace_data.model_dump(exclude_none=True),
                               organisation_id=current_user.organisation_id, cree_par=current_user.id)
    return EspaceVertRepositoryImpl(db).save(espace)


@router.get("/{espace_id}", response_model=EspaceVertRead)
def get_espace_vert(
    espace_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(get_current_user)
):
    return _espace_de_l_organisation(espace_id, db, current_user)


@router.get("/{espace_id}/bilans", response_model=list[BilanHydriqueRead])
def get_bilans_espace_vert(
    espace_id: int,
    jours: int = Query(30, ge=1, le=365, description="Profondeur de l'historique en jours (aujourd'hui compris)."),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """Historique des bilans hydriques et de leurs termes, par date croissante."""
    espace = _espace_de_l_organisation(espace_id, db, current_user)
    aujourd_hui = datetime.now(settings.fuseau).date()
    return historique_des_bilans(espace.id, jours, aujourd_hui, BilanHydriqueRepositoryImpl(db))


@router.get("/{espace_id}/prevision", response_model=PrevisionDTO)
def get_prevision_espace_vert(
    espace_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
    meteo_service: IMeteoService = Depends(get_meteo_service),
):
    """Réserve projetée de J à J+7, dates de bascule et décision (arroser, reporter, surveiller, rien,
    ou interdit sous restriction sécheresse)."""
    espace = _espace_de_l_organisation(espace_id, db, current_user)
    aujourd_hui = datetime.now(settings.fuseau).date()
    restriction = restrictions_en_vigueur([espace.id], aujourd_hui, RestrictionSecheresseRepositoryImpl(db))
    evaluation = evaluer_espace(espace, restriction.get(espace.id),
                                regles_depuis_parametres(current_user.organisation.parametres), aujourd_hui)
    try:
        return prevision_de_l_espace(espace, BilanHydriqueRepositoryImpl(db), meteo_service, settings.fuseau,
                                     evaluation=evaluation)
    except (MeteoIndisponibleError, PrevisionMeteoIncompleteError):
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=ERREUR_METEO) from None
    except PrevisionImpossibleError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Prévision indisponible : aucun bilan hydrique récent pour cet espace (calculé à chaque heure).",
        ) from None


@router.put("/{espace_id}", response_model=EspaceVertRead)
def update_espace_vert(
    espace_id: int,
    espace_data: EspaceVertUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(gestionnaire),
):
    """Mise à jour partielle : seuls les champs envoyés sont modifiés."""
    espace = _espace_de_l_organisation(espace_id, db, current_user)
    for key, value in espace_data.model_dump(exclude_unset=True).items():
        setattr(espace, key, value)
    return EspaceVertRepositoryImpl(db).save(espace)


@router.delete("/{espace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_espace_vert(
    espace_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(gestionnaire)
):
    espace = _espace_de_l_organisation(espace_id, db, current_user)
    db.delete(espace)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
