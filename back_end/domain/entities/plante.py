# domain/entities/plante.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class PlanteEntity:
    """Entité métier représentant une plante du catalogue."""
    id: int
    nom_scientifique: str
    nom_commun: str
    type_plante: str

    # Eau
    besoin_eau: str
    eau_min_mm_semaine: float
    eau_max_mm_semaine: float

    # Température
    temp_min_confort: float
    temp_max_confort: float
    temp_min_survie: float
    temp_max_survie: float

    # Lumière & Sol
    exposition: str
    type_sol_prefere: str
    ph_min: Optional[float] = None
    ph_max: Optional[float] = None

    # UI
    icone: Optional[str] = None
    description_courte: Optional[str] = None