# Fichier : domain/schemas.py

from pydantic import BaseModel, Field
import datetime

class DonneesMeteoJournalieres(BaseModel):
    """
    Objet de données représentant les informations météo pour une journée.
    C'est un DTO (Data Transfer Object) utilisé par le domaine.
    """
    date: datetime.date
    pluie_mm: float = Field(..., description="Précipitations totales du jour en mm")
    et0_mm: float = Field(..., description="Évapotranspiration de référence (ET0) du jour en mm")
