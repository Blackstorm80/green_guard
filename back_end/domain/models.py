from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean, Date, Text, JSON,func
from sqlalchemy.orm import relationship
from datetime import datetime
from infrastructure.database import Base

# --- 1. UTILISATEURS ---
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

# --- 2. BOTANIQUE & CATALOGUE ---
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

# --- 3. ESPACES & LOGIQUE MÉTIER ---
class EspaceVert(Base):
    __tablename__ = "espaces_verts"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String)
    ville = Column(String, nullable=True)
    latitude = Column(Float)
    longitude = Column(Float)
    surface_m2 = Column(Float, nullable=True)
    type_espace = Column(String) #    
    # --- CHAMPS AGRONOMIQUES CRITIQUES (non fini)
    type_sol = Column(String, nullable=True)
    ph_actuel = Column(Float, nullable=True)
    exposition = Column(String, nullable=True)
    drainage = Column(String, nullable=True)
    humidite_cible = Column(Float, nullable=True)
    frequence_arrosage_auto = Column(Integer, nullable=True) # En heures
    profondeur_racinaire = Column(Float, nullable=True) # En cm
    type_irrigation = Column(String, nullable=True)
    date_derniere_fertilisation = Column(Date, nullable=True)
    sante_percent = Column(Float, nullable=True)
    # -----------------------------------------

    user_id = Column(Integer, ForeignKey("users.id"))
    
    proprietaire = relationship("User", back_populates="espaces")
    mesures = relationship("Mesure", back_populates="espace", cascade="all, delete-orphan")
    bilans_hydriques = relationship("BilanHydriqueJournalier", back_populates="espace")
    capteurs = relationship("Capteur", back_populates="espace")

class ZoneIntelligente(Base):
    __tablename__ = "zones_intelligentes"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))
    description = Column(Text, nullable=True)

class ClusteringConfig(Base):
    __tablename__ = "clustering_configs"
    id = Column(Integer, primary_key=True, index=True)
    nom_config = Column(String, unique=True)
    distance_max = Column(Float, default=0.5)
    algorithme = Column(String, default="DBSCAN")

# --- 4. CAPTEURS & MESURES ---
class Capteur(Base):
    __tablename__ = "capteurs"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String)
    type = Column(String)
    emplacement = Column(String, nullable=True) # Champ requis par ton script
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

# --- 5. ANALYSE & NOTIFICATIONS ---
class BilanHydriqueJournalier(Base):
    __tablename__ = "bilans_hydriques"
    id = Column(Integer, primary_key=True, index=True)
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"))
    date = Column(Date, default=datetime.utcnow().date())
    reserve_utile_fin_journee = Column(Float)
    
    indice_stress = Column(Float, default=0.0)
    statut_hydrique = Column(String, default="Optimal")
    stress_sanitaire = Column(Float, nullable=True)
    
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"))
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
    timestamp = Column(DateTime, default=func.now()) # Utilise func.now() de sqlalchemy

class Intervention(Base):
    __tablename__ = "interventions"
    id = Column(Integer, primary_key=True, index=True)
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"))
    type_action = Column(String)
    terminee = Column(Boolean, default=False)