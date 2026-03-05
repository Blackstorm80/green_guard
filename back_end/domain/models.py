# Fichier : back_end/domain/models.py
# Ce fichier centralise tous les modèles de données SQLAlchemy,.
#note a moi meme : le 'domain' ne doit avoir aucune dépendance vers l'infrastructure'.

import datetime
from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import declarative_base, relationship

# 1. Base Déclarative : Cœur de l'ORM
# Toutes les entités hériteront de cette base.
Base = declarative_base()

# 2. Tables d'Association (Many-to-Many)
# Déclarées ici pour être importées sans dépendances circulaires.

zones_espaces = Table(
    "zones_espaces",
    Base.metadata,
    Column("zone_id", Integer, ForeignKey("zones_intelligentes.id"), primary_key=True),
    Column("espace_id", Integer, ForeignKey("espaces_verts.id"), primary_key=True),
)

espaces_especes = Table(
    "espaces_especes",
    Base.metadata,
    Column("espace_id", Integer, ForeignKey("espaces_verts.id"), primary_key=True),
    Column("espece_id", Integer, ForeignKey("especes_vegetales.id"), primary_key=True),
)


# 3. Énumérations
# Utiliser les Enum de Python pour la validation des données au niveau de l'application.

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

class TypeCapteur(str, PyEnum):
    TEMPERATURE = "temperature"
    HUMIDITE_RELATIVE = "humidite_relative"
    HUMIDITE_SOL = "humidite_sol"
    CO2 = "co2"
    O2 = "o2"
    LUMINOSITE = "luminosite"
    PRESSION_ATM = "pression_atm"

class TypeIntervention(str, PyEnum):
    ARROSAGE = "arrosage"
    TAILLE = "taille"
    FERTILISATION = "fertilisation"
    TRAITEMENT = "traitement"
    NETTOYAGE = "nettoyage"
    DIAGNOSTIC = "diagnostic"


# 4. Modèles d'Entités (Classes ORM)

class User(Base):
    """Représente un utilisateur de l'application."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    role = Column(String, default="user", nullable=False)  # admin, manager, user

    # Relations (One-to-Many)
    espaces_verts = relationship("EspaceVert", back_populates="user", cascade="all, delete-orphan")
    zones_intelligentes = relationship("ZoneIntelligente", back_populates="user", cascade="all, delete-orphan")
    configs_clustering = relationship("ClusteringConfig", back_populates="user", cascade="all, delete-orphan")
    interventions = relationship("Intervention", back_populates="createur", cascade="all, delete-orphan")
    alertes = relationship("Alerte", back_populates="user", cascade="all, delete-orphan")
    hashed_password = Column(String, nullable=False)


class EspaceVert(Base):
    """Représente un espace vert géré par l'application."""

    __tablename__ = "espaces_verts"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, index=True, nullable=False)
    ville = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    surface_m2 = Column(Float)
    sante_percent = Column(Float, default=100.0)

    # Clé étrangère vers l'utilisateur propriétaire
    user_id = Column(Integer, ForeignKey("users.id"))

    # Relations
    user = relationship("User", back_populates="espaces_verts")
    
    # Many-to-Many avec ZoneIntelligente
    zones_intelligentes = relationship(
        "ZoneIntelligente", secondary=zones_espaces, back_populates="espaces"
    )

    # Many-to-Many avec EspeceVegetale
    especes_vegetales = relationship(
        "EspeceVegetale", secondary=espaces_especes, back_populates="espaces_verts"
    )

    # One-to-Many
    bilans = relationship("BilanHydriqueJournalier", back_populates="espace", cascade="all, delete-orphan")
    capteurs = relationship("Capteur", back_populates="espace", cascade="all, delete-orphan")
    interventions = relationship("Intervention", back_populates="espace", cascade="all, delete-orphan")
    alertes = relationship("Alerte", back_populates="espace", cascade="all, delete-orphan")


class ZoneIntelligente(Base):
    """Regroupement logique d'espaces verts basé sur des critères (clustering)."""

    __tablename__ = "zones_intelligentes"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), index=True, nullable=False)
    
    # Clés étrangères
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    config_id = Column(Integer, ForeignKey("clustering_configs.id"), nullable=True)

    # Propriétés du cluster
    centroid_lat = Column(Float, nullable=False)
    centroid_lon = Column(Float, nullable=False)
    rayon_km = Column(Float, default=1.5)
    sante_moyenne = Column(Float, default=0.0)
    nb_espaces = Column(Integer, default=0)
    granularite = Column(String(20), default="arrondissement")
    silhouette_score = Column(Float, nullable=True)

    # Audit
    cree_le = Column(DateTime, default=datetime.datetime.utcnow)
    mis_a_jour_le = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relations
    user = relationship("User", back_populates="zones_intelligentes")
    config = relationship("ClusteringConfig", back_populates="zones")
    espaces = relationship(
        "EspaceVert", secondary=zones_espaces, back_populates="zones_intelligentes"
    )

