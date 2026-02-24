# Fichier: domain/entities/zone_intelligente.py

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.database import Base
from datetime import datetime
from typing import List

class ZoneIntelligenteEntity(Base):
    __tablename__ = "zones_intelligentes"
    
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), index=True, nullable=False)  # "Nord-Est 19e", "Buttes Chaumont"
    
    # Propriétaire / client
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    config_id = Column(Integer, ForeignKey("clustering_configs.id"), nullable=True)
    
    # Géométrie
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    rayon_km = Column(Float, default=1.5)  # ~1.5km pour arrondissements
    
    # Métriques agrégées
    sante_moyenne = Column(Float, default=0.0)
    nb_espaces = Column(Integer, default=0)
    
    # Configuration clustering
    granularite = Column(String(20), default="arrondissement")  # quartier, arrondissement, ville
    silhouette_score = Column(Float, nullable=True)  # Qualité 0-1
    
    # Audit
    cree_le = Column(DateTime, default=datetime.utcnow)
    mis_a_jour_le = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relations
    user = relationship("UserEntity", back_populates="zones_intelligentes")
    espaces = relationship(
        "EspaceVertEntity", 
        secondary="zones_espaces", 
        back_populates="zones_intelligentes"
    
    )

    zones = relationship(
    "EspaceVertEntity",
    secondary="zones_espaces",
    back_populates="zones",
)

    config = relationship(
        "ClusteringConfigEntity", 
        back_populates="zone", 
        uselist=False
    )

    """ la class en haut presente comment est repre"""
    """ la class en haut presente comment est representer une zone intelligente dans notre bave de donnée"""