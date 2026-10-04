"""Interventions : détection des urgences + CRUD (repris de feature/Lucresse-branche, sécurisé).

Boucle arrosage → bilan : toute écriture d'une intervention aligne l'apport d'eau compté dans le bilan
(application/use_cases/interventions.py), dans la même transaction, puis recalcule aussitôt le bilan.

Mode sécheresse : un arrosage interdit par le niveau VigiEau en vigueur est refusé (409), sauf dérogation ;
un arrosage réalisé fige son registre (niveau, plage, dérogation, agent) : ni les règles ni l'espace modifiés
ensuite ne le réécrivent, et sa date de réalisation ne se corrige qu'en l'annulant (repasser en planifié).
Limite connue : le registre est lu sur les interventions ; annuler, retyper ou supprimer un arrosage réalisé
le retire de l'export (pas encore de journal en ajout seul).
"""
import logging
from collections.abc import Callable
from datetime import UTC, date, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session, selectinload

from api.deps.auth import exiger_role, get_current_user
from api.v1.endpoints.capteurs import get_capteur_service
from api.v1.endpoints.meteo import get_meteo_service
from api.v1.endpoints.secheresse import get_vigieau_service
from application.dto.intervention import InterventionsUrgentesDTO
from application.use_cases.generer_bilans_hydriques_journaliers import arrosage_journalier, recalculer_bilan_espace
from application.use_cases.interventions import (
    lister_interventions_urgentes,
    retirer_action_irrigation,
    synchroniser_action_irrigation,
)
from application.use_cases.secheresse import (
    ArrosageInterditError,
    annuler_registre,
    controler_arrosage,
    meme_instant,
    niveau_du_releve,
    restriction_du_jour,
)
from config import settings
from domain.logic.arrosage import ArrosageNonComptableError
from domain.logic.droits import ROLES_GESTION, ROLES_INTERVENTION
from domain.logic.secheresse import regles_depuis_parametres
from domain.models import EspaceVert, Intervention, User
from domain.ports.meteo import IMeteoService
from domain.ports.vigieau import IVigieauService
from infrastructure.database import get_db
from infrastructure.repositories.action_irrigation_repository_impl import ActionIrrigationRepositoryImpl
from infrastructure.repositories.bilan_hydrique_repository_impl import BilanHydriqueRepositoryImpl
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl
from infrastructure.repositories.restriction_secheresse_repository_impl import RestrictionSecheresseRepositoryImpl
from infrastructure.services.capteur_hybrid_service import CapteurHybridService
from schema.interventions import InterventionCreate, InterventionRead, InterventionUpdate

logger = logging.getLogger(__name__)

router = APIRouter()
intervenant = exiger_role(*ROLES_INTERVENTION)
gestionnaire = exiger_role(*ROLES_GESTION)
# Champs dont dépend la légalité d'un arrosage : leur modification le fait contrôler à nouveau
CHAMPS_SECHERESSE = {"type", "statut", "realisee_le", "planifiee_le"}
REGISTRE_FIGE = ("Arrosage déjà réalisé : sa date de réalisation est figée dans le registre sécheresse. "
                 "Repassez-le en planifié pour l'annuler, puis terminez-le à nouveau à la bonne date.")


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


def _annulation(db: Session, espace: EspaceVert, maintenant: datetime) -> Callable[[], None]:
    """db.rollback() qui conserve le relevé VigiEau du jour fait pendant la requête : un arrosage refusé
    (409, 422) annule ses modifications, pas le niveau relevé (sinon relu à chaque tentative)."""
    aujourd_hui = maintenant.astimezone(settings.fuseau).date()
    repo = RestrictionSecheresseRepositoryImpl(db)
    deja_releve = repo.get(espace.id, aujourd_hui) is not None

    def annuler() -> None:
        releve = None if deja_releve else repo.get(espace.id, aujourd_hui)
        a_garder = (niveau_du_releve(releve), releve.recupere_le) if releve is not None else None
        db.rollback()
        if a_garder is not None:
            repo.enregistrer(espace.id, aujourd_hui, a_garder[0], a_garder[1] or maintenant)
            db.commit()
    return annuler


