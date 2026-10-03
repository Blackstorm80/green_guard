"""Génération idempotente du bilan hydrique journalier.

Le bilan du jour J se calcule toujours à partir du dernier bilan *antérieur* à J,
puis remplace (et non ajoute) le bilan de J s'il existe déjà : on peut relancer
le calcul autant de fois que voulu dans la journée, la réserve n'est décomptée
qu'une seule fois. Les cumuls météo du jour (pluie, ET0) s'affinent à chaque passage.
"""
import logging
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from domain.logic.bilan_hydrique import calculer_bilan_hydrique_pour_jour
from domain.models import BilanHydriqueJournalier, EspaceVert
from domain.ports.bilan_hydrique_repository import IBilanHydriqueRepository
from domain.ports.meteo import ConditionsMeteo, IMeteoService, MeteoIndisponibleError

logger = logging.getLogger(__name__)


@dataclass
class ResultatEspace:
    espace: EspaceVert
    bilan: BilanHydriqueJournalier
    conditions: ConditionsMeteo


@dataclass
class RapportGeneration:
    traites: list[ResultatEspace] = field(default_factory=list)
    ignores: list[int] = field(default_factory=list)  # ids d'espaces sans données météo exploitables


def calculer_bilan_du_jour(
    espace: EspaceVert,
    date_du_calcul: date,
    conditions: ConditionsMeteo,
    arrosage_jour_mm: float,
    bilan_repo: IBilanHydriqueRepository,
) -> BilanHydriqueJournalier:
    precedent = bilan_repo.get_dernier_avant(espace.id, date_du_calcul)
    calcul = calculer_bilan_hydrique_pour_jour(
        espace_vert=espace,
        bilan_precedent=precedent,
        pluie_jour_mm=conditions.pluie_jour_mm,
        et0_jour_mm=conditions.et0_jour_mm,
        arrosage_jour_mm=arrosage_jour_mm,
        date_du_jour=date_du_calcul,
        stress_sanitaire_jour=None,
    )

    existant = bilan_repo.get_by_espace_and_date(espace.id, date_du_calcul)
    if existant is None:
        return bilan_repo.save(calcul)

    existant.reserve_utile_fin_journee = calcul.reserve_utile_fin_journee
    existant.indice_stress = calcul.indice_stress
    existant.statut_hydrique = calcul.statut_hydrique
    existant.stress_sanitaire = calcul.stress_sanitaire
    return bilan_repo.save(existant)


def generer_bilans_hydriques_journaliers(
    espaces: Iterable[EspaceVert],
    bilan_repo: IBilanHydriqueRepository,
    meteo_service: IMeteoService,
    arrosage_du_jour_mm: Callable[[int, date], float],
    date_du_calcul: date | None = None,
) -> RapportGeneration:
    date_du_calcul = date_du_calcul or date.today()
    maintenant = datetime.now(UTC)
    rapport = RapportGeneration()

    for espace in espaces:
        try:
            conditions = meteo_service.recuperer_conditions_actuelles(espace.latitude, espace.longitude, maintenant)
        except MeteoIndisponibleError:
            rapport.ignores.append(espace.id)
            continue
        if conditions.et0_jour_mm is None:
            logger.warning("ET0 absente pour l'espace %s : bilan ignoré.", espace.id)
            rapport.ignores.append(espace.id)
            continue

        bilan = calculer_bilan_du_jour(
            espace=espace,
            date_du_calcul=date_du_calcul,
            conditions=conditions,
            arrosage_jour_mm=arrosage_du_jour_mm(espace.id, date_du_calcul),
            bilan_repo=bilan_repo,
        )
        rapport.traites.append(ResultatEspace(espace=espace, bilan=bilan, conditions=conditions))

    return rapport
