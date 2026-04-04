from sqlalchemy import Column, Integer, String, Float, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.database import Base
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

class TypeIntervention(str, PyEnum):
    ARROSAGE = "arrosage"
    TAILLE = "taille"
    FERTILISATION = "fertilisation"
    TRAITEMENT = "traitement"
    NETTOYAGE = "nettoyage"
    DIAGNOSTIC = "diagnostic"

class InterventionEntity(Base):
    __tablename__ = "interventions"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Contexte métier
    type = Column(Enum(TypeIntervention), index=True)
    description = Column(String(500))
    volume_eau_l = Column(Float, nullable=True)  # pour arrosage
    duree_minutes = Column(Integer, nullable=True)
    cout_euros = Column(Float, nullable=True)
    
    # Localisation
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"), index=True)
    
    # Planification
    planifiee_le = Column(DateTime, nullable=True)
    realisee_le = Column(DateTime, default=datetime.utcnow)
    statut = Column(String(20), default="planifiee")  # planifiee, en_cours, terminee
    
    # Audit
    cree_par = Column(Integer, ForeignKey("users.id"))
    
    # Relations
    espace = relationship("EspaceVertEntity", back_populates="interventions")
    createur = relationship("UserEntity", back_populates="interventions")
