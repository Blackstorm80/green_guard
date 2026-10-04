from collections.abc import Sequence

from sqlalchemy import Row, func, select
from sqlalchemy.orm import Session

from domain.logic.arrosage import dose_recommandee
from domain.logic.fao56 import COEFFICIENT_PAYSAGER_DEFAUT
from domain.logic.prevision import EtatHydrique
from domain.models import BilanHydriqueJournalier, Mesure
from domain.ports.capteurs import STATUT_SANS_DONNEE, EspaceIdentifie, ICapteurService, LectureCapteur


def _arrondi(valeur: float | None) -> float | None:
    return round(valeur, 1) if valeur is not None else None


class CapteurHybridService(ICapteurService):
    """Lit la dernière mesure et le dernier bilan hydrique en base.

    « Hybride » : les mesures proviennent aujourd'hui du job météo planifié
    (simulation pilotée par Open-Meteo) et demain de capteurs IoT réels,
    sans changement pour les appelants.
    """

    def __init__(self, db_session: Session):
        self.db = db_session

    # Lecture par colonnes (et non par objets ORM complets) : le tableau de bord est la route la plus
    # sollicitée, et l'hydratation de centaines d'objets coûtait l'essentiel du temps de réponse.
    def _dernieres_mesures(self, ids: list[int]) -> dict[int, Row]:
        derniere = (
            select(Mesure.espace_id, func.max(Mesure.timestamp).label("ts"))
            .where(Mesure.espace_id.in_(ids))
            .group_by(Mesure.espace_id)
            .subquery()
        )
        requete = select(
            Mesure.espace_id, Mesure.temperature, Mesure.humidite_sol,
            Mesure.humidite_air, Mesure.co2, Mesure.timestamp,
        ).join(derniere, (Mesure.espace_id == derniere.c.espace_id) & (Mesure.timestamp == derniere.c.ts))
        return {ligne.espace_id: ligne for ligne in self.db.execute(requete)}

    def _derniers_bilans(self, ids: list[int]) -> dict[int, Row]:
        b = BilanHydriqueJournalier
        dernier = (
            select(b.espace_id, func.max(b.date).label("d"))
            .where(b.espace_id.in_(ids))
            .group_by(b.espace_id)
            .subquery()
        )
        requete = select(
            b.espace_id, b.date, b.reserve_utile_fin_journee, b.indice_stress, b.statut_hydrique,
            b.taw_mm, b.raw_mm, b.et0_mm, b.etc_mm, b.epuisement_fin_mm, b.version_modele, b.kl, b.pluie_mm,
        ).join(
            dernier, (b.espace_id == dernier.c.espace_id) & (b.date == dernier.c.d)
        )
        return {ligne.espace_id: ligne for ligne in self.db.execute(requete)}

    @staticmethod
    def _dose(bilan: Row, espace: EspaceIdentifie):
        epuisement = bilan.epuisement_fin_mm
        if epuisement is None:
            epuisement = bilan.taw_mm - bilan.reserve_utile_fin_journee
        return dose_recommandee(
            epuisement, bilan.taw_mm, getattr(espace, "surface_m2", None),
            getattr(espace, "type_irrigation", None), getattr(espace, "debit_arrosage_l_min", None),
        )

    @classmethod
    def _termes(cls, bilan: Row | None, espace: EspaceIdentifie) -> dict:
        """Termes FAO-56 du dernier bilan (restent à None pour un bilan historique-v1)."""
        if bilan is None:
            return {}
        return {
            "reserve_max_mm": _arrondi(bilan.taw_mm),
            "reserve_facilement_utilisable_mm": _arrondi(bilan.raw_mm),
            "reserve_percent": _arrondi(bilan.reserve_utile_fin_journee / bilan.taw_mm * 100)
            if bilan.taw_mm else None,
            "et0_mm": _arrondi(bilan.et0_mm),
            "etc_mm": _arrondi(bilan.etc_mm),
            "date_bilan": bilan.date,
            "version_modele": bilan.version_modele,
            "dose_recommandee": cls._dose(bilan, espace) if bilan.taw_mm is not None else None,
            "etat_hydrique": EtatHydrique(
                date=bilan.date, epuisement_mm=bilan.epuisement_fin_mm, taw_mm=bilan.taw_mm,
                kl=bilan.kl or COEFFICIENT_PAYSAGER_DEFAUT, et0_mm=bilan.et0_mm, pluie_mm=bilan.pluie_mm,
            ) if bilan.taw_mm is not None and bilan.epuisement_fin_mm is not None else None,
        }

    def lectures_actuelles(self, espaces: Sequence[EspaceIdentifie]) -> list[LectureCapteur]:
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
                **self._termes(bilan, espace),
            ))
        return lectures

    def lecture_actuelle(self, espace: EspaceIdentifie) -> LectureCapteur:
        return self.lectures_actuelles([espace])[0]
