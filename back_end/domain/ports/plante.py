# application/dto/plante.py
from pydantic import BaseModel


class PlantDTO(BaseModel):
    id: int
    name: str       # nom_commun
    type: str       # type_plante
    water: str      # besoin_eau
    exposure: str   # exposition
    icon: str | None = None