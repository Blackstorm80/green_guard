# back_end/application/dto/meteo.py
from pydantic import BaseModel

class MeteoDTO(BaseModel):
    city: str
    temperature_c: float
    condition: str
    icon: str | None = None
    ensoleillement_fort: bool
