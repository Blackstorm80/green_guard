# back_end/api/v1/endpoints/interventions.py
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import List
from sqlalchemy.orm import Session #ceci est pour l'injection qu'on utilisera une base de données relationnelle avec SQLAlchemy

from application.dto.intervention import InterventionsUrgentesDTO
from application.dto.user import UserDTO
from application.use_cases.interventions import lister_interventions_urgentes
from api.deps.auth import get_current_user
from domain.ports.capteurs import ICapteurService
from domain.ports.espace_vert_repository import IEspaceVertRepository
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl
from api.v1.endpoints.capteurs import get_capteur_service

"""ici  on va définir les endpoints liés aux interventions
notamment celui pour lister les interventions urgentes pour le dashboard. 
On utilisera les DTOs et les use cases que nous avons définis précédemment."""
from schema.interventions import InterventionCreate, InterventionRead, InterventionUpdate
from domain.entities import InterventionEntity, EspaceVertEntity
from infrastructure.database import SessionLocal

"""notre petit initialisation de router pour les interventions"""
router = APIRouter(
    prefix="/interventions", 
    tags=["Interventions"])

def get_db():
    # Ouvre la connexion  et retourne  le connexion directement
    db = SessionLocal()

    return db #la connexion ne se fermera pas auto


@router.get("", response_model=[InterventionRead])

#Cette route permet de lister les interventions en passant l'id d'un espace vert
def lister_interventions(espace_id: int = Query(None, description="ID de l'espace vert pour filtrer les interventions urgentes"),
                        db: Session = Depends(get_db)):
    query = db.query(InterventionEntity) # pour faire une requete des interventions
    if espace_id is not None:
        query = query.filter(InterventionEntity.espace_id == espace_id) #si id alors on filtre les intercentions de cette espace vert
        
    interventions = query.all()
    return interventions 

#cette route permet d'obtenir les détails d'une intervention spécifique en passant son ID dans l'URL
@router.get("/{intervention_id}", response_model=InterventionRead)
def obtenir_intervention(intervention_id: int,  # c'est en parametre parce que ca vient de l'url /interventions/{intervention_id}
                         db: Session = Depends(get_db)):
#cherche id dans la BDD, et .first() pour retourner le premier résultat ou None si elle n'exite pas
    intervention = db.query(InterventionEntity).filter(InterventionEntity.id == intervention_id).first()
    if not intervention:
        msg_erreur = f" Desolé , aucune intervention trouvée avec l'ID {intervention_id}"
        erreur = HTTPException(status_code=404, detail=msg_erreur)
        raise erreur
    return intervention


"""Cette route permet de créer une nouvelle intervention en envoyant les données dans le corps de la requête."""
# on va  utilisiser interventionCreatepour la validation et INterventionRead pour la réponse
@router.post("", response_model=InterventionRead, status_code=201)

def creer_intervention(intervention_data: InterventionCreate,
                       db: Session = Depends(get_db)):
    espace = db.query(EspaceVertEntity).filter(
        EspaceVertEntity.id == intervention_data.espace_id
    ).first()
    
    if not espace:
        msg_erreur = "Espace vert avec l'ID {intervention_data.espace_id} introuvable"
        erreur = HTTPException(status_code=404, detail=msg_erreur)
        raise erreur
    
    
    nouvelle_intervention = InterventionEntity(
        type=intervention_data.type,
        description=intervention_data.description,
        volume_eau_l=intervention_data.volume_eau_l,
        espace_id=intervention_data.espace_id,
        planifiee_le=intervention_data.planifiee_le,
        realisee_le=intervention_data.realisee_le, # realisee_le et planifiee_le seront remplies automatiquement
    )
    
    db.add(nouvelle_intervention)
    db.commit()
    db.refresh(nouvelle_intervention) 
    return nouvelle_intervention

""" cette route permet de faire la maj d'une interv et d'envoyer uniquement les données modif  """
@router.put("/{intervention_id}", response_model=InterventionRead)
def maj_intervention(
    intervention_id: int,
    intervention_data: InterventionUpdate,
    db: Session = Depends(get_db)
):
    intervention = db.query(InterventionEntity).filter(
        InterventionEntity.id == intervention_id
    ).first()
    if not intervention:
        msg_erreur = f" Desolé , l'intervention avec l'ID {intervention_id} n'existe pas"
        erreur = HTTPException(status_code=404, detail=msg_erreur)
        raise erreur
    
    # nous allons faire un maj  en utilisant les champ presents
    update_data = intervention_data.dict(exclude_unset=True) # exclude_unset=True uniquement pour les champs utilisés
    for champ, valeur in update_data.items():
        setattr(intervention, champ, valeur)
    db.commit()
    db.refresh(intervention)
    return intervention


"""cette route permet de sup l'id de l'intevention dans l'url """
@router.delete("/{intervention_id}", status_code=204)
def supprimer_intervention(
    intervention_id: int, 
    db: Session = Depends(get_db)):
    intervention = db.query(InterventionEntity).filter(
        InterventionEntity.id == intervention_id
    ).first()
    if not intervention:
        msg_erreur = f" Desolé , l'intervention avec l'ID {intervention_id} n'existe pas"
        erreur = HTTPException(status_code=404, detail=msg_erreur)
        raise erreur
    db.delete(intervention)
    db.commit()
    return  None