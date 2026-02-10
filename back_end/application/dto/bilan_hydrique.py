# application/dto/bilan_hydrique.py
from pydantic import BaseModel
from datetime import date


class BilanHydriqueEspaceDTO(BaseModel):
    """DTO pour le résumé du bilan hydrique d'un espace vert, destiné à l'API."""
    espace_id: int
    nom_espace: str
    type_espace: str
    localisation: str
    date_bilan: date
    statut_hydrique: str
    indice_stress: float
    stress_sanitaire: float | None = None
    co2_absorbe_jour: float | None = None
    o2_produit_jour: float | None = None