from collections.abc import Iterable
from datetime import date, datetime, timedelta

from sqlalchemy.dialects import postgresql, sqlite
from sqlalchemy.orm import Session, aliased

from domain.logic.secheresse import RANG_NIVEAU
from domain.models import EspaceVert, Intervention, RestrictionSecheresse, User
from domain.ports.restriction_secheresse_repository import (
    IRegistreSecheresseRepository,
    IRestrictionSecheresseRepository,
    LigneRegistre,
)
from domain.ports.vigieau import NiveauVigieau

_INSERTIONS = {"postgresql": postgresql.insert, "sqlite": sqlite.insert}


class RestrictionSecheresseRepositoryImpl(IRestrictionSecheresseRepository):
    def __init__(self, db: Session):
        self.db = db

    def get(self, espace_id: int, jour: date) -> RestrictionSecheresse | None:
        return (self.db.query(RestrictionSecheresse)
                .filter(RestrictionSecheresse.espace_id == espace_id, RestrictionSecheresse.date == jour).first())

    def plus_proche(self, espace_id: int, jour: date, fenetre_jours: int) -> RestrictionSecheresse | None:
        ecart = timedelta(days=fenetre_jours)
        voisins = (self.db.query(RestrictionSecheresse)
                   .filter(RestrictionSecheresse.espace_id == espace_id,
                           RestrictionSecheresse.date.between(jour - ecart, jour + ecart)).all())
        return min(voisins, key=lambda r: (abs((r.date - jour).days), -RANG_NIVEAU.get(r.niveau, 0)), default=None)

    def par_espaces(self, espace_ids: Iterable[int], jour: date) -> dict[int, RestrictionSecheresse]:
        ids = list(espace_ids)
        if not ids:
            return {}
        lignes = (self.db.query(RestrictionSecheresse)
                  .filter(RestrictionSecheresse.espace_id.in_(ids), RestrictionSecheresse.date == jour))
        return {r.espace_id: r for r in lignes}

    def en_vigueur(self, espace_ids: Iterable[int], jour: date,
                   fenetre_jours: int) -> dict[int, RestrictionSecheresse]:
        ids = list(espace_ids)
        if not ids:
            return {}
        lignes = (self.db.query(RestrictionSecheresse)
                  .filter(RestrictionSecheresse.espace_id.in_(ids),
                          RestrictionSecheresse.date.between(jour - timedelta(days=fenetre_jours), jour)))
        derniers: dict[int, RestrictionSecheresse] = {}
        for r in lignes:
            if r.espace_id not in derniers or r.date > derniers[r.espace_id].date:
                derniers[r.espace_id] = r
        return derniers

    def enregistrer(self, espace_id: int, jour: date, niveau: NiveauVigieau,
                    maintenant: datetime) -> RestrictionSecheresse:
        """INSERT … ON CONFLICT (espace_id, date) DO UPDATE : le worker et une requête qui relèvent le
        même espace le même jour ne se heurtent pas à la contrainte d'unicité (la seconde écriture attend
        la première puis la remplace)."""
        valeurs = {
            "niveau": niveau.niveau, "type_zone": niveau.type_zone, "zone_nom": niveau.zone_nom,
            "zone_code": niveau.zone_code, "arrete_identifiant": niveau.arrete_identifiant,
            "arrete_url": niveau.arrete_url, "recupere_le": maintenant,
        }
        insertion = _INSERTIONS.get(self.db.get_bind().dialect.name)
        if insertion is None:
            restriction = self.get(espace_id, jour) or RestrictionSecheresse(espace_id=espace_id, date=jour)
            for champ, valeur in valeurs.items():
                setattr(restriction, champ, valeur)
            self.db.add(restriction)
            self.db.flush()
            return restriction
        self.db.execute(
            insertion(RestrictionSecheresse).values(espace_id=espace_id, date=jour, **valeurs)
            .on_conflict_do_update(index_elements=["espace_id", "date"], set_=valeurs)
        )
        return (self.db.query(RestrictionSecheresse).populate_existing()
                .filter(RestrictionSecheresse.espace_id == espace_id, RestrictionSecheresse.date == jour).one())


class RegistreSecheresseRepositoryImpl(IRegistreSecheresseRepository):
    def __init__(self, db: Session):
        self.db = db

    def lister(self, organisation_id: int, debut: datetime, fin: datetime) -> list[LigneRegistre]:
        # Agent : celui qui a réalisé l'arrosage, jamais son créateur à sa place (compte supprimé : None)
        realisateur = aliased(User)
        lignes = (
            self.db.query(Intervention.realisee_le, EspaceVert.nom, EspaceVert.ville, Intervention.volume_eau_l,
                          Intervention.secheresse_niveau, Intervention.secheresse_plage_interdite,
                          Intervention.secheresse_derogation, Intervention.secheresse_zone, realisateur.name)
            .join(EspaceVert, EspaceVert.id == Intervention.espace_id)
            .outerjoin(realisateur, realisateur.id == Intervention.realisee_par)
            .filter(EspaceVert.organisation_id == organisation_id, Intervention.type == "arrosage",
                    Intervention.statut == "terminee", Intervention.realisee_le >= debut,
                    Intervention.realisee_le < fin)
            .order_by(Intervention.realisee_le, Intervention.id)
        )
        return [LigneRegistre(*ligne) for ligne in lignes]
