from sqlalchemy import Column, Integer, String, Enum, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.database import Base
from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

class NiveauAlerte(str, PyEnum):
    INFO = "info"
    WARNING = "warning"
    URGENT = "urgent"

class TypeAlerte(str, PyEnum):
    STRESS_HYDRIQUE = "stress_hydrique"
    CANICULE = "canicule"
    CO2_ELEVE = "co2_eleve"
    HUMIDITE_FAIBLE = "humidite_faible"
    ARROSAGE_DUE = "arrosage_due"

class AlerteEntity(Base):
    __tablename__ = "alertes"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Contexte
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # Métadonnées alerte
    type = Column(Enum(TypeAlerte), index=True)
    niveau = Column(Enum(NiveauAlerte), index=True)
    message = Column(String(255))
    valeur_seuil = Column(String(50))  # ex: "humidité < 25%"
    
    # État
    est_active = Column(Boolean, default=True)
    est_acquit = Column(Boolean, default=False)
    
    # Audit
    cree_le = Column(DateTime, default=datetime.utcnow)
    resolu_le = Column(DateTime, nullable=True)
    
    # Relations
    espace = relationship("EspaceVertEntity", back_populates="alertes")
    user = relationship("UserEntity", back_populates="alertes")
