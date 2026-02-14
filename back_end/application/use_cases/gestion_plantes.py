# Fichier: application/use_cases/gestion_plantes.py

domain.entities import PlanteEntity
domain.ports.plante_repository import IPlanteRepository
application.dto.plante import PlantCreateDTO

def ajouter_plante_au_catalogue(
    plante_dto: PlantCreateDTO,
    plante_repo: IPlanteRepository
) -> PlanteEntity:
    """
    Use case pour ajouter une nouvelle plante au catalogue.
    La validation est gérée par le DTO Pydantic.
    """
    # Le DTO a déjà validé les données à l'instanciation.
    # On peut maintenant créer l'entité de domaine.
    nouvelle_plante = PlanteEntity(
        id=0, # L'ID sera généré par la persistance
        nom_scientifique=plante_dto.nom_scientifique,
        nom_commun=plante_dto.nom_commun,
        type_plante=plante_dto.type_plante,
        besoin_eau=plante_dto.besoin_eau,
        eau_min_mm_semaine=plante_dto.eau_min_mm_semaine,
        eau_max_mm_semaine=plante_dto.eau_max_mm_semaine,
        temp_min_confort=plante_dto.temp_min_confort,
        temp_max_confort=plante_dto.temp_max_confort,
        temp_min_survie=plante_dto.temp_min_survie,
        temp_max_survie=plante_dto.temp_max_survie,
        exposition=plante_dto.exposition,
        type_sol_prefere=plante_dto.type_sol_prefere,
        ph_min=plante_dto.ph_min,
        ph_max=plante_dto.ph_max,
        icone=plante_dto.icone,
        description_courte=plante_dto.description_courte
    )

    # Sauvegarde via le port de persistance
    plante_sauvegardee = plante_repo.sauvegarder(nouvelle_plante)

    return plante_sauvegardee