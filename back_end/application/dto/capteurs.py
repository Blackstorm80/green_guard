from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from application.dto.meteo import MeteoDTO
from application.dto.secheresse import SecheresseEspaceDTO


class DoseRecommandeeDTO(BaseModel):
    """Dose pour revenir à la capacité au champ ; litres sans surface connue et minutes sans débit : null."""
    model_config = ConfigDict(from_attributes=True)

    mm: float
    litres: float | None = None
    minutes: float | None = None


class DecisionDTO(BaseModel):
    """Décision d'arrosage issue de la prévision à 7 jours (arroser / reporter / surveiller / rien), corrigée
    par le mode sécheresse : « interdit » (besoin d'eau, arrosage interdit) ou « arroser » hors d'une plage."""
    model_config = ConfigDict(from_attributes=True)

    code: Literal["arroser", "reporter", "surveiller", "rien", "interdit"]
    texte: str
    date_limite: date | None = None
    jour_pluie: date | None = None
    pluie_attendue_mm: float | None = None
    dose_recommandee: DoseRecommandeeDTO | None = None
    plage_interdite: str | None = None   # « 11:00–18:00 » : arroser en dehors
    derogation: str | None = None


class LectureCapteurDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    espace_id: int
    nom: str
    temperature_c: float | None = None
    humidite_percent: float | None = None
    humidite_air_percent: float | None = None
    co2_ppm: float | None = None
    reserve_eau_mm: float | None = None
    sante_percent: float | None = None
    statut: str
    timestamp: datetime | None = None
    reserve_max_mm: float | None = None
    reserve_facilement_utilisable_mm: float | None = None
    reserve_percent: float | None = None
    et0_mm: float | None = None
    etc_mm: float | None = None
    date_bilan: date | None = None
    version_modele: str | None = None
    dose_recommandee: DoseRecommandeeDTO | None = None
    # Prévision à 7 jours ; null si la météo est indisponible ou sans bilan FAO-56 récent
    decision: DecisionDTO | None = None
    date_bascule: date | None = None   # premier jour prévu en Critique (J si déjà critique)
    # Niveau VigiEau du jour et ce qu'il permet ; null si le mode sécheresse n'est pas évalué
    secheresse: SecheresseEspaceDTO | None = None


class MetriquesDashboardDTO(BaseModel):
    sante_globale_percent: float | None = None
    espaces_suivis: int
    espaces_avec_donnees: int
    espaces_stress: int
    espaces_critiques: int
    co2_moyen_ppm: float | None = None
    qualite_air: str


class DashboardCapteursDTO(BaseModel):
    statut: str    # "Sain" | "Attention" | "Critique" | "En attente"
    message: str
    meteo_exterieure: MeteoDTO | None = None
    capteurs: list[LectureCapteurDTO]
    metrics: MetriquesDashboardDTO
    # Jour métier du calcul (fuseau du serveur) : référence pour situer les dates de bascule
    date_calcul: date | None = None


class DiagnosticDTO(BaseModel):
    statut: str
    message: str
    # Phrase calculée (réserve, manque depuis la dernière pluie, évapotranspiration) ; None sans bilan FAO-56
    explication: str | None = None
    dose_recommandee: DoseRecommandeeDTO | None = None
    # Conseil chiffré (mm, litres, minutes) ; None si la réserve est pleine ou sans bilan FAO-56
    conseil_arrosage: str | None = None
    mesures: LectureCapteurDTO
