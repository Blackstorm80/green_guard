from datetime import date

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
    false,
    func,
    true,
)
from sqlalchemy.orm import relationship

from domain.logic.droits import LECTEUR, ROLES, permissions_du_role
from infrastructure.database import Base

STATUTS_HYDRIQUES = ("Optimal", "A surveiller", "Critique")
TYPES_INTERVENTION = ("arrosage", "ombrage", "taille", "fertilisation", "traitement", "nettoyage", "diagnostic")
STATUTS_INTERVENTION = ("planifiee", "en_cours", "terminee")


def _in(colonne: str, valeurs: tuple) -> str:
    return f"{colonne} IN ({', '.join(repr(v) for v in valeurs)})"


# Table d'association many-to-many ZoneIntelligente <-> EspaceVert
zone_espaces = Table(
    "zone_espaces",
    Base.metadata,
    Column("zone_id", Integer, ForeignKey("zones_intelligentes.id", ondelete="CASCADE"), primary_key=True),
    Column("espace_id", Integer, ForeignKey("espaces_verts.id", ondelete="CASCADE"), primary_key=True),
)


#  1. ORGANISATIONS & UTILISATEURS
class Organisation(Base):
    """Collectivité cliente : son patrimoine et ses membres sont cloisonnés (filtrage applicatif + RLS)."""
    __tablename__ = "organisations"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(120), nullable=False)
    slug = Column(String(80), nullable=False, unique=True, index=True)
    parametres = Column(JSON, nullable=True)  # paramètres métier propres à la collectivité
    cree_le = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    membres = relationship("User", back_populates="organisation", passive_deletes=True)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint(_in("role", ROLES), name="role"),)

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    organisation_id = Column(Integer, ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String, nullable=False, default=LECTEUR, server_default=LECTEUR)
    # Administrateur de la plateforme (crée les organisations), indépendant du rôle dans l'organisation
    est_superadmin = Column(Boolean, nullable=False, default=False, server_default=false())
    is_active = Column(Boolean, nullable=False, default=True, server_default=true())
    avatar_url = Column(String, nullable=True)

    organisation = relationship("Organisation", back_populates="membres")
    notifications = relationship("Notification", back_populates="user", passive_deletes=True)

    @property
    def permissions(self) -> list[str]:
        return permissions_du_role(self.role)


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


class Alerte(Base):
    __tablename__ = "alertes"
    id = Column(Integer, primary_key=True, index=True)
    espace_id = Column(Integer, ForeignKey("espaces_verts.id", ondelete="CASCADE"), nullable=True, index=True)
    type_alerte_id = Column(Integer, ForeignKey("types_alertes.id"), nullable=True)
    niveau_alerte_id = Column(Integer, ForeignKey("niveaux_alertes.id"), nullable=True)
    message = Column(Text)
    est_resolue = Column(Boolean, default=False)
    cree_le = Column(DateTime(timezone=True), server_default=func.now())

    type_alerte = relationship("TypeAlerte", back_populates="alertes")
    niveau_alerte = relationship("NiveauAlerte", back_populates="alertes")


#  3. ESPACES & LOGIQUE MÉTIER
class EspaceVert(Base):
    __tablename__ = "espaces_verts"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    ville = Column(String, nullable=True)
    zone = Column(String, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    surface_m2 = Column(Float, nullable=True)
    type_espace = Column(String, nullable=False, default="Jardin", server_default="Jardin")
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
    reserve_utile_max = Column(Float, nullable=False, default=100.0, server_default="100")
    coefficient_cultural = Column(Float, nullable=False, default=1.0, server_default="1")
    cree_le = Column(DateTime(timezone=True), server_default=func.now())

    organisation_id = Column(Integer, ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    # Historique seulement : l'espace appartient à l'organisation, pas à son créateur
    cree_par = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    mesures = relationship("Mesure", back_populates="espace", cascade="all, delete-orphan", passive_deletes=True)
    bilans_hydriques = relationship("BilanHydriqueJournalier", back_populates="espace", passive_deletes=True)
    capteurs = relationship("Capteur", back_populates="espace", passive_deletes=True)
    interventions = relationship("Intervention", back_populates="espace", passive_deletes=True)
    zones = relationship("ZoneIntelligente", secondary=zone_espaces, back_populates="espaces")

    @property
    def zone_id(self) -> int | None:
        """Zone intelligente de rattachement (le clustering affecte une seule zone par espace)."""
        return self.zones[0].id if self.zones else None


class ZoneIntelligente(Base):
    __tablename__ = "zones_intelligentes"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, nullable=False)
    organisation_id = Column(Integer, ForeignKey("organisations.id", ondelete="CASCADE"), nullable=False, index=True)
    description = Column(Text, nullable=True)
    granularite = Column(String, nullable=True)
    centroid_lat = Column(Float, nullable=True)
    centroid_lon = Column(Float, nullable=True)
    rayon_km = Column(Float, nullable=True)
    sante_moyenne = Column(Float, nullable=True)
    nb_espaces = Column(Integer, nullable=False, default=0, server_default="0")

    espaces = relationship("EspaceVert", secondary=zone_espaces, back_populates="zones")


class ClusteringConfig(Base):
    """Paramètres de clustering ; organisation_id NULL = configuration par défaut de l'instance."""
    __tablename__ = "clustering_configs"
    id = Column(Integer, primary_key=True, index=True)
    nom_config = Column(String, unique=True)
    organisation_id = Column(Integer, ForeignKey("organisations.id", ondelete="CASCADE"), nullable=True, index=True)
    n_clusters = Column(Integer, nullable=False, default=5, server_default="5")
    distance_max = Column(Float, default=0.5)
    algorithme = Column(String, default="KMEANS")
    granularite = Column(String, nullable=True)
    rayon_max_km = Column(Float, nullable=True)


#  4. CAPTEURS & MESURES
class Capteur(Base):
    __tablename__ = "capteurs"
    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String)
    type = Column(String)
    emplacement = Column(String, nullable=True)
    espace_id = Column(Integer, ForeignKey("espaces_verts.id", ondelete="CASCADE"), nullable=False, index=True)
    est_actif = Column(Boolean, default=True)

    espace = relationship("EspaceVert", back_populates="capteurs")


