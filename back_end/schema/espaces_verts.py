from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class EspaceVertBase(BaseModel):
    """Le socle commun : On ne garde en obligatoire que le strict nécessaire."""
    nom: str
    ville: Optional[str] = None
    latitude: float
    longitude: float
    surface_m2: Optional[float] = None
    user_id: int # L'ID de Nathan
    
    # --- Données Agronomiques (Optionnelles pour éviter les crashs 500) ---
    type_espace: Optional[str] = "Jardin"
    exposition_reelle: Optional[str] = "Ensoleillé"
    type_sol: Optional[str] = "Argileux"
    ph_sol: Optional[float] = 7.0
    reserve_utile_max: Optional[float] = 0.0
    coefficient_cultural: Optional[float] = 1.0
    zone: Optional[str] = None
    gerant_id: Optional[int] = None
    plante_id: Optional[int] = None

class EspaceVertCreate(EspaceVertBase):
    """Utilisé lors de l'envoi du formulaire par le Front-end."""
    pass

class EspaceVertRead(EspaceVertBase):
    """Utilisé par l'API pour renvoyer les données à React."""
    id: int
    # On ajoute les champs calculés ou automatiques
    sante_percent: Optional[float] = 100.0
    cree_le: Optional[datetime] = None

    # Crucial pour la compatibilité avec SQLAlchemy
    model_config = ConfigDict(from_attributes=True)

class EspaceVertUpdate(BaseModel):
    """Pour les modifications partielles des données agronomiques."""
    nom: Optional[str] = None
    ville: Optional[str] = None
    surface_m2: Optional[float] = None
    
    # --- 9 Champs Agronomiques ---
    type_sol: Optional[str] = None
    ph_actuel: Optional[float] = None
    exposition: Optional[str] = None
    drainage: Optional[str] = None
    humidite_cible: Optional[float] = None
    frequence_arrosage_auto: Optional[int] = None
    profondeur_racinaire: Optional[float] = None
    type_irrigation: Optional[str] = None
    date_derniere_fertilisation: Optional[datetime] = None