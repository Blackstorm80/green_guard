"""Interventions : détection des urgences + CRUD (repris de feature/Lucresse-branche, sécurisé).

Boucle arrosage → bilan : toute écriture d'une intervention aligne l'apport d'eau compté dans le bilan
(application/use_cases/interventions.py), dans la même transaction, puis recalcule aussitôt le bilan.
"""
import logging
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session, selectinload

from api.deps.auth import exiger_role, get_current_user
from api.v1.endpoints.capteurs import get_capteur_service
from api.v1.endpoints.meteo import get_meteo_service
from application.dto.intervention import InterventionsUrgentesDTO
from application.use_cases.generer_bilans_hydriques_journaliers import arrosage_journalier, recalculer_bilan_espace
from application.use_cases.interventions import (
    lister_interventions_urgentes,
    retirer_action_irrigation,
    synchroniser_action_irrigation,
)
from config import settings
from domain.logic.arrosage import ArrosageNonComptableError
from domain.logic.droits import ROLES_GESTION, ROLES_INTERVENTION
from domain.models import EspaceVert, Intervention, User
from domain.ports.meteo import IMeteoService
from infrastructure.database import get_db
from infrastructure.repositories.action_irrigation_repository_impl import ActionIrrigationRepositoryImpl
from infrastructure.repositories.bilan_hydrique_repository_impl import BilanHydriqueRepositoryImpl
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl
from infrastructure.services.capteur_hybrid_service import CapteurHybridService
from schema.interventions import InterventionCreate, InterventionRead, InterventionUpdate

logger = logging.getLogger(__name__)

router = APIRouter()
intervenant = exiger_role(*ROLES_INTERVENTION)
gestionnaire = exiger_role(*ROLES_GESTION)


def _requete_organisation(db: Session, user: User):
    """Interventions limitées aux espaces de l'organisation."""
    return (
        db.query(Intervention).join(EspaceVert)
        .options(selectinload(Intervention.action_irrigation))
        .filter(EspaceVert.organisation_id == user.organisation_id)
    )


def _intervention_de_l_organisation(intervention_id: int, db: Session, user: User) -> Intervention:
    intervention = _requete_organisation(db, user).filter(Intervention.id == intervention_id).first()
    if intervention is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intervention introuvable")
    return intervention


def _recalculer(db: Session, espace: EspaceVert, depuis: date | None, meteo: IMeteoService) -> None:
    """Recalcul immédiat du bilan (météo en cache). Un échec n'annule pas l'intervention déjà validée :
    le passage horaire du worker recompte l'apport du jour."""
    if depuis is None:
        return
    try:
        recalculer_bilan_espace(
            espace, depuis, BilanHydriqueRepositoryImpl(db), meteo,
            arrosage_journalier(ActionIrrigationRepositoryImpl(db), settings.fuseau), settings.fuseau,
        )
    except Exception:
        db.rollback()
        logger.exception("Recalcul immédiat du bilan impossible pour l'espace %s.", espace.id)


def _enregistrer(db: Session, intervention: Intervention, espace: EspaceVert, meteo: IMeteoService) -> Intervention:
    db.flush()
    try:
        depuis = synchroniser_action_irrigation(intervention, espace, ActionIrrigationRepositoryImpl(db),
                                                settings.fuseau)
    except ArrosageNonComptableError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from None
    db.commit()
    _recalculer(db, espace, depuis, meteo)
    db.refresh(intervention)
    return intervention


@router.get("/urgent", response_model=InterventionsUrgentesDTO)
def get_interventions_urgentes(
    limit: int = Query(5, ge=1, le=20, description="Nombre maximum d'interventions à retourner."),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    capteur_service: CapteurHybridService = Depends(get_capteur_service),
):
    """Interventions urgentes pour le dashboard."""
    espaces = EspaceVertRepositoryImpl(db).list_resume_par_organisation(current_user.organisation_id)
    return lister_interventions_urgentes(espaces=espaces, capteur_service=capteur_service, limit=limit)


@router.get("/", response_model=list[InterventionRead])
def lister_interventions(
    espace_id: int | None = Query(None, description="Filtrer sur un espace"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = _requete_organisation(db, current_user)
    if espace_id is not None:
        query = query.filter(Intervention.espace_id == espace_id)
    return query.order_by(Intervention.cree_le.desc()).all()


@router.post("/", response_model=InterventionRead, status_code=status.HTTP_201_CREATED)
def creer_intervention(
    data: InterventionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(intervenant),
    meteo: IMeteoService = Depends(get_meteo_service),
):
    espace = EspaceVertRepositoryImpl(db).get_pour_organisation(data.espace_id, current_user.organisation_id)
    if espace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Espace vert introuvable")
    champs = data.model_dump()
    if champs["statut"] == "terminee" and champs["realisee_le"] is None:
        champs["realisee_le"] = datetime.now(UTC)
    intervention = Intervention(**champs, cree_par=current_user.id)
    db.add(intervention)
    return _enregistrer(db, intervention, espace, meteo)


@router.get("/{intervention_id}", response_model=InterventionRead)
def obtenir_intervention(
    intervention_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    return _intervention_de_l_organisation(intervention_id, db, current_user)


@router.put("/{intervention_id}", response_model=InterventionRead)
def maj_intervention(
    intervention_id: int,
    data: InterventionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(intervenant),
    meteo: IMeteoService = Depends(get_meteo_service),
):
    """Suivi d'une intervention (dont « terminer », avec le volume réel) : ouvert aux techniciens.

    Repasser une intervention terminée en planifiée ou en cours l'annule : sa date de réalisation
    est effacée et son apport d'eau retiré du bilan.
    """
    intervention = _intervention_de_l_organisation(intervention_id, db, current_user)
    champs = data.model_dump(exclude_unset=True)
    statut = champs.get("statut", intervention.statut)
    if "realisee_le" not in champs:
        if statut == "terminee" and intervention.realisee_le is None:
            champs["realisee_le"] = datetime.now(UTC)
        elif statut != "terminee" and intervention.statut == "terminee":
            champs["realisee_le"] = None
    for champ, valeur in champs.items():
        setattr(intervention, champ, valeur)
    return _enregistrer(db, intervention, intervention.espace, meteo)


@router.delete("/{intervention_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_intervention(
    intervention_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(gestionnaire),
    meteo: IMeteoService = Depends(get_meteo_service),
):
    """Supprime l'intervention ; un arrosage compté est retiré du bilan, aussitôt recalculé."""
    intervention = _intervention_de_l_organisation(intervention_id, db, current_user)
    espace = intervention.espace
    depuis = retirer_action_irrigation(intervention.id, ActionIrrigationRepositoryImpl(db), settings.fuseau)
    db.delete(intervention)
    db.commit()
    _recalculer(db, espace, depuis, meteo)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
