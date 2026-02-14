# back_end/domain/entities/espace_vert.py

class EspaceVertEntity:
    """
    Représente un espace vert dans le domaine métier.
    """
    def __init__(self, id: int, nom: str, zone: str | None = None, surface_m2: float = 50.0, reserve_utile_max: float = 100.0, plante_id: int = 1, ville: str | None = "Inconnue", latitude: float = 0.0, longitude: float = 0.0, sante_percent: float = 100.0):
        self.id = id
        self.nom = nom
        self.zone = zone
        self.surface_m2 = surface_m2
        self.reserve_utile_max = reserve_utile_max
        self.plante_id = plante_id
        self.ville = ville
        self.latitude = latitude
        self.longitude = longitude
        self.sante_percent = sante_percent