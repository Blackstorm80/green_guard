# Fichier : domain/models.py

import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship

# Base déclarative pour nos modèles SQLAlchemy
Base = declarative_base()

class EspaceVert(Base):
    """
    Modèle ORM (SQLAlchemy) représentant un espace vert dans la base de données.
    """
    __tablename__ = "espaces_verts"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, index=True, nullable=False, unique=True)
    localisation = Column(String) # Ex: "48.8566, 2.3522"
    reserve_utile_max = Column(Float, nullable=False)
    coefficient_cultural = Column(Float, nullable=False)

    # Relation: Un EspaceVert a plusieurs bilans journaliers
    bilans_journaliers = relationship("BilanHydriqueJournalier", back_populates="espace_vert", cascade="all, delete-orphan")

class BilanHydriqueJournalier(Base):
    """
    Modèle ORM (SQLAlchemy) représentant un bilan hydrique journalier.
    """
    __tablename__ = "bilans_hydriques_journaliers"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False, default=datetime.date.today)
    reserve_eau = Column(Float, nullable=False)
    indice_stress = Column(Float, nullable=False)
    statut_hydrique = Column(String, nullable=False)

    # Clé étrangère vers l'espace vert concerné
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"), nullable=False)
    espace_vert = relationship("EspaceVert", back_populates="bilans_journaliers")