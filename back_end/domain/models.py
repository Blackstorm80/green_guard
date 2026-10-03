from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Date, Text, JSON, Table, func
from sqlalchemy.orm import relationship
from datetime import datetime
from infrastructure.database import Base

# Table d'association many-to-many ZoneIntelligente <-> EspaceVert (A12)
zone_espaces = Table(
    "zone_espaces",
    Base.metadata,
    Column("zone_id", Integer, ForeignKey("zones_intelligentes.id"), primary_key=True),
    Column("espace_id", Integer, ForeignKey("espaces_verts.id"), primary_key=True),
)

#  1. UTILISATEURS
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String, default="user")
    is_active = Column(Boolean, default=True)
    avatar_url = Column(String, nullable=True)

    notifications = relationship("Notification", back_populates="user")
    espaces = relationship("EspaceVert", back_populates="proprietaire")

# 2. BOTANIQUE & CATALOGUE
class Plante(Base):
    __tablename__ = "plantes"
    id = Column(Integer, primary_key=True, index=True)
    nom_scientifique = Column(String, index=True)
    nom_commun = Column(String)
    famille = Column(String)
    ph_ideal = Column(Float)
    besoin_eau = Column(String)
    url_image = Column(String, nullable=True)

class Auxiliaire(Base):
    __tablename__ = "auxiliaires"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, index=True)
    description = Column(Text)
    role = Column(String)
    url_image = Column(String, nullable=True)

# A9 — EspeceVegetale utilisée dans sante.py
class EspeceVegetale(Base):
    __tablename__ = "especes_vegetales"
    id = Column(Integer, primary_key=True, index=True)
    nom_scientifique = Column(String, index=True)
    nom_commun = Column(String, nullable=True)
    famille = Column(String, nullable=True)
    temperature_min = Column(Float, nullable=True)
    temperature_max = Column(Float, nullable=True)
    humidite_min = Column(Float, nullable=True)
    humidite_max = Column(Float, nullable=True)

# A9 — TypeAlerte et NiveauAlerte utilisés dans sante.py
class TypeAlerte(Base):
    __tablename__ = "types_alertes"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    libelle = Column(String)

    alertes = relationship("Alerte", back_populates="type_alerte")

class NiveauAlerte(Base):
    __tablename__ = "niveaux_alertes"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True)
    libelle = Column(String)
    priorite = Column(Integer, default=0)

    alertes = relationship("Alerte", back_populates="niveau_alerte")

# A9 — Alerte utilisée dans sante.py
class Alerte(Base):
    __tablename__ = "alertes"
    id = Column(Integer, primary_key=True, index=True)
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"), nullable=True)
    type_alerte_id = Column(Integer, ForeignKey("types_alertes.id"), nullable=True)
    niveau_alerte_id = Column(Integer, ForeignKey("niveaux_alertes.id"), nullable=True)
    message = Column(Text)
    est_resolue = Column(Boolean, default=False)
    cree_le = Column(DateTime, default=datetime.utcnow)

    type_alerte = relationship("TypeAlerte", back_populates="alertes")
    niveau_alerte = relationship("NiveauAlerte", back_populates="alertes")

#  3. ESPACES & LOGIQUE MÉTIER
class EspaceVert(Base):
    __tablename__ = "espaces_verts"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String)
    ville = Column(String, nullable=True)
    latitude = Column(Float)
    longitude = Column(Float)
    surface_m2 = Column(Float, nullable=True)
    type_espace = Column(String)
    type_sol = Column(String, nullable=True)
    ph_actuel = Column(Float, nullable=True)
    exposition = Column(String, nullable=True)
    drainage = Column(String, nullable=True)
    humidite_cible = Column(Float, nullable=True)
    frequence_arrosage_auto = Column(Integer, nullable=True)
    profondeur_racinaire = Column(Float, nullable=True)
    type_irrigation = Column(String, nullable=True)
    date_derniere_fertilisation = Column(Date, nullable=True)
    sante_percent = Column(Float, nullable=True)
    reserve_utile_max = Column(Float, default=100.0)
    coefficient_cultural = Column(Float, default=1.0)

    user_id = Column(Integer, ForeignKey("users.id"))

    proprietaire = relationship("User", back_populates="espaces")
    mesures = relationship("Mesure", back_populates="espace", cascade="all, delete-orphan")
    bilans_hydriques = relationship("BilanHydriqueJournalier", back_populates="espace")
    capteurs = relationship("Capteur", back_populates="espace")
    zones = relationship("ZoneIntelligente", secondary=zone_espaces, back_populates="espaces")

# A11+A12 — ZoneIntelligente complétée avec champs manquants et relation espaces
class ZoneIntelligente(Base):
    __tablename__ = "zones_intelligentes"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(Text, nullable=True)
    centroid_lat = Column(Float, nullable=True)
    centroid_lon = Column(Float, nullable=True)
    rayon_km = Column(Float, nullable=True)
    sante_moyenne = Column(Float, nullable=True)
    nb_espaces = Column(Integer, default=0)

    espaces = relationship("EspaceVert", secondary=zone_espaces, back_populates="zones")

# A25 — ClusteringConfig complétée avec granularite et rayon_max_km
class ClusteringConfig(Base):
    __tablename__ = "clustering_configs"
    id = Column(Integer, primary_key=True, index=True)
    nom_config = Column(String, unique=True)
    distance_max = Column(Float, default=0.5)
    algorithme = Column(String, default="DBSCAN")
    granularite = Column(String, nullable=True)
    rayon_max_km = Column(Float, nullable=True)

#  4. CAPTEURS & MESURES
class Capteur(Base):
    __tablename__ = "capteurs"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String)
    type = Column(String)
    emplacement = Column(String, nullable=True)
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"))
    est_actif = Column(Boolean, default=True)

    espace = relationship("EspaceVert", back_populates="capteurs")

class Mesure(Base):
    __tablename__ = "mesures"
    id = Column(Integer, primary_key=True, index=True)
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"))
    temperature = Column(Float)
    humidite_sol = Column(Float)
    humidite_air = Column(Float)
    co2 = Column(Float, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    espace = relationship("EspaceVert", back_populates="mesures")

# 5. ANALYSE & NOTIFICATIONS
class BilanHydriqueJournalier(Base):
    __tablename__ = "bilans_hydriques"
    id = Column(Integer, primary_key=True, index=True)
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"))  # A8 — doublon supprimé
    date = Column(Date, default=datetime.utcnow().date())
    reserve_utile_fin_journee = Column(Float)
    indice_stress = Column(Float, default=0.0)
    statut_hydrique = Column(String, default="Optimal")
    stress_sanitaire = Column(Float, nullable=True)

    espace = relationship("EspaceVert", back_populates="bilans_hydriques")

class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    message = Column(String)
    type = Column(String, default="info")
    est_lue = Column(Boolean, default=False)
    cree_le = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")

class ActionIrrigation(Base):
    __tablename__ = "actions_irrigation"
    id = Column(Integer, primary_key=True, index=True)
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"))
    quantite_mm = Column(Float)
    timestamp = Column(DateTime, default=func.now())

class Intervention(Base):
    __tablename__ = "interventions"
    id = Column(Integer, primary_key=True, index=True)
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"))
    type_action = Column(String)
    terminee = Column(Boolean, default=False)
