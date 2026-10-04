from datetime import UTC, date, datetime, tzinfo

from application.dto.intervention import (
    InterventionsUrgentesDTO,
    InterventionUrgenteDTO,
    PrioriteIntervention,
    TypeIntervention,
)
from application.use_cases.generer_bilans_hydriques_journaliers import jour_metier
from domain.logic.arrosage import horodatage_arrosage, quantite_apportee_mm
from domain.models import ActionIrrigation, EspaceVert, Intervention
from domain.ports.action_irrigation_repository import IActionIrrigationRepository
from domain.ports.capteurs import EspaceIdentifie, ICapteurService, LectureCapteur

SEUIL_CO2_PPM = 1200
SEUIL_CHALEUR_C = 32
# Rang explicite : un tri alphabétique placerait "low" avant "critical"
RANG_PRIORITE = {PrioriteIntervention.CRITICAL: 0, PrioriteIntervention.HIGH: 1, PrioriteIntervention.LOW: 2}
_ORDRE_TYPES = list(TypeIntervention)


def _detecter_problemes(
    espace: EspaceIdentifie, lecture: LectureCapteur, maintenant: datetime
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
    espaces: list[EspaceIdentifie],
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


def _arrosage_a_compter(intervention: Intervention) -> bool:
    return (intervention.type == "arrosage" and intervention.statut == "terminee"
            and (intervention.volume_eau_l or 0) > 0)


def synchroniser_action_irrigation(
    intervention: Intervention,
    espace: EspaceVert,
    action_repo: IActionIrrigationRepository,
    fuseau: tzinfo,
    maintenant: datetime | None = None,
) -> date | None:
    """Aligne l'apport d'eau lié sur l'intervention (déjà écrite, non validée).

    Arrosage terminé avec un volume : un seul apport (volume / surface), horodaté à la réalisation.
    Sinon (autre statut, autre type, volume nul) : l'apport éventuel est retiré.
    Renvoie le premier jour (fuseau métier) dont le bilan change, None si rien ne change.
    Lève ArrosageNonComptableError (surface inconnue, date future) : l'appelant annule la transaction.
    """
    existante = action_repo.get_par_intervention(intervention.id)
    jours = [jour_metier(existante.timestamp, fuseau)] if existante else []

    if not _arrosage_a_compter(intervention):
        if existante is None:
            return None
        action_repo.supprimer(existante)
        return jours[0]

    maintenant = maintenant or datetime.now(UTC)
    quantite = quantite_apportee_mm(intervention.volume_eau_l, espace.surface_m2)
    horodatage = horodatage_arrosage(intervention.realisee_le or maintenant, maintenant)
    intervention.realisee_le = horodatage   # même instant, en UTC : apport et intervention restent alignés
    if existante is None:
        action_repo.ajouter(ActionIrrigation(espace_id=espace.id, quantite_mm=quantite, timestamp=horodatage,
                                             intervention_id=intervention.id))
    else:
        if existante.quantite_mm == quantite and jour_metier(horodatage, fuseau) == jours[0]:
            existante.timestamp = horodatage
            return None
        existante.quantite_mm, existante.timestamp = quantite, horodatage
        action_repo.ajouter(existante)
    jours.append(jour_metier(horodatage, fuseau))
    return min(jours)


def retirer_action_irrigation(
    intervention_id: int, action_repo: IActionIrrigationRepository, fuseau: tzinfo
) -> date | None:
    """Avant la suppression d'une intervention : retire son apport ; renvoie le jour à recalculer."""
    existante = action_repo.get_par_intervention(intervention_id)
    if existante is None:
        return None
    jour = jour_metier(existante.timestamp, fuseau)
    action_repo.supprimer(existante)
    return jour
