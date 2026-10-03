from collections.abc import Sequence

from sqlalchemy import func
from sqlalchemy.orm import Session

from domain.models import BilanHydriqueJournalier, EspaceVert, Mesure
from domain.ports.capteurs import STATUT_SANS_DONNEE, ICapteurService, LectureCapteur


class CapteurHybridService(ICapteurService):
    """Lit la dernière mesure et le dernier bilan hydrique en base.

    « Hybride » : les mesures proviennent aujourd'hui du job météo planifié
    (simulation pilotée par Open-Meteo) et demain de capteurs IoT réels,
    sans changement pour les appelants.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    def _dernieres_mesures(self, ids: list[int]) -> dict[int, Mesure]:
        derniere = (
            self.db.query(Mesure.espace_id, func.max(Mesure.timestamp).label("ts"))
            .filter(Mesure.espace_id.in_(ids))
            .group_by(Mesure.espace_id)
            .subquery()
        )
        lignes = self.db.query(Mesure).join(
            derniere, (Mesure.espace_id == derniere.c.espace_id) & (Mesure.timestamp == derniere.c.ts)
        )
        return {m.espace_id: m for m in lignes}

    def _derniers_bilans(self, ids: list[int]) -> dict[int, BilanHydriqueJournalier]:
        dernier = (
            self.db.query(BilanHydriqueJournalier.espace_id, func.max(BilanHydriqueJournalier.date).label("d"))
            .filter(BilanHydriqueJournalier.espace_id.in_(ids))
            .group_by(BilanHydriqueJournalier.espace_id)
            .subquery()
        )
        lignes = self.db.query(BilanHydriqueJournalier).join(
            dernier,
            (BilanHydriqueJournalier.espace_id == dernier.c.espace_id) & (BilanHydriqueJournalier.date == dernier.c.d),
        )
        return {b.espace_id: b for b in lignes}

    def lectures_actuelles(self, espaces: Sequence[EspaceVert]) -> list[LectureCapteur]:
        """Lectures de plusieurs espaces en 2 requêtes, quel que soit leur nombre."""
        if not espaces:
            return []
        ids = [e.id for e in espaces]
        mesures, bilans = self._dernieres_mesures(ids), self._derniers_bilans(ids)
        lectures = []
        for espace in espaces:
            mesure, bilan = mesures.get(espace.id), bilans.get(espace.id)
            lectures.append(LectureCapteur(
                espace_id=espace.id,
                nom=espace.nom,
                temperature_c=mesure.temperature if mesure else None,
                humidite_percent=mesure.humidite_sol if mesure else None,
                humidite_air_percent=mesure.humidite_air if mesure else None,
                co2_ppm=mesure.co2 if mesure else None,
                reserve_eau_mm=round(bilan.reserve_utile_fin_journee, 1) if bilan else None,
                sante_percent=round((1.0 - bilan.indice_stress) * 100, 1) if bilan else None,
                statut=bilan.statut_hydrique if bilan else STATUT_SANS_DONNEE,
                timestamp=mesure.timestamp if mesure else None,
            ))
        return lectures

    def lecture_actuelle(self, espace: EspaceVert) -> LectureCapteur:
        return self.lectures_actuelles([espace])[0]