class Mesure(Base):
    __tablename__ = "mesures"
    __table_args__ = (Index("ix_mesures_espace_timestamp", "espace_id", "timestamp"),)

    id = Column(Integer, primary_key=True, index=True)
    espace_id = Column(Integer, ForeignKey("espaces_verts.id", ondelete="CASCADE"), nullable=False)
    temperature = Column(Float)
    humidite_sol = Column(Float)
    humidite_air = Column(Float)
    co2 = Column(Float, nullable=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    espace = relationship("EspaceVert", back_populates="mesures")


# 5. ANALYSE & NOTIFICATIONS
class BilanHydriqueJournalier(Base):
    __tablename__ = "bilans_hydriques"
    __table_args__ = (
        UniqueConstraint("espace_id", "date", name="uq_bilans_hydriques_espace_date"),
        CheckConstraint(_in("statut_hydrique", STATUTS_HYDRIQUES), name="statut"),
    )

    id = Column(Integer, primary_key=True, index=True)
    espace_id = Column(Integer, ForeignKey("espaces_verts.id", ondelete="CASCADE"), nullable=False, index=True)
    # Callable : évalué à chaque insertion (et non une seule fois à l'import du module)
    date = Column(Date, nullable=False, default=date.today)
    reserve_utile_fin_journee = Column(Float, nullable=False)
    indice_stress = Column(Float, nullable=False, default=0.0)
    statut_hydrique = Column(String, nullable=False, default="Optimal")
    stress_sanitaire = Column(Float, nullable=True)

    espace = relationship("EspaceVert", back_populates="bilans_hydriques")


class Notification(Base):
    __tablename__ = "notifications"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    message = Column(String, nullable=False)
    type = Column(String, nullable=False, default="info", server_default="info")
    est_lue = Column(Boolean, nullable=False, default=False, server_default=false())
    cree_le = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    user = relationship("User", back_populates="notifications")


class ActionIrrigation(Base):
    __tablename__ = "actions_irrigation"
    id = Column(Integer, primary_key=True, index=True)
    espace_id = Column(Integer, ForeignKey("espaces_verts.id", ondelete="CASCADE"), nullable=False, index=True)
    quantite_mm = Column(Float, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


class Intervention(Base):
    """Action terrain sur un espace (arrosage, ombrage, taille…)."""
    __tablename__ = "interventions"
    __table_args__ = (
        CheckConstraint(_in("type", TYPES_INTERVENTION), name="type"),
        CheckConstraint(_in("statut", STATUTS_INTERVENTION), name="statut"),
    )

    id = Column(Integer, primary_key=True, index=True)
    espace_id = Column(Integer, ForeignKey("espaces_verts.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(30), nullable=False)
    description = Column(String(500), nullable=True)
    volume_eau_l = Column(Float, nullable=True)
    statut = Column(String(20), nullable=False, default="planifiee", server_default="planifiee")
    planifiee_le = Column(DateTime(timezone=True), nullable=True)
    realisee_le = Column(DateTime(timezone=True), nullable=True)
    cree_le = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    cree_par = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    espace = relationship("EspaceVert", back_populates="interventions")
