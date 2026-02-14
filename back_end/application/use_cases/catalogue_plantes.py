# application/use_cases/catalogue_plantes.py
from typing import Sequence, List
from domain.entities import PlanteEntity
from domain.ports.plante_repository import IPlanteRepository
from application.dto.plante import PlantDTO

def lister_plantes_catalogue(
    plante_repo: IPlanteRepository,
) -> list[PlantDTO]:
    """
    Retourne la liste des plantes du catalogue sous forme de DTO
    pour alimenter la page Catalogue (PlantFilterBar + PlantsGrid).
    """
    plantes: Sequence[PlanteEntity] = plante_repo.list_toutes()

    result: List[PlantDTO] = []
    for p in plantes:
        result.append(
            PlantDTO(
                id=p.id,
                name=p.nom_commun,
                type=p.type_plante,
                water=p.besoin_eau,
                exposure=p.exposition,
                icon=p.icone,
            )
        )
    return result