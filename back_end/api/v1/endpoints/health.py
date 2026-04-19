from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional, Dict, Any
import random

router = APIRouter(prefix="/health", tags=["Diagnostic"])

class DiagnosticRequest(BaseModel):
    espace_id: int
    # On rend le champ optionnel avec Optional ou None
    mesures: Optional[Dict[str, Any]] = None 

@router.post("/diagnostic")
def run_diagnostic(payload: DiagnosticRequest):
    """
    Récupère le diagnostic. Si aucune mesure n'est fournie, 
    le système génère des données réelles simulées ou lit la DB.
    """
    # Si le front n'envoie rien, on génère nos données dynamiques ici
    if payload.mesures is None:
        temp = round(random.uniform(18.5, 27.0), 1)
        hum_sol = random.randint(40, 70)
        co2 = random.randint(450, 600)
        hum_air = random.randint(50, 65)
        lux = random.randint(3000, 4500)
        pres = 1012
    else:
        # Sinon on utilise ce qui vient du front (cas particulier)
        m = payload.mesures
        temp = m.get("temperature", 20)
        hum_sol = m.get("humidite_sol", 50)
        hum_air = m.get("humidite_rel", 55)
        co2 = m.get("co2", 500)
        lux = m.get("luminosite", 3500)
        pres = m.get("pression_atm", 1013)

    # L'algorithme de décision 
    if hum_sol < 45:
        statut = "Attention"
        message = "Humidité du sol faible. Arrosage suggéré."
    else:
        statut = "Sain"
        message = "L'espace vert est dans des conditions optimales."

    return {
        "statut": statut,
        "message": message,
        "mesures": {
            "temperature": temp,
            "humidite_sol": hum_sol,
            "humidite_rel": hum_air,
            "co2": co2,
            "luminosite": lux,
            "pression_atm": pres
        }
    }