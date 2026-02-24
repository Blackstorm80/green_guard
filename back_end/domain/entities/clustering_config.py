# Fichier: domain/entities/clustering_config.py

from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from infrastructure.database import Base
from datetime import datetime
from enum import Enum as PyEnum

class Granularite(str, PyEnum):
    QUARTIER = "quartier"
    ARRONDISSEMENT = "arrondissement"
    VILLE = "ville"

class ClusteringConfigEntity(Base):
    __tablename__ = "clustering_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    
    # Paramètres K-Means
    algo = Column(String(20), default="kmeans")
    n_clusters = Column(Integer, default=5)
    granularite = Column(String(20), default="arrondissement")
    rayon_max_km = Column(Float, default=2.0)
    
    # Features utilisées (stocké JSON)
    features = Column(Text, default='["lat", "lon", "sante"]')
    
    # Audit
    cree_le = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("UserEntity", back_populates="configs_clustering")
    zone = relationship("ZoneIntelligenteEntity", back_populates="config")