class EspeceVegetale(Base):
    """Catalogue des espèces végétales avec leurs caractéristiques."""

    __tablename__ = "especes_vegetales"

    id = Column(Integer, primary_key=True, index=True)
    nom_commun = Column(String(100), index=True)
    nom_scientifique = Column(String(150), unique=True)
    
    # Seuils hydriques
    humidite_sol_min = Column(Float, default=20.0)
    humidite_sol_max = Column(Float, default=60.0)
    
    # Coefficient cultural pour le calcul de l'évapotranspiration
    coeff_cultural = Column(Float, default=1.0)

    # Audit
    cree_le = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relation Many-to-Many
    espaces_verts = relationship(
        "EspaceVert", secondary=espaces_especes, back_populates="especes_vegetales"
    )

class BilanHydriqueJournalier(Base):
    """Enregistrement quotidien du bilan hydrique pour un espace vert."""

    __tablename__ = "bilans_hydriques"

    id = Column(Integer, primary_key=True, index=True)
    date_bilan = Column(Date, default=datetime.date.today)
    precipitations_mm = Column(Float)
    evapotranspiration_mm = Column(Float)
    bilan_mm = Column(Float)
    arrosage_recommande_mm = Column(Float)

    # Clé étrangère
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"), nullable=False)
    
    # Relation
    espace = relationship("EspaceVert", back_populates="bilans")


class Capteur(Base):
    """Représente un capteur physique déployé sur un espace vert."""

    __tablename__ = "capteurs"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(100), index=True)
    type = Column(Enum(TypeCapteur), index=True)
    emplacement = Column(String(100))
    est_actif = Column(Boolean, default=True)
    
    # Clé étrangère
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"), index=True)
    
    # Audit
    cree_le = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relations
    espace = relationship("EspaceVert", back_populates="capteurs")
    mesures = relationship("MesureCapteur", back_populates="capteur", cascade="all, delete-orphan")

class MesureCapteur(Base):
    """Une mesure ponctuelle prise par un capteur."""
    
    __tablename__ = "mesures_capteurs"
    
    id = Column(Integer, primary_key=True, index=True)
    valeur = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    
    # Clé étrangère
    capteur_id = Column(Integer, ForeignKey("capteurs.id"), nullable=False)

    # Relation
    capteur = relationship("Capteur", back_populates="mesures")


class Intervention(Base):
    """Action de maintenance planifiée ou réalisée sur un espace vert."""

    __tablename__ = "interventions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(TypeIntervention), index=True)
    description = Column(String(500))
    statut = Column(String(20), default="planifiee")  # planifiee, en_cours, terminee
    
    # Clés étrangères
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"), index=True)
    cree_par_id = Column(Integer, ForeignKey("users.id"))
    
    # Timestamps
    planifiee_le = Column(DateTime, nullable=True)
    realisee_le = Column(DateTime, nullable=True)

    # Relations
    espace = relationship("EspaceVert", back_populates="interventions")
    createur = relationship("User", back_populates="interventions")

class Alerte(Base):
    """Notification générée par le système suite à la détection d'un seuil."""

    __tablename__ = "alertes"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(Enum(TypeAlerte), index=True)
    niveau = Column(Enum(NiveauAlerte), index=True)
    message = Column(String(255))
    est_active = Column(Boolean, default=True)
    
    # Clés étrangères
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    
    # Audit
    cree_le = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relations
    espace = relationship("EspaceVert", back_populates="alertes")
    user = relationship("User", back_populates="alertes")


class ClusteringConfig(Base):
    """Configuration pour un algorithme de clustering des espaces verts."""

    __tablename__ = "clustering_configs"

    id = Column(Integer, primary_key=True, index=True)
    algo = Column(String(20), default="kmeans")
    n_clusters = Column(Integer, default=5)
    features = Column(Text, default='["latitude", "longitude", "sante_percent"]')
    
    # Clé étrangère
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    
    # Audit
    cree_le = Column(DateTime, default=datetime.datetime.utcnow)
    
    # Relations
    user = relationship("User", back_populates="configs_clustering")
    zones = relationship("ZoneIntelligente", back_populates="config")



from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from datetime import datetime


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String, nullable=False)
    type_notif = Column(String, default="info") # info, warning, urgent
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"), nullable=True)
    est_lu = Column(Boolean, default=False)
    cree_le = Column(DateTime, default=datetime.utcnow)