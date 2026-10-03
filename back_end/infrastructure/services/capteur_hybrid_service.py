from sqlalchemy import desc
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

    def lecture_actuelle(self, espace: EspaceVert) -> LectureCapteur:
        mesure = (
            self.db.query(Mesure)
            .filter(Mesure.espace_id == espace.id)
            .order_by(desc(Mesure.timestamp))
            .first()
        )
        bilan = (
            self.db.query(BilanHydriqueJournalier)
            .filter(BilanHydriqueJournalier.espace_id == espace.id)
            .order_by(desc(BilanHydriqueJournalier.date))
            .first()
        )
        return LectureCapteur(
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
        )
