# domain/entities/bilan_hydrique.py
from dataclasses import dataclass
import datetime

@dataclass
class BilanHydriqueJournalierEntity:
    """
    Entité métier représentant le bilan hydrique pour un jour donné.
    """
    id: int
    date: datetime.date
    reserve_eau: float
    indice_stress: float
    statut_hydrique: str
    espace_id: int
    stress_sanitaire: float | None = None
    co2_absorbe_jour: float | None = None
    o2_produit_jour: float | None = None