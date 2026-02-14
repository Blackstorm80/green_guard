# back_end/application/use_cases/interventions.py
from typing import List
from datetime import datetime

from application.dto.intervention import (
    InterventionsUrgentesDTO, 
    InterventionUrgenteDTO, 
    PrioriteIntervention, 
    TypeIntervention
)
from domain.ports.capteurs import ICapteurService, LectureCapteur
from domain.ports.espace_vert_repository import IEspaceVertRepository
from application.dto.user import UserDTO
from domain.entities.espace_vert import EspaceVertEntity


class InterventionInterne:
    """Structure interne pour les calculs avant la création du DTO final."""
    def __init__(self, espace_id: int, espace_nom: str, type: TypeIntervention,
                 label: str, description: str, priorite: PrioriteIntervention, created_at: datetime):
        self.espace_id = espace_id
        self.espace_nom = espace_nom
        self.type = type
        self.label = label
        self.description = description
        self.priorite = priorite
        self.created_at = created_at
        self.is_read = False


def _detecter_problemes_critiques(
    espace: EspaceVertEntity, 
    lecture: LectureCapteur
) -> List[InterventionInterne]:
    """
    Détecte les seuils critiques à partir d'une lecture capteur.
    Utilise des `if` au lieu de `elif` pour pouvoir remonter plusieurs alertes pour un même espace.
    """
    problèmes = []
    now = datetime.utcnow()
    
    # STRESS HYDRIQUE CRITIQUE
    if lecture.reserve_eau_mm < 15:
        problèmes.append(InterventionInterne(
            espace_id=espace.id,
            espace_nom=espace.nom,
            type=TypeIntervention.STRESS_HYDRIQUE,
            label="Sec",
            description=f"Réserve eau critique : {lecture.reserve_eau_mm:.0f}mm",
            priorite=PrioriteIntervention.CRITICAL,
            created_at=now
        ))
    
    # HYPERCAPNIE (CO2 > 1200ppm)
    if lecture.co2_ppm > 1200:
        problèmes.append(InterventionInterne(
            espace_id=espace.id,
            espace_nom=espace.nom,
            type=TypeIntervention.HYPERCAPNIE,
            label="CO₂",
            description=f"CO₂ élevé : {lecture.co2_ppm}ppm",
            priorite=PrioriteIntervention.HIGH,
            created_at=now
        ))
    
    # CHALEUR EXCESSIVE
    if lecture.temperature_c > 32:
        problèmes.append(InterventionInterne(
            espace_id=espace.id,
            espace_nom=espace.nom,
            type=TypeIntervention.CANICULE,
            label="Chaleur",
            description=f"Température seuil : {lecture.temperature_c:.1f}°C",
            priorite=PrioriteIntervention.HIGH,
            created_at=now
        ))
    
    return problèmes


def lister_interventions_urgentes(
    user: UserDTO,
    capteur_service: ICapteurService,
    espace_repo: IEspaceVertRepository,
    limit: int = 5,
    depuis_heures: int = 24
) -> InterventionsUrgentesDTO:
    """
    Liste les interventions urgentes pour l'utilisateur connecté,
    basé sur les lectures capteurs récentes et des seuils critiques.
    """
    espaces_user = espace_repo.list_by_user(user.id)
    
    interventions = []
    for espace in espaces_user:
        lecture = capteur_service.lecture_actuelle(espace.id)
        if lecture:
            interventions.extend(_detecter_problemes_critiques(espace, lecture))
    
    interventions.sort(key=lambda i: (i.priorite.value, i.created_at), reverse=True)
    
    interventions_dto = [InterventionUrgenteDTO(id=hash(f"{i.espace_id}-{i.type}-{i.created_at}"), **i.__dict__) for i in interventions[:limit]]
    
    return InterventionsUrgentesDTO(
        interventions=interventions_dto,
        total=len(interventions),
        non_lues=len([i for i in interventions_dto if not i.is_read])
    )