"""Génération idempotente du bilan hydrique journalier (moteur FAO-56, domain/logic/fao56.py).

Le bilan du jour J se calcule toujours à partir du dernier bilan *antérieur* à J,
puis remplace (et non ajoute) le bilan de J s'il existe déjà : on peut relancer
le calcul autant de fois que voulu dans la journée, la réserve n'est décomptée
qu'une seule fois. Les cumuls météo du jour (pluie, ET0) s'affinent à chaque passage.

Le « jour » est celui du fuseau métier (celui de la météo journalière), jamais le jour UTC :
sinon, entre minuit et 2 h à Paris, le calcul écraserait le bilan de la veille.

Rattrapage : si le dernier bilan d'un espace date de plus d'un jour (worker arrêté…), chaque jour
manquant est d'abord recalculé dans l'ordre à partir de la série météo journalière passée, puis le
jour courant. Jamais plus de SERIE_JOURS_MAX jours : au-delà, la chaîne repart du dernier bilan connu.

Recalcul immédiat : un arrosage saisi (ou retiré) recalcule aussitôt le bilan de l'espace, sans attendre
le passage horaire. S'il date d'un jour passé, les bilans existants depuis ce jour sont d'abord recalculés
dans l'ordre (série météo journalière), pour que la chaîne jusqu'au jour courant en tienne compte.
"""
import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta, tzinfo

from domain.logic.bilan_hydrique import COLONNES_CALCULEES, calculer_bilan_hydrique_pour_jour
from domain.models import BilanHydriqueJournalier, EspaceVert
from domain.ports.action_irrigation_repository import IActionIrrigationRepository
from domain.ports.bilan_hydrique_repository import IBilanHydriqueRepository
from domain.ports.meteo import SERIE_JOURS_MAX, ConditionsMeteo, IMeteoService, MeteoIndisponibleError

logger = logging.getLogger(__name__)


@dataclass
class ResultatEspace:
    espace: EspaceVert
    bilan: BilanHydriqueJournalier
    conditions: ConditionsMeteo
    jours_rattrapes: int = 0


@dataclass
class RapportGeneration:
    traites: list[ResultatEspace] = field(default_factory=list)
    ignores: list[int] = field(default_factory=list)  # ids d'espaces sans données météo exploitables


def bornes_du_jour(jour: date, fuseau: tzinfo) -> tuple[datetime, datetime]:
    """Minuit local du jour et du lendemain, en UTC (heures stockées en UTC)."""
    debut = datetime.combine(jour, time.min, tzinfo=fuseau)
    fin = datetime.combine(jour + timedelta(days=1), time.min, tzinfo=fuseau)
    return debut.astimezone(UTC), fin.astimezone(UTC)


def jour_metier(horodatage: datetime, fuseau: tzinfo) -> date:
    """Jour du fuseau métier d'un horodatage (naïf : UTC, comme le renvoie SQLite)."""
    if horodatage.tzinfo is None:
        horodatage = horodatage.replace(tzinfo=UTC)
    return horodatage.astimezone(fuseau).date()


def arrosage_journalier(action_repo: IActionIrrigationRepository, fuseau: tzinfo) -> Callable[[int, date], float]:
    """Cumul des apports d'un espace sur un jour du fuseau métier."""
    def cumul(espace_id: int, jour: date) -> float:
        return action_repo.cumul_mm(espace_id, *bornes_du_jour(jour, fuseau))
    return cumul


def calculer_bilan_du_jour(
    espace: EspaceVert,
    date_du_calcul: date,
    pluie_mm: float,
    et0_mm: float,
    arrosage_jour_mm: float,
    bilan_repo: IBilanHydriqueRepository,
    source_meteo: str | None = None,
) -> BilanHydriqueJournalier:
    precedent = bilan_repo.get_dernier_avant(espace.id, date_du_calcul)
    calcul = calculer_bilan_hydrique_pour_jour(
        espace_vert=espace,
        bilan_precedent=precedent,
        pluie_jour_mm=pluie_mm,
        et0_jour_mm=et0_mm,
        arrosage_jour_mm=arrosage_jour_mm,
        date_du_jour=date_du_calcul,
        stress_sanitaire_jour=None,
        source_meteo=source_meteo,
    )

    existant = bilan_repo.get_by_espace_and_date(espace.id, date_du_calcul)
    if existant is None:
        return bilan_repo.save(calcul)
    for colonne in COLONNES_CALCULEES:
        setattr(existant, colonne, getattr(calcul, colonne))
    return bilan_repo.save(existant)


def jours_a_rattraper(dernier_bilan: date | None, date_du_calcul: date) -> list[date]:
    """Jours manquants entre le dernier bilan et la veille du calcul, au plus SERIE_JOURS_MAX (les plus récents)."""
    if dernier_bilan is None:
        return []
    debut = max(dernier_bilan + timedelta(days=1), date_du_calcul - timedelta(days=SERIE_JOURS_MAX))
    return [debut + timedelta(days=i) for i in range((date_du_calcul - debut).days)]