def _controler_secheresse(db: Session, intervention: Intervention, espace: EspaceVert, user: User,
                          vigieau: IVigieauService, annuler: Callable[[], None], maintenant: datetime) -> None:
    """Refus 409 d'un arrosage interdit, 422 d'une réalisation datée dans le futur (modifications annulées) ;
    niveau relevé à la demande s'il manque. Sans autoflush : l'intervention modifiée n'est pas écrite (ni sa
    ligne verrouillée) pendant l'éventuel appel à VigiEau."""
    aujourd_hui = maintenant.astimezone(settings.fuseau).date()
    repo = RestrictionSecheresseRepositoryImpl(db)
    try:
        with db.no_autoflush:
            controler_arrosage(
                intervention, espace, regles_depuis_parametres(user.organisation.parametres),
                lambda jour: restriction_du_jour(espace, jour, aujourd_hui, repo, vigieau, maintenant),
                settings.fuseau, maintenant, user.id,
            )
    except ArrosageInterditError as exc:
        annuler()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from None
    except ArrosageNonComptableError as exc:
        annuler()
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(exc)) from None


def _enregistrer(db: Session, intervention: Intervention, espace: EspaceVert, meteo: IMeteoService,
                 annuler: Callable[[], None] | None = None) -> Intervention:
    db.flush()
    try:
        depuis = synchroniser_action_irrigation(intervention, espace, ActionIrrigationRepositoryImpl(db),
                                                settings.fuseau)
    except ArrosageNonComptableError as exc:
        (annuler or db.rollback)()
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
    vigieau: IVigieauService = Depends(get_vigieau_service),
):
    espace = EspaceVertRepositoryImpl(db).get_pour_organisation(data.espace_id, current_user.organisation_id)
    if espace is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Espace vert introuvable")
    champs = data.model_dump()
    if champs["statut"] == "terminee" and champs["realisee_le"] is None:
        champs["realisee_le"] = datetime.now(UTC)
    intervention = Intervention(**champs, cree_par=current_user.id)
    maintenant = datetime.now(UTC)
    annuler = _annulation(db, espace, maintenant)
    _controler_secheresse(db, intervention, espace, current_user, vigieau, annuler, maintenant)
    db.add(intervention)
    return _enregistrer(db, intervention, espace, meteo, annuler)


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
    vigieau: IVigieauService = Depends(get_vigieau_service),
):
    """Suivi d'une intervention (dont « terminer », avec le volume réel) : ouvert aux techniciens.

    Repasser une intervention terminée en planifiée ou en cours l'annule : sa date de réalisation
    est effacée et son apport d'eau retiré du bilan ; sans nouvelle date prévue, cette annulation n'est
    pas soumise au contrôle sécheresse (possible même en crise). Un arrosage qui reste réalisé garde son registre
    sécheresse tel qu'il a été figé (sa date de réalisation n'est plus modifiable).
    """
    intervention = _intervention_de_l_organisation(intervention_id, db, current_user)
    champs = data.model_dump(exclude_unset=True)
    statut = champs.get("statut", intervention.statut)
    deja_realise = intervention.type == "arrosage" and intervention.statut == "terminee"
    reste_realise = champs.get("type", intervention.type) == "arrosage" and statut == "terminee"
    # Annulation d'une réalisation (terminée → planifiée ou en cours, sans nouvelle date prévue) : ce n'est
    # pas un arrosage, elle n'est pas contrôlée (sinon impossible sous interdiction totale)
    annulation = (deja_realise and statut != "terminee" and champs.get("type", "arrosage") == "arrosage"
                  and meme_instant(champs.get("planifiee_le", intervention.planifiee_le), intervention.planifiee_le))
    if deja_realise and reste_realise:
        if "realisee_le" in champs and not meme_instant(champs["realisee_le"], intervention.realisee_le):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=REGISTRE_FIGE)
        a_controler = False
    else:
        a_controler = not annulation and bool(CHAMPS_SECHERESSE & champs.keys())
    if "realisee_le" not in champs:
        if statut == "terminee" and intervention.realisee_le is None:
            champs["realisee_le"] = datetime.now(UTC)
        elif statut != "terminee" and intervention.statut == "terminee":
            champs["realisee_le"] = None
    espace = intervention.espace
    maintenant = datetime.now(UTC)
    annuler = _annulation(db, espace, maintenant)
    for champ, valeur in champs.items():
        setattr(intervention, champ, valeur)
    if annulation:
        annuler_registre(intervention)
    elif a_controler:
        _controler_secheresse(db, intervention, espace, current_user, vigieau, annuler, maintenant)
    return _enregistrer(db, intervention, espace, meteo, annuler)


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
