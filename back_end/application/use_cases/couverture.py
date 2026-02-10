from back_end.domain.entities import EspaceVertEntity, PlanteEntity
from back_end.domain.ports.espace import IEspaceVertRepository
from back_end.domain.ports.plante import IPlanteRepository
from back_end.domain.ports.couverture_pilotage import ICouverturePilotageService


class EnsoleillementFortError(Exception):
    """Erreur levée si les conditions d'activation ne sont pas remplies."""
    pass


def activer_couverture_si_necessaire(
    espace_id: int,
    meteo_ensoleillement_fort: bool,
    espace_repo: IEspaceVertRepository,
    plante_repo: IPlanteRepository,
    couverture_service: ICouverturePilotageService,
) -> bool:
    """
    Use case :
    - si la plante préfère 'ombre' ou 'mi-ombre'
    - ET que l'espace est en 'plein-soleil'
    - ET que la météo annonce un ensoleillement fort,
    => alors on demande au service de pilotage d'ajuster la couverture.

    Retourne True si la couverture a été activée, False sinon.
    """

    espace: EspaceVertEntity | None = espace_repo.get_by_id(espace_id)
    if espace is None:
        raise EnsoleillementFortError(f"Espace {espace_id} introuvable")

    plante: PlanteEntity | None = plante_repo.get_by_id(espace.plante_id)
    if plante is None:
        raise EnsoleillementFortError(
            f"Aucune plante associée à l'espace {espace_id}"
        )

    # Condition 1 : préférence de la plante
    if plante.exposition not in ("ombre", "mi-ombre"):
        return False

    # Condition 2 : exposition réelle de l'espace
    if espace.exposition != "plein-soleil":
        return False

    # Condition 3 : météo
    if not meteo_ensoleillement_fort:
        return False

    # Toutes les conditions sont réunies -> on pilote la couverture
    couverture_service.ajuster_couverture_pour_protection(espace)
    return True
