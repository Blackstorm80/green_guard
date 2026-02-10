# application/use_cases/gestion_espaces_verts.py

from back_end.domain.entities import EspaceVertEntity, PlanteEntity
from back_end.domain.ports.plante_repository import IPlanteRepository
from back_end.domain.ports.espace_vert_repository import IEspaceVertRepository
from back_end.domain.logic.compatibilite_plante_espace import (
    verifier_compatibilite_plante_espace,
)
from back_end.application.dto.espace_vert import (
    CreerEspaceDTO,
    EspaceVertDTO,
    MettreAJourEspaceVertDTO,
)


class PlanteIntrouvableError(Exception):
    """Exception levée quand une plante n'est pas trouvée dans le catalogue."""
    pass


class EspaceVertIntrouvableError(Exception):
    """Exception levée quand un espace vert n'est pas trouvé."""
    pass


class IncompatibilitePlanteEspaceError(Exception):
    """Exception levée quand une plante n'est pas compatible avec l'espace."""
    pass


def creer_espace_vert(
    data: CreerEspaceDTO,
    plante_repo: IPlanteRepository,
    espace_repo: IEspaceVertRepository,
) -> EspaceVertDTO:
    """
    Use case pour créer un nouvel espace vert, en vérifiant la compatibilité
    avec la plante choisie.
    """
    # 1. Vérifier que la plante existe
    plante = plante_repo.get_by_id(data.plante_id)
    if plante is None:
        raise PlanteIntrouvableError(f"Plante avec id={data.plante_id} introuvable.")

    # 2. Créer une entité EspaceVert temporaire pour la vérification
    espace_potentiel = EspaceVertEntity(
        id=0,  # sera remplacé par l'implémentation du repo
        nom=data.nom,
        type_espace=data.type_espace,
        localisation=data.localisation,
        plante_id=data.plante_id,
        surface_m2=data.surface_m2,
        exposition_reelle=data.exposition_reelle,
        type_sol=data.type_sol,
        ph_sol=data.ph_sol,
        reserve_utile_max=data.reserve_utile_max,
        coefficient_cultural=data.coefficient_cultural,
        zone=data.zone,
        gerant_id=data.gerant_id,
    )

    # 3. Vérifier la compatibilité globale (logique de domaine)
    compatible, raisons = verifier_compatibilite_plante_espace(
        plante=plante,
        espace=espace_potentiel,
        # temp_min_site=temp_min_site,
        # temp_max_site=temp_max_site,
    )
    if not compatible:
        raise IncompatibilitePlanteEspaceError(
            f"Incompatibilité plante-espace: {', '.join(raisons)}"
        )

    # 4. Sauvegarder via le repository
    espace_sauvegarde = espace_repo.sauvegarder(espace_potentiel)

    # 5. Mapper l'entité sauvegardée vers un DTO
    return EspaceVertDTO(
        id=espace_sauvegarde.id,
        nom=espace_sauvegarde.nom,
        type_espace=espace_sauvegarde.type_espace,
        localisation=espace_sauvegarde.localisation,
        plante_id=espace_sauvegarde.plante_id,
        surface_m2=espace_sauvegarde.surface_m2,
        exposition_reelle=espace_sauvegarde.exposition_reelle,
        type_sol=espace_sauvegarde.type_sol,
        ph_sol=espace_sauvegarde.ph_sol,
    )


def mettre_a_jour_espace_vert(
    espace_id: int,
    data: MettreAJourEspaceVertDTO,
    plante_repo: IPlanteRepository,
    espace_repo: IEspaceVertRepository,
    temp_min_site: float | None = None,
    temp_max_site: float | None = None,
) -> EspaceVertDTO:
    """
    Use case : modifier un espace vert existant en vérifiant que la plante
    associée reste compatible avec les nouvelles conditions (ou la nouvelle plante).
    """

    # 1. Charger l'espace existant
    espace = espace_repo.get_by_id(espace_id)
    if espace is None:
        raise EspaceVertIntrouvableError(
            f"Espace vert introuvable pour id={espace_id}"
        )

    # 2. Appliquer les modifications (merge)
    plante_id = data.plante_id if data.plante_id is not None else espace.plante_id

    espace_modifie = EspaceVertEntity(
        id=espace.id,
        nom=data.nom if data.nom is not None else espace.nom,
        type_espace=data.type_espace if data.type_espace is not None else espace.type_espace,
        localisation=data.localisation if data.localisation is not None else espace.localisation,
        plante_id=plante_id,
        surface_m2=data.surface_m2 if data.surface_m2 is not None else espace.surface_m2,
        exposition_reelle=(
            data.exposition_reelle
            if data.exposition_reelle is not None
            else espace.exposition_reelle
        ),
        type_sol=data.type_sol if data.type_sol is not None else espace.type_sol,
        ph_sol=data.ph_sol if data.ph_sol is not None else espace.ph_sol,
        reserve_utile_max=(
            data.reserve_utile_max
            if data.reserve_utile_max is not None
            else espace.reserve_utile_max
        ),
        coefficient_cultural=(
            data.coefficient_cultural
            if data.coefficient_cultural is not None
            else espace.coefficient_cultural
        ),
        zone=data.zone if data.zone is not None else espace.zone,
        gerant_id=data.gerant_id if data.gerant_id is not None else espace.gerant_id,
    )

    # 3. Charger la plante (nouvelle ou existante)
    plante = plante_repo.get_by_id(plante_id)
    if plante is None:
        raise PlanteIntrouvableError(f"Plante introuvable pour id={plante_id}")

    # 4. Vérifier la compatibilité plante ↔ espace modifié
    compatible, raisons = verifier_compatibilite_plante_espace(
        plante=plante,
        espace=espace_modifie,
        temp_min_site=temp_min_site,
        temp_max_site=temp_max_site,
    )
    if not compatible:
        raise IncompatibilitePlanteEspaceError(
            f"Incompatibilité plante-espace: {', '.join(raisons)}"
        )

    # 5. Persister les modifications
    espace_persisted = espace_repo.mettre_a_jour(espace_modifie)

    # 6. Construire le DTO de sortie
    return EspaceVertDTO(
        id=espace_persisted.id,
        nom=espace_persisted.nom,
        type_espace=espace_persisted.type_espace,
        localisation=espace_persisted.localisation,
        plante_id=espace_persisted.plante_id,
        surface_m2=espace_persisted.surface_m2,
        exposition_reelle=espace_persisted.exposition_reelle,
        type_sol=espace_persisted.type_sol,
        ph_sol=espace_persisted.ph_sol,
    )
