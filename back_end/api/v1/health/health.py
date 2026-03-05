from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from infrastructure.database import get_db
from domain.models import EspaceVert

router = APIRouter()

# --- Schéma de réponse pour le Dashboard ---
class HealthDiagnostic(BaseModel):
    espace_id: int
    nom: str
    sante_globale: float
    statut: str
    message: str

    class Config:
        from_attributes = True

# --- Endpoint ---
@router.get("/diagnostic", response_model=List[HealthDiagnostic], summary="Diagnostic santé global pour le Dashboard")
def get_diagnostic(db: Session = Depends(get_db)):
    """
    Récupère l'état de santé de tous les espaces verts pour alimenter les cartes du Dashboard.
    """
    espaces = db.query(EspaceVert).all()
    results = []
    
    for e in espaces:
        # Récupération de la santé (logique simplifiée pour la démo basée sur les données seedées)
        sante = getattr(e, "sante_percent", 100.0) or 100.0
        
        statut = "Sain"
        msg = "Aucune alerte"
        
        if sante < 50:
            statut = "Critique"
            msg = "Intervention nécessaire"
        elif sante < 80:
            statut = "Attention"
            msg = "À surveiller"
            
        results.append(HealthDiagnostic(
            espace_id=e.id,
            nom=e.nom,
            sante_globale=sante,
            statut=statut,
            message=msg
        ))
    return results
