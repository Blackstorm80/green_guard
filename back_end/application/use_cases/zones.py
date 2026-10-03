from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session

from domain.logic.clustering import nommer_zones, regrouper
from domain.models import ClusteringConfig, EspaceVert, ZoneIntelligente
from infrastructure.repositories.bilan_hydrique_repository_impl import BilanHydriqueRepositoryImpl

N_CLUSTERS_PAR_DEFAUT = 5


def _config_pour(db: Session, user_id: int) -> Optional[ClusteringConfig]:
    """Configuration de l'utilisateur, sinon configuration par défaut de l'instance (user_id NULL)."""
    return (
        db.query(ClusteringConfig)
        .filter(or_(ClusteringConfig.user_id == user_id, ClusteringConfig.user_id.is_(None)))
        .order_by(ClusteringConfig.user_id.is_(None))  # la config personnelle passe en premier
        .first()
    )


def _sante_moyenne(espaces: List[EspaceVert], bilans: BilanHydriqueRepositoryImpl) -> Optional[float]:
    scores = []
    for espace in espaces:
        bilan = bilans.get_dernier_bilan_pour_espace(espace.id)
        if bilan is not None:
            scores.append((1.0 - bilan.indice_stress) * 100)
    return round(sum(scores) / len(scores), 1) if scores else None


def reconstruire_zones(db: Session, user_id: int) -> List[ZoneIntelligente]:
    """Remplace les zones de l'utilisateur par un nouveau regroupement de ses espaces."""
    espaces = db.query(EspaceVert).filter(EspaceVert.user_id == user_id).order_by(EspaceVert.id).all()
    if not espaces:
        raise ValueError("Aucun espace vert à regrouper.")

    config = _config_pour(db, user_id)
    n_clusters = config.n_clusters if config else N_CLUSTERS_PAR_DEFAUT
    granularite = config.granularite if config else None

    groupes = regrouper([(e.latitude, e.longitude) for e in espaces], n_clusters)
    noms = nommer_zones(len(groupes), granularite)
    bilans = BilanHydriqueRepositoryImpl(db)

    db.query(ZoneIntelligente).filter(ZoneIntelligente.user_id == user_id).delete()
    zones = []
    for nom, groupe in zip(noms, groupes):
        membres = [espaces[i] for i in groupe.indices]
        zone = ZoneIntelligente(
            nom=nom,
            user_id=user_id,
            granularite=granularite,
            centroid_lat=groupe.centroid_lat,
            centroid_lon=groupe.centroid_lon,
            rayon_km=groupe.rayon_km,
            sante_moyenne=_sante_moyenne(membres, bilans),
            nb_espaces=len(membres),
        )
        zone.espaces = membres
        db.add(zone)
        zones.append(zone)
    db.commit()
    return zones
