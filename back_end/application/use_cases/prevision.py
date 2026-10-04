"""Prévision à 7 jours (domain/logic/prevision.py) : par espace, pour le tableau de bord et pour le worker.

La météo prévue est lue par point (cache du service météo, ~10 km) : deux espaces voisins ne coûtent
qu'un appel. Si le fournisseur est indisponible, la prévision est simplement absente.
"""
import logging
from collections.abc import Sequence
from datetime import UTC, date, datetime, tzinfo

from application.dto.capteurs import DecisionDTO, DoseRecommandeeDTO
from application.dto.prevision import JourPrevisionDTO, PrevisionDTO
from domain.logic.fao56 import COEFFICIENT_PAYSAGER_DEFAUT
from domain.logic.prevision import Decision, EtatHydrique, Prevision, PrevisionImpossibleError, prevoir
from domain.logic.secheresse import EvaluationArrosage, appliquer_restriction
from domain.models import BilanHydriqueJournalier
from domain.ports.bilan_hydrique_repository import IBilanHydriqueRepository
from domain.ports.capteurs import EspaceIdentifie, LectureCapteur
from domain.ports.meteo import IMeteoService, MeteoIndisponibleError, PrevisionJournaliere

logger = logging.getLogger(__name__)


def etat_du_bilan(bilan: BilanHydriqueJournalier | None) -> EtatHydrique | None:
    """Point de départ de la projection ; None sans bilan ou pour un bilan antérieur au modèle FAO-56."""
    if bilan is None or bilan.taw_mm is None or bilan.epuisement_fin_mm is None:
        return None
    return EtatHydrique(date=bilan.date, epuisement_mm=bilan.epuisement_fin_mm, taw_mm=bilan.taw_mm,
                        kl=bilan.kl or COEFFICIENT_PAYSAGER_DEFAUT, et0_mm=bilan.et0_mm, pluie_mm=bilan.pluie_mm)


def _prevoir(espace: EspaceIdentifie, etat: EtatHydrique, previsions: Sequence[PrevisionJournaliere],
             aujourd_hui: date) -> Prevision:
    return prevoir(etat, previsions, aujourd_hui, getattr(espace, "surface_m2", None),
                   getattr(espace, "type_irrigation", None), getattr(espace, "debit_arrosage_l_min", None))


def prevoir_espace(espace: EspaceIdentifie, etat: EtatHydrique, meteo_service: IMeteoService,
                   aujourd_hui: date) -> Prevision:
    """Propage MeteoIndisponibleError et PrevisionImpossibleError."""
    previsions = meteo_service.recuperer_prevision_journaliere(espace.latitude, espace.longitude)
    return _prevoir(espace, etat, previsions, aujourd_hui)


def decision_dto(decision: Decision) -> DecisionDTO:
    return DecisionDTO(
        code=decision.code, texte=decision.texte, date_limite=decision.date_limite,
        jour_pluie=decision.jour_pluie,
        pluie_attendue_mm=round(decision.pluie_attendue_mm, 1) if decision.pluie_attendue_mm is not None else None,
        dose_recommandee=DoseRecommandeeDTO.model_validate(decision.dose) if decision.dose else None,
        plage_interdite=decision.plage_interdite, derogation=decision.derogation,
    )


def _arrondi(valeur: float | None) -> float | None:
    return round(valeur, 1) if valeur is not None else None


def prevision_de_l_espace(
    espace: EspaceIdentifie,
    bilan_repo: IBilanHydriqueRepository,
    meteo_service: IMeteoService,
    fuseau: tzinfo,
    maintenant: datetime | None = None,
    evaluation: EvaluationArrosage | None = None,
) -> PrevisionDTO:
    """Prévision détaillée d'un espace (déjà contrôlé sur l'organisation par l'appelant).

    evaluation : restriction sécheresse du jour, appliquée à la décision (jamais d'arrosage interdit conseillé).

    Lève PrevisionImpossibleError (pas de bilan FAO-56 récent, prévision incomplète) et MeteoIndisponibleError.
    """
    aujourd_hui = (maintenant or datetime.now(UTC)).astimezone(fuseau).date()
    etat = etat_du_bilan(bilan_repo.get_dernier_bilan_pour_espace(espace.id))
    if etat is None:
        raise PrevisionImpossibleError("Aucun bilan hydrique exploitable pour cet espace")
    previsions = meteo_service.recuperer_prevision_journaliere(espace.latitude, espace.longitude)
    prevision = _prevoir(espace, etat, previsions, aujourd_hui)
    return PrevisionDTO(
        espace_id=espace.id,
        date_calcul=aujourd_hui,
        date_bilan=etat.date,
        reserve_max_mm=round(etat.taw_mm, 1),
        jours=[
            JourPrevisionDTO(
                jour=j.jour, reserve_mm=round(j.reserve_mm, 1), reserve_percent=_arrondi(j.reserve_percent),
                statut=j.statut, et0_mm=_arrondi(j.et0_mm), pluie_mm=round(j.pluie_mm, 1),
                probabilite_pluie_pct=j.probabilite_pluie_pct, pluie_comptee_mm=round(j.pluie_comptee_mm, 1),
                pluie_acquise=j.pluie_acquise, indicatif=j.indicatif, issu_du_bilan=j.issu_du_bilan,
            )
            for j in prevision.jours
        ],
        date_bascule_a_surveiller=prevision.date_bascule_a_surveiller,
        date_bascule_critique=prevision.date_bascule_critique,
        decision=decision_dto(appliquer_restriction(prevision.decision, evaluation, aujourd_hui)),
        avertissement=prevision.avertissement,
        source_meteo=next((p.source for p in previsions if p.source), None),
    )


def previsions_des_lectures(
    espaces: Sequence[EspaceIdentifie],
    lectures: Sequence[LectureCapteur],
    meteo_service: IMeteoService,
    aujourd_hui: date,
) -> dict[int, Prevision]:
    """Prévision de chaque espace lu (tableau de bord) ; absente si la météo ou le bilan manque.

    Au premier échec du fournisseur, les points suivants ne sont pas interrogés : la panne est générale
    et chaque tentative coûterait un délai d'attente à la lecture du tableau de bord.
    """
    par_id = {e.id: e for e in espaces}
    resultat: dict[int, Prevision] = {}
    for lecture in lectures:
        espace = par_id.get(lecture.espace_id)
        if espace is None or lecture.etat_hydrique is None:
            continue
        try:
            resultat[espace.id] = prevoir_espace(espace, lecture.etat_hydrique, meteo_service, aujourd_hui)
        except PrevisionImpossibleError as exc:
            logger.debug("Prévision indisponible pour l'espace %s : %s", espace.id, exc)
        except MeteoIndisponibleError as exc:
            logger.warning("Prévision météo indisponible (tableau de bord) : %s", exc)
            break
        except Exception:
            # Fonction secondaire : une donnée inattendue prive l'espace de prévision, pas le tableau de bord
            logger.exception("Échec de la prévision de l'espace %s (tableau de bord)", espace.id)
    return resultat
