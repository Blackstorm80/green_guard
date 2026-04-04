from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from infrastructure.database import Base
from datetime import datetime
from enum import Enum as PyEnum

class TypeCapteur(str, PyEnum):
    TEMPERATURE = "temperature"
    HUMIDITE_RELATIVE = "humidite_relative"
    HUMIDITE_SOL = "humidite_sol"
    CO2 = "co2"
    O2 = "o2"
    LUMINOSITE = "luminosite"
    PRESSION_ATM = "pression_atm"

class CapteurEntity(Base):
    __tablename__ = "capteurs"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), index=True)  # "Capteur Sol P1", "Capteur Air A1"
    type = Column(Enum(TypeCapteur), index=True)
    emplacement = Column(String(100))  # "Sud parc", "Centre jardin"
    
    # Position dans l'espace vert
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"), index=True)
    
    # État technique
    est_actif = Column(Float, default=True)
    calibration_date = Column(DateTime, nullable=True)
    
    # Audit
    cree_le = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    espace = relationship("EspaceVertEntity", back_populates="capteurs")
    mesures = relationship("MesureCapteurEntity", back_populates="capteur")
