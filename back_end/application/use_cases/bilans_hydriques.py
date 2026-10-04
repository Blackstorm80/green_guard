"""Lecture des bilans hydriques : historique des termes (futur carnet de santé) et diagnostic expliqué."""
from datetime import date, timedelta

from application.dto.capteurs import DiagnosticDTO, LectureCapteurDTO
from domain.logic.fao56 import expliquer_bilan
from domain.models import BilanHydriqueJournalier
from domain.ports.bilan_hydrique_repository import IBilanHydriqueRepository
from domain.ports.capteurs import STATUT_SANS_DONNEE, EspaceIdentifie, ICapteurService

# Fenêtre de recherche de la dernière pluie efficace pour la phrase explicative
JOURS_EXPLICATION = 30

MESSAGES = {
    "Optimal": "L'espace vert est dans des conditions optimales.",
    "A surveiller": "Réserve facilement utilisable épuisée : la végétation commence à souffrir, "
                    "un arrosage est à prévoir.",
    "Critique": "Stress hydrique critique : arrosage recommandé sans délai.",
    STATUT_SANS_DONNEE: "Aucune mesure disponible pour cet espace pour le moment.",
}


def historique_des_bilans(
    espace_id: int, jours: int, aujourd_hui: date, bilan_repo: IBilanHydriqueRepository
) -> list[BilanHydriqueJournalier]:
    """Bilans des `jours` derniers jours (aujourd'hui compris), par date croissante."""
    return bilan_repo.lister_depuis(espace_id, aujourd_hui - timedelta(days=jours - 1))


def diagnostiquer_espace(
    espace: EspaceIdentifie,
    capteur_service: ICapteurService,
    bilan_repo: IBilanHydriqueRepository,
) -> DiagnosticDTO:
    """Diagnostic en lecture seule : dernier état connu et phrase explicative calculée sur l'historique."""
    lecture = LectureCapteurDTO.model_validate(capteur_service.lecture_actuelle(espace))
    explication = None
    if lecture.date_bilan is not None:
        debut = lecture.date_bilan - timedelta(days=JOURS_EXPLICATION - 1)
        explication = expliquer_bilan(bilan_repo.lister_depuis(espace.id, debut))
    return DiagnosticDTO(
        statut=lecture.statut, message=MESSAGES.get(lecture.statut, ""), explication=explication, mesures=lecture,
    )
