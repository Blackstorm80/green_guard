from datetime import UTC, datetime

from application.dto.intervention import (
    InterventionsUrgentesDTO,
    InterventionUrgenteDTO,
    PrioriteIntervention,
    TypeIntervention,
)
from domain.models import EspaceVert
from domain.ports.capteurs import ICapteurService, LectureCapteur

SEUIL_CO2_PPM = 1200
SEUIL_CHALEUR_C = 32
# Rang explicite : un tri alphabétique placerait "low" avant "critical"
RANG_PRIORITE = {PrioriteIntervention.CRITICAL: 0, PrioriteIntervention.HIGH: 1, PrioriteIntervention.LOW: 2}
_ORDRE_TYPES = list(TypeIntervention)


def _detecter_problemes(
    espace: EspaceVert, lecture: LectureCapteur, maintenant: datetime
) -> list[InterventionUrgenteDTO]:
    """Plusieurs alertes possibles pour un même espace (pas de elif)."""
    problemes = []

    def ajouter(type_: TypeIntervention, label: str, description: str, priorite: PrioriteIntervention):
        problemes.append(InterventionUrgenteDTO(
            # Identifiant stable : un même problème garde le même id entre deux appels
            id=espace.id * 10 + _ORDRE_TYPES.index(type_),
            espace_id=espace.id,
            espace_nom=espace.nom,
            type=type_,
            label=label,
            description=description,
            priorite=priorite,
            created_at=lecture.timestamp or maintenant,
        ))

    if lecture.statut == "Critique":
        reserve = f" ({lecture.reserve_eau_mm:.0f} mm)" if lecture.reserve_eau_mm is not None else ""
        ajouter(TypeIntervention.STRESS_HYDRIQUE, "Sec", f"Stress hydrique critique{reserve}",
                PrioriteIntervention.CRITICAL)
    if lecture.co2_ppm is not None and lecture.co2_ppm > SEUIL_CO2_PPM:
        ajouter(TypeIntervention.HYPERCAPNIE, "CO₂", f"CO₂ élevé : {lecture.co2_ppm:.0f} ppm",
                PrioriteIntervention.HIGH)
    if lecture.temperature_c is not None and lecture.temperature_c > SEUIL_CHALEUR_C:
        ajouter(TypeIntervention.CANICULE, "Chaleur", f"Température : {lecture.temperature_c:.1f} °C",
                PrioriteIntervention.HIGH)
    return problemes


def lister_interventions_urgentes(
    espaces: list[EspaceVert],
    capteur_service: ICapteurService,
    limit: int = 5,
) -> InterventionsUrgentesDTO:
    """Interventions urgentes détectées sur les espaces fournis (déjà filtrés sur l'utilisateur)."""
    maintenant = datetime.now(UTC)
    interventions: list[InterventionUrgenteDTO] = []
    for espace, lecture in zip(espaces, capteur_service.lectures_actuelles(espaces), strict=False):
        interventions.extend(_detecter_problemes(espace, lecture, maintenant))

    interventions.sort(key=lambda i: (RANG_PRIORITE[i.priorite], -i.created_at.timestamp()))
    retenues = interventions[:limit]
    return InterventionsUrgentesDTO(
        interventions=retenues,
        total=len(interventions),
        non_lues=sum(1 for i in retenues if not i.is_read),
    )
