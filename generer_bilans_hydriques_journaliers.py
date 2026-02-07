# Fichier: application/use_cases/generer_bilans_hydriques_journaliers.py

import datetime

from domain.logic.bilan_hydrique import calculer_bilan_hydrique_pour_jour
from domain.ports.bilan_hydrique_repository import IBilanHydriqueRepository
from domain.ports.espace_vert_repository import IEspaceVertRepository
from domain.ports.meteo_service import IMeteoService
from domain.ports.notification_service import INotificationService
# J'ajoute l'import du DTO comme suggéré.
# Ce chemin suppose que le DTO est défini dans application/dto/bilan_hydrique.py
from application.dto.bilan_hydrique import BilanHydriqueEspaceDTO


class EspaceVertIntrouvableError(Exception):
    """Exception levée quand un espace vert n'est pas trouvé."""
    pass


def generer_bilans_hydriques_pour_tous_les_espaces(
    date_du_calcul: datetime.date,
    espace_vert_repo: IEspaceVertRepository,
    bilan_repo: IBilanHydriqueRepository,
    meteo_service: IMeteoService,
    notification_service: INotificationService | None,
    arrosage_par_defaut_mm: float = 0.0,
) -> list[BilanHydriqueEspaceDTO]:
    """
    Use case pour calculer et enregistrer le bilan hydrique du jour pour tous les espaces verts.

    Ce cas d'usage orchestre les interactions entre les repositories et la logique métier
    pour accomplir une tâche complète.

    Returns:
        Une liste de DTOs contenant un résumé du bilan pour chaque espace.
    """
    # 1. Récupérer tous les espaces via le port de persistance
    espaces = espace_vert_repo.list_tous()

    # 2. Préparer une liste vide pour les résumés
    resultats = []

    # 3. Itérer sur chaque espace pour calculer son bilan
    for espace in espaces:
        # Récupérer le dernier bilan connu pour cet espace
        bilan_veille = bilan_repo.get_dernier_bilan_pour_espace(espace.id)

        # Appeler la fonction de domaine pure pour le calcul
        nouveau_bilan = calculer_bilan_hydrique_pour_jour(
            espace_vert=espace,
            bilan_veille=bilan_veille,
            meteo_service=meteo_service,
            arrosage_jour_mm=arrosage_par_defaut_mm,
            notification_service=notification_service,
            date_du_jour=date_du_calcul,
        )

        # Sauvegarder le résultat via le port de persistance
        bilan_repo.sauvegarder(nouveau_bilan)

        # Construire le DTO de résumé pour la valeur de retour
        resume = BilanHydriqueEspaceDTO(
            espace_id=espace.id,
            nom_espace=espace.nom,
            type_espace=espace.type_espace,
            date_bilan=date_du_calcul,
            statut_hydrique=nouveau_bilan.statut_hydrique,
            indice_stress=nouveau_bilan.indice_stress,
            localisation=espace.localisation,
            stress_sanitaire=nouveau_bilan.stress_sanitaire,
        )
        resultats.append(resume)

    # 4. Retourner la liste des résumés
    return resultats


def generer_bilan_hydrique_pour_un_espace(
    espace_id: int,
    date_du_calcul: datetime.date,
    espace_vert_repo: IEspaceVertRepository,
    bilan_repo: IBilanHydriqueRepository,
    meteo_service: IMeteoService,
    notification_service: INotificationService | None,
    arrosage_jour_mm: float = 0.0,
) -> BilanHydriqueEspaceDTO:
    """
    Calcule le bilan hydrique pour un seul espace, le sauvegarde et retourne un résumé.

    Raises:
        EspaceVertIntrouvableError: Si l'espace avec l'ID donné n'est pas trouvé.
    """
    # 1. Récupérer l'espace
    espace = espace_vert_repo.get_by_id(espace_id)
    if not espace:
        raise EspaceVertIntrouvableError(f"L'espace vert avec l'ID {espace_id} est introuvable.")

    # 2. Récupérer le dernier bilan
    bilan_veille = bilan_repo.get_dernier_bilan_pour_espace(espace_id)

    # 3. Appeler la logique métier de calcul
    nouveau_bilan = calculer_bilan_hydrique_pour_jour(
        espace_vert=espace,
        bilan_veille=bilan_veille,
        meteo_service=meteo_service,
        arrosage_jour_mm=arrosage_jour_mm,
        notification_service=notification_service,
        date_du_jour=date_du_calcul,
    )

    # 4. Sauvegarder le bilan
    bilan_repo.sauvegarder(nouveau_bilan)

    # 5. Construire le DTO de résumé à retourner
    resume = BilanHydriqueEspaceDTO(
        espace_id=espace.id,
        nom_espace=espace.nom,
        type_espace=espace.type_espace,
        date_bilan=date_du_calcul,
        statut_hydrique=nouveau_bilan.statut_hydrique,
        indice_stress=nouveau_bilan.indice_stress,
        localisation=espace.localisation,
        stress_sanitaire=nouveau_bilan.stress_sanitaire,
    )

    # 6. Retourner le résumé
    return resume