# domain/entities/espace_vert.py
from dataclasses import dataclass
from typing import Optional

@dataclass
class EspaceVertEntity:
    """
    Entité métier représentant un espace vert.
    """
    id: int
    nom: str
    type_espace: str
    localisation: str
    plante_id: int
    surface_m2: float
    exposition_reelle: str
    type_sol: str
    ph_sol: Optional[float] = None
    reserve_utile_max: float
    coefficient_cultural: float
    zone: Optional[str] = None
    gerant_id: Optional[int] = None