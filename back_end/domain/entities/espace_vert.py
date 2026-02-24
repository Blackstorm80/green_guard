from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.database import Base

class EspaceVertEntity(Base):
    __tablename__ = "espaces_verts"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, index=True)
    ville = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    surface_m2 = Column(Float)
    sante_percent = Column(Float)
    
    # Ancienne FK (à supprimer si tu utilises gerant_id)
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # NOUVELLES RELATIONS CORRECTES
    bilans = relationship("BilanHydriqueJournalierEntity", back_populates="espace")
    
    #  Relation zones intelligentes (many-to-many)
    zones_intelligentes = relationship(
        "ZoneIntelligenteEntity", 
        secondary="zones_espaces", 
        back_populates="espaces"
    )
    # Relation many-to-many avec espèces
    especes_vegetales = relationship(
        "EspeceVegetaleEntity",
        secondary="espaces_especes",
        back_populates="espaces_verts"
    )
    # Relations capteurs et interventions
    capteurs = relationship("CapteurEntity", back_populates="espace", cascade="all, delete-orphan")
    interventions = relationship("InterventionEntity", back_populates="espace", cascade="all, delete-orphan")

    
    #  Alertes de cet espace
    alertes = relationship("AlerteEntity", back_populates="espace", cascade="all, delete-orphan")
    
    # Ancienne relation user (si tu l'as)
    user = relationship("UserEntity", back_populates="espaces_verts")