def rattraper_jours_manquants(
    espace: EspaceVert,
    date_du_calcul: date,
    bilan_repo: IBilanHydriqueRepository,
    meteo_service: IMeteoService,
    arrosage_du_jour_mm: Callable[[int, date], float],
) -> int:
    """Recalcule dans l'ordre les jours sans bilan avant date_du_calcul ; renvoie le nombre de jours rattrapés.

    Lève MeteoIndisponibleError si la série est indisponible ou incomplète : aucun jour n'est alors
    écrit, pour ne jamais enchaîner un bilan sur un trou (le rattrapage sera retenté au passage suivant).
    """
    precedent = bilan_repo.get_dernier_avant(espace.id, date_du_calcul)
    jours = jours_a_rattraper(precedent.date if precedent else None, date_du_calcul)
    if not jours:
        return 0
    serie = {
        j.jour: j for j in meteo_service.recuperer_serie_journaliere(espace.latitude, espace.longitude,
                                                                     jours[0], jours[-1])
    }
    manquants = [jour for jour in jours if jour not in serie or serie[jour].et0_mm is None]
    if manquants:
        raise MeteoIndisponibleError(f"Série météo incomplète ({len(manquants)} jour(s) sans ET0)")
    for jour in jours:
        meteo_jour = serie[jour]
        calculer_bilan_du_jour(
            espace=espace, date_du_calcul=jour, pluie_mm=meteo_jour.pluie_mm, et0_mm=meteo_jour.et0_mm,
            arrosage_jour_mm=arrosage_du_jour_mm(espace.id, jour), bilan_repo=bilan_repo,
            source_meteo=meteo_jour.source,
        )
    logger.info("Espace %s : %d jour(s) de bilan rattrapé(s) (%s → %s).", espace.id, len(jours), jours[0], jours[-1])
    return len(jours)


def generer_bilans_hydriques_journaliers(
    espaces: Iterable[EspaceVert],
    bilan_repo: IBilanHydriqueRepository,
    meteo_service: IMeteoService,
    arrosage_du_jour_mm: Callable[[int, date], float],
    fuseau: tzinfo,
    maintenant: datetime | None = None,
) -> RapportGeneration:
    maintenant = maintenant or datetime.now(UTC)
    date_du_calcul = maintenant.astimezone(fuseau).date()
    rapport = RapportGeneration()

    for espace in espaces:
        try:
            conditions = meteo_service.recuperer_conditions_actuelles(espace.latitude, espace.longitude, maintenant)
            if conditions.et0_jour_mm is None:
                logger.warning("ET0 absente pour l'espace %s : bilan ignoré.", espace.id)
                rapport.ignores.append(espace.id)
                continue
            rattrapes = rattraper_jours_manquants(espace, date_du_calcul, bilan_repo, meteo_service,
                                                  arrosage_du_jour_mm)
        except MeteoIndisponibleError as exc:
            logger.warning("Météo indisponible pour l'espace %s : %s", espace.id, exc)
            rapport.ignores.append(espace.id)
            continue

        bilan = calculer_bilan_du_jour(
            espace=espace,
            date_du_calcul=date_du_calcul,
            pluie_mm=conditions.pluie_jour_mm,
            et0_mm=conditions.et0_jour_mm,
            arrosage_jour_mm=arrosage_du_jour_mm(espace.id, date_du_calcul),
            bilan_repo=bilan_repo,
            source_meteo=conditions.source,
        )
        rapport.traites.append(ResultatEspace(espace=espace, bilan=bilan, conditions=conditions,
                                              jours_rattrapes=rattrapes))

    return rapport


def recorriger_jours_passes(
    espace: EspaceVert,
    depuis: date,
    date_du_calcul: date,
    bilan_repo: IBilanHydriqueRepository,
    meteo_service: IMeteoService,
    arrosage_du_jour_mm: Callable[[int, date], float],
) -> int:
    """Recalcule dans l'ordre les bilans existants de [depuis, date_du_calcul[ ; renvoie leur nombre.

    Tout ou rien, comme le rattrapage : MeteoIndisponibleError si un jour n'a pas d'ET0, rien n'est écrit.
    """
    borne = max(depuis, date_du_calcul - timedelta(days=SERIE_JOURS_MAX))
    jours = [b.date for b in bilan_repo.lister_depuis(espace.id, borne) if b.date < date_du_calcul]
    if not jours:
        return 0
    serie = {
        j.jour: j for j in meteo_service.recuperer_serie_journaliere(espace.latitude, espace.longitude,
                                                                     jours[0], jours[-1])
    }
    if any(jour not in serie or serie[jour].et0_mm is None for jour in jours):
        raise MeteoIndisponibleError("Série météo incomplète pour corriger les jours passés")
    for jour in jours:
        calculer_bilan_du_jour(
            espace=espace, date_du_calcul=jour, pluie_mm=serie[jour].pluie_mm, et0_mm=serie[jour].et0_mm,
            arrosage_jour_mm=arrosage_du_jour_mm(espace.id, jour), bilan_repo=bilan_repo,
            source_meteo=serie[jour].source,
        )
    return len(jours)


def recalculer_bilan_espace(
    espace: EspaceVert,
    depuis: date,
    bilan_repo: IBilanHydriqueRepository,
    meteo_service: IMeteoService,
    arrosage_du_jour_mm: Callable[[int, date], float],
    fuseau: tzinfo,
    maintenant: datetime | None = None,
) -> RapportGeneration:
    """Recalcul immédiat après un changement des apports d'eau datés du jour `depuis` (fuseau métier)."""
    maintenant = maintenant or datetime.now(UTC)
    date_du_calcul = maintenant.astimezone(fuseau).date()
    if depuis < date_du_calcul:
        try:
            recorriger_jours_passes(espace, depuis, date_du_calcul, bilan_repo, meteo_service, arrosage_du_jour_mm)
        except MeteoIndisponibleError as exc:
            # Le jour courant reste recalculé ; les jours passés gardent leur bilan
            logger.warning("Espace %s : jours passés non corrigés depuis le %s (%s).", espace.id, depuis, exc)
    return generer_bilans_hydriques_journaliers(
        [espace], bilan_repo, meteo_service, arrosage_du_jour_mm, fuseau, maintenant,
    )
