# application/dto/plante.py
from pydantic import BaseModel, model_validator


class PlantDTO(BaseModel):
    """DTO pour l'affichage d'une plante dans un catalogue."""
    id: int
    name: str       # nom_commun
    type: str       # type_plante
    water: str     # "Faible" | "Moyen" | "Élevé"
    exposure: str  # "Soleil" | "Mi-ombre" | "Ombre"
    icon: str | None = None

class PlantCreateDTO(BaseModel):
    """DTO pour la création d'une nouvelle plante dans le catalogue."""
    nom_scientifique: str
    nom_commun: str
    type_plante: str
    besoin_eau: str
    eau_min_mm_semaine: float
    eau_max_mm_semaine: float
    temp_min_confort: float
    temp_max_confort: float
    temp_min_survie: float
    temp_max_survie: float
    exposition: str
    type_sol_prefere: str
    ph_min: float | None = None
    ph_max: float | None = None
    icone: str | None = None
    description_courte: str

    @model_validator(mode='after')
    def check_range_coherence(self):
        """Vérifie la cohérence des plages min/max."""
        if self.eau_min_mm_semaine > self.eau_max_mm_semaine:
            raise ValueError("eau_min_mm_semaine ne peut pas être supérieur à eau_max_mm_semaine")
        if self.temp_min_confort > self.temp_max_confort:
            raise ValueError("temp_min_confort ne peut pas être supérieur à temp_max_confort")
        if self.temp_min_survie > self.temp_max_survie:
            raise ValueError("temp_min_survie ne peut pas être supérieur à temp_max_survie")
        if self.temp_min_survie > self.temp_min_confort:
            raise ValueError("temp_min_survie ne peut pas être supérieur à temp_min_confort")
        if self.temp_max_confort > self.temp_max_survie:
            raise ValueError("temp_max_confort ne peut pas être supérieur à temp_max_survie")
        if self.ph_min is not None and self.ph_max is not None and self.ph_min > self.ph_max:
            raise ValueError("ph_min ne peut pas être supérieur à ph_max")
        return self