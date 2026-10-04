from sqlalchemy import or_
from sqlalchemy.orm import Session

from domain.logic.clustering import nommer_zones, regrouper
from domain.models import ClusteringConfig, EspaceVert, ZoneIntelligente
from infrastructure.services.capteur_hybrid_service import CapteurHybridService

N_CLUSTERS_PAR_DEFAUT = 5


def _config_pour(db: Session, user_id: int) -> ClusteringConfig | None:
    """Configuration de l'utilisateur, sinon configuration par défaut de l'instance (user_id NULL)."""
    return (
        db.query(ClusteringConfig)
        .filter(or_(ClusteringConfig.user_id == user_id, ClusteringConfig.user_id.is_(None)))
        .order_by(ClusteringConfig.user_id.is_(None))  # la config personnelle passe en premier
        .first()
    )


def _sante_moyenne(espaces: list[EspaceVert], sante_par_espace: dict[int, float | None]) -> float | None:
    scores = [s for e in espaces if (s := sante_par_espace.get(e.id)) is not None]
    return round(sum(scores) / len(scores), 1) if scores else None


def reconstruire_zones(db: Session, user_id: int) -> list[ZoneIntelligente]:
    """Remplace les zones de l'utilisateur par un nouveau regroupement de ses espaces."""
    espaces = db.query(EspaceVert).filter(EspaceVert.user_id == user_id).order_by(EspaceVert.id).all()
    if not espaces:
        raise ValueError("Aucun espace vert à regrouper.")

    config = _config_pour(db, user_id)
    n_clusters = config.n_clusters if config else N_CLUSTERS_PAR_DEFAUT
    granularite = config.granularite if config else None

    groupes = regrouper([(e.latitude, e.longitude) for e in espaces], n_clusters)
    noms = nommer_zones(len(groupes), granularite)
    lectures = CapteurHybridService(db).lectures_actuelles(espaces)  # 2 requêtes pour tous les espaces
    sante_par_espace = {lecture.espace_id: lecture.sante_percent for lecture in lectures}

    db.query(ZoneIntelligente).filter(ZoneIntelligente.user_id == user_id).delete()
    zones = []
    for nom, groupe in zip(noms, groupes, strict=False):
        membres = [espaces[i] for i in groupe.indices]
        zone = ZoneIntelligente(
            nom=nom,
            user_id=user_id,
            granularite=granularite,
            centroid_lat=groupe.centroid_lat,
            centroid_lon=groupe.centroid_lon,
            rayon_km=groupe.rayon_km,
            sante_moyenne=_sante_moyenne(membres, sante_par_espace),
            nb_espaces=len(membres),
        )
        zone.espaces = membres
        db.add(zone)
        zones.append(zone)
    db.commit()
    return zones
