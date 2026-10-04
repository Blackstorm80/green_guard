from datetime import date, datetime

from pydantic import BaseModel


class SecheresseEspaceDTO(BaseModel):
    """Restriction du jour au point d'un espace et ce qu'elle permet (domain/logic/secheresse.py)."""
    niveau: str                     # aucune, vigilance, alerte, alerte_renforcee, crise ou inconnu
    autorise_maintenant: bool
    interdit_toute_la_journee: bool
    plage_interdite: str | None = None   # « 11:00–18:00 »
    motif: str
    derogation: str | None = None
    type_zone: str | None = None         # AEP, SOU, SUP
    zone_nom: str | None = None
    arrete_url: str | None = None
    releve_le: datetime | None = None
    releve_du: date | None = None        # date du relevé retenu (antérieure : relevé du jour manquant)
    priorite_secheresse: int             # 1 jeunes plantations, 2 arbres, 3 massifs, 4 gazons et autres
    priorite_libelle: str


class EtatEspaceSecheresseDTO(SecheresseEspaceDTO):
    espace_id: int
    nom: str
    ville: str | None = None
    source_eau: str


class SyntheseSecheresseDTO(BaseModel):
    niveau_max: str
    par_niveau: dict[str, int]
    espaces_interdits: int          # interdits toute la journée
    espaces_avec_plage: int         # arrosage permis hors d'une plage horaire
    espaces_niveau_inconnu: int
    derniere_actualisation: datetime | None = None


class EtatSecheresseDTO(BaseModel):
    date: date
    synthese: SyntheseSecheresseDTO
    espaces: list[EtatEspaceSecheresseDTO]   # par priorité d'arrosage, puis par nom
    avertissement: str | None = None
    source: str


class RapportActualisationDTO(BaseModel):
    lus: int
    echecs: int
