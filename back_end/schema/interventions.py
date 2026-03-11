""" Tu dois créer **4 classes Pydantic** :

1. `InterventionBase` : les champs de base
   - `type` (str) : "arrosage", "taille", etc.
   - `description` (str) 
   - `volume_eau_l` (float, optionnel)
   - `espace_id` (int)
   - `planifiee_le` (datetime, optionnel)
   - `realisee_le` (datetime, optionnel)

2. `InterventionCreate` : hérite de `InterventionBase`

3. `InterventionUpdate` : tous les champs optionnels de `InterventionBase`

4. `InterventionRead` : hérite de `InterventionBase` + ajoute `id: int`

**Astuce** : Regarde comment sont faits les schémas pour `espace_vert.py` dans le même dossier."""


from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime

class InterventionBase(BaseModel):
    type: str      # Intervention comme arrosage, taille, désherbage, le traitement des plantes et le nettoyage
    description: str
    volume_eau: Optional[float] = None # en litres pour les interventions d'arrosage
    espace_id: int # ID de l'espace vert ou l'intervention a lieu
    planifiee_le: Optional[datetime] = None  # Date et heure prévues pour l'intervention
    realisee_le: Optional[datetime] = None  # Date et heure quand l'intervention a été réalisée
    

class InterventionCreate(InterventionBase):
   pass

class InterventionUpdate(BaseModel):
   """Schéma pour la mise à jour et la modification d'une intervention"""
   # elle redéfinit tous les champs  en les rendant optionnels
   # pour permettre une MAJ
   type: Optional[str] = None
   description: Optional[str] = None
   volume_eau: Optional[float] = None
   espace_id: Optional[int] = None
   planifiee_le: Optional[datetime] = None
   realisee_le: Optional[datetime] = None
