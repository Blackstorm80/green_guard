"""Interventions : détection des urgences + CRUD (repris de feature/Lucresse-branche, sécurisé)."""
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from api.deps.auth import exiger_role, get_current_user
from api.v1.endpoints.capteurs import get_capteur_service
from application.dto.intervention import InterventionsUrgentesDTO
from application.use_cases.interventions import lister_interventions_urgentes
from domain.logic.droits import ROLES_GESTION, ROLES_INTERVENTION
from domain.models import EspaceVert, Intervention, User
from infrastructure.database import get_db
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl
from infrastructure.services.capteur_hybrid_service import CapteurHybridService
from schema.interventions import InterventionCreate, InterventionRead, InterventionUpdate

router = APIRouter()
intervenant = exiger_role(*ROLES_INTERVENTION)
gestionnaire = exiger_role(*ROLES_GESTION)


def _requete_organisation(db: Session, user: User):
    """Interventions limitées aux espaces de l'organisation."""
    return db.query(Intervention).join(EspaceVert).filter(EspaceVert.organisation_id == user.organisation_id)


def _intervention_de_l_organisation(intervention_id: int, db: Session, user: User) -> Intervention:
    intervention = _requete_organisation(db, user).filter(Intervention.id == intervention_id).first()
    if intervention is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intervention introuvable")
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
):
    if EspaceVertRepositoryImpl(db).get_pour_organisation(data.espace_id, current_user.organisation_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Espace vert introuvable")
    intervention = Intervention(**data.model_dump(), cree_par=current_user.id)
    db.add(intervention)
    db.commit()
    db.refresh(intervention)
    return intervention


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
):
    """Suivi d'une intervention (dont « terminer ») : ouvert aux techniciens."""
    intervention = _intervention_de_l_organisation(intervention_id, db, current_user)
    champs = data.model_dump(exclude_unset=True)
    if champs.get("statut") == "terminee" and "realisee_le" not in champs and intervention.realisee_le is None:
        champs["realisee_le"] = datetime.now(UTC)
    for champ, valeur in champs.items():
        setattr(intervention, champ, valeur)
    db.commit()
    db.refresh(intervention)
    return intervention


@router.delete("/{intervention_id}", status_code=status.HTTP_204_NO_CONTENT)
def supprimer_intervention(
    intervention_id: int, db: Session = Depends(get_db), current_user: User = Depends(gestionnaire)
):
    db.delete(_intervention_de_l_organisation(intervention_id, db, current_user))
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
