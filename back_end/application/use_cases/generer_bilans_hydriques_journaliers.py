# Fichier: application/use_cases/generer_bilans_hydriques_journaliers.py

from datetime import date
from typing import List

from domain.entities import EspaceVertEntity, BilanHydriqueJournalierEntity
from domain.logic.bilan_hydrique import calculer_bilan_hydrique_pour_jour
from domain.logic.stress_sanitaire import calculer_stress_sanitaire_jour
from domain.ports.bilan_hydrique_repository import IBilanHydriqueRepository
from domain.ports.espace_vert_repository import IEspaceVertRepository
from domain.ports.meteo_service import IMeteoService
from domain.ports.notification_service import INotificationService
from application.dto.bilan_hydrique import BilanHydriqueEspaceDTO


class EspaceVertIntrouvableError(Exception):
    """Exception levée quand un espace vert n'est pas trouvé."""
    pass


def generer_bilans_hydriques_pour_tous_les_espaces(
    date_du_calcul: date,
    espace_vert_repo: IEspaceVertRepository,
    bilan_repo: IBilanHydriqueRepository,
    meteo_service: IMeteoService,
    notification_service: INotificationService | None,
    arrosage_par_defaut_mm: float = 0.0,
) -> list[BilanHydriqueEspaceDTO]:
    """
    Cas d'usage "vue d'ensemble" : pour une date donnée, on fait le tour
    de tous les espaces verts, on calcule leur bilan hydrique (et, si possible,
    leur stress sanitaire), on enregistre tout, puis on renvoie un résumé
    pour chacun.

    C'est la couche "chef d'orchestre" : elle va chercher les données,
    appelle la logique métier, déclenche les notifications, et prépare
    les DTO pour l'API.
    """

    resultats: list[BilanHydriqueEspaceDTO] = []

    # 1. On commence par demander au repository la "liste de tous les jardins".
    espaces = espace_vert_repo.list_tous()

    # 2. On parcourt chaque espace comme si on faisait une tournée de contrôle.
    for espace in espaces:
        # 2.1. On regarde ce qui s'est passé la veille pour cet espace.
        #      S'il n'y a jamais eu de bilan, on partira d'une réserve pleine.
        bilan_precedent: BilanHydriqueJournalierEntity | None = (
            bilan_repo.get_dernier_bilan_pour_espace(espace.id)
        )

        # 2.2. On récupère la météo journalière dont la logique hydrique a besoin :
        #      typiquement pluie et ET0. La forme exacte de "donnees_meteo_jour"
        #      dépend de ton implémentation du service météo.
        donnees_meteo_jour = meteo_service.get_donnees_meteo_jour(
            espace=espace,
            date_du_jour=date_du_calcul,
        )
        pluie_jour_mm = donnees_meteo_jour.pluie_mm      # pluie du jour (en mm)
        et0_jour_mm = donnees_meteo_jour.et0_mm          # ET0 du jour (en mm)

        # 2.3. Pour l'instant, on utilise un arrosage "par défaut" commun à tous
        #      les espaces. Plus tard, tu pourras brancher un arrosage spécifique
        #      par espace si tu as cette info.
        arrosage_jour_mm = arrosage_par_defaut_mm

        # 2.4. Tentative de calcul du stress sanitaire :
        #      si la météo horaire est disponible, on la transforme en stress (0–1).
        #      Sinon, on reste sur None sans casser le reste du flux.
        stress_sanitaire_jour: float | None
        try:
            # Le service météo nous donne les "films" horaires de T et H.
            temperatures_horaires, humidites_horaires = meteo_service.get_donnees_meteo_horaires(
                espace=espace,
                date_du_jour=date_du_calcul,
            )

            # On demande ensuite au cerveau sanitaire de résumer ce film en une note 0–1.
            stress_sanitaire_jour = calculer_stress_sanitaire_jour(
                temperatures_horaires=temperatures_horaires,
                humidites_horaires=humidites_horaires,
            )
        except Exception:
            # Si quelque chose ne va pas (service pas prêt, données manquantes, etc.),
            # on ne bloque pas le calcul hydrique : on se contente de dire
            # "pas de stress sanitaire calculé aujourd'hui".
            stress_sanitaire_jour = None

            # En bonus, on peut prévenir un service de notification pour que
            # quelqu'un jette un œil à la météo.
            if notification_service is not None:
                notification_service.notifier_meteo_indisponible(espace, date_du_calcul)

        # 2.5. Maintenant qu'on a toutes les "ingrédients" (pluie, ET0, arrosage,
        #      bilan précédent, stress sanitaire éventuel), on appelle la vraie
        #      logique de domaine hydrique.
        nouveau_bilan = calculer_bilan_hydrique_pour_jour(
            espace_vert=espace,
            bilan_precedent=bilan_precedent,
            pluie_jour_mm=donnees_meteo_jour.pluie_mm,
            et0_jour_mm=donnees_meteo_jour.et0_mm,
            arrosage_jour_mm=arrosage_jour_mm,
            date_du_jour=date_du_calcul,
            stress_sanitaire_jour=stress_sanitaire_jour,
        )

        # 2.6. On enregistre ce nouveau bilan dans la base via le repository.
        bilan_repo.sauvegarder(nouveau_bilan)

        # 2.7. Si la situation hydrique est critique, on en profite pour
        #      déclencher une alerte (mail, SMS, etc.) via le service de notification.
        if nouveau_bilan.statut_hydrique == "Critique" and notification_service is not None:
            notification_service.notifier_stress_hydrique(
                nom_espace=espace.nom,
                statut=nouveau_bilan.statut_hydrique,
                indice_stress=nouveau_bilan.indice_stress,
            )

        # 2.8. Enfin, on transforme le résultat métier en DTO propre pour la couche API.
        #      Ce DTO est ce qui sera renvoyé aux clients (front, intégrations, etc.).
        resume = BilanHydriqueEspaceDTO(
            espace_id=espace.id,
            nom_espace=espace.nom,
            type_espace=espace.type_espace,
            date_bilan=date_du_calcul,
            statut_hydrique=nouveau_bilan.statut_hydrique,
            indice_stress=nouveau_bilan.indice_stress,
            localisation=espace.localisation,
            stress_sanitaire=nouveau_bilan.stress_sanitaire,
            co2_absorbe_jour=nouveau_bilan.co2_absorbe_jour,
            o2_produit_jour=nouveau_bilan.o2_produit_jour,
        )
        resultats.append(resume)

    # 3. À la fin de la tournée, on renvoie la liste des résumés pour tous les espaces.
    return resultats


def generer_bilan_hydrique_pour_un_espace(
    espace_id: int,
    date_du_calcul: date,
    espace_vert_repo: IEspaceVertRepository,
    bilan_repo: IBilanHydriqueRepository,
    meteo_service: IMeteoService,
    notification_service: INotificationService | None,
    arrosage_jour_mm: float = 0.0,
) -> BilanHydriqueEspaceDTO:
    """
    Cas d'usage "focus" : pour une date donnée, on calcule le bilan hydrique
    (et éventuellement sanitaire) d'un seul espace vert, on l'enregistre,
    puis on renvoie un résumé prêt pour l'API.

    C'est la version "zoom" de la tournée globale.

    Raises:
        EspaceVertIntrouvableError: Si l'espace avec l'ID donné n'est pas trouvé.
    """

    # 1. Récupérer l'espace ciblé.
    espace = espace_vert_repo.get_par_id(espace_id)
    if espace is None:
        raise EspaceVertIntrouvableError(f"Espace vert introuvable pour id={espace_id}")

    # 2. Récupérer le bilan précédent s'il existe.
    bilan_precedent: BilanHydriqueJournalierEntity | None = (
        bilan_repo.get_dernier_bilan_pour_espace(espace.id)
    )

    # 3. Récupérer la météo journalière nécessaire au calcul hydrique
    #    (pluie, ET0, etc. — à adapter à ton modèle réel).
    donnees_meteo_jour = meteo_service.get_donnees_meteo_jour(
        espace=espace,
        date_du_jour=date_du_calcul,
    )
    pluie_jour_mm = donnees_meteo_jour.pluie_mm
    et0_jour_mm = donnees_meteo_jour.et0_mm

    # 4. L'arrosage du jour : ici passé en paramètre (par défaut 0).
    #    Plus tard, tu pourras le déduire d'un autre service si besoin.
    #    arrosage_jour_mm est donc la "dose d'eau manuelle" pour cet espace.
    #    (différente de la pluie).
    # -> déjà fourni en paramètre.

    # 5. Calculer éventuellement le stress sanitaire si la météo horaire est dispo.
    stress_sanitaire_jour: float | None
    try:
        temperatures_horaires, humidites_horaires = meteo_service.get_donnees_meteo_horaires(
            espace=espace,
            date_du_jour=date_du_calcul,
        )
        stress_sanitaire_jour = calculer_stress_sanitaire_jour(
            temperatures_horaires=temperatures_horaires,
            humidites_horaires=humidites_horaires,
        )
    except Exception:
        # Si la météo horaire n'est pas prête ou plante, on n'empêche pas
        # le calcul hydrique de se faire. On laisse simplement le stress
        # sanitaire à None pour cette journée.
        stress_sanitaire_jour = None
        if notification_service is not None:
            notification_service.notifier_meteo_indisponible(espace, date_du_calcul)

    # 6. Appeler la logique de domaine hydrique (cœur de l'oignon).
    nouveau_bilan = calculer_bilan_hydrique_pour_jour(
        espace_vert=espace,
        bilan_precedent=bilan_precedent,
        pluie_jour_mm=donnees_meteo_jour.pluie_mm,
        et0_jour_mm=donnees_meteo_jour.et0_mm,
        arrosage_jour_mm=arrosage_jour_mm,
        date_du_jour=date_du_calcul,
        stress_sanitaire_jour=stress_sanitaire_jour,
    )

    # 7. Sauvegarder ce nouveau bilan.
    bilan_repo.sauvegarder(nouveau_bilan)

    # 8. Si la situation hydrique est critique, déclencher une notification.
    if nouveau_bilan.statut_hydrique == "Critique" and notification_service is not None:
        notification_service.notifier_stress_hydrique(
            nom_espace=espace.nom,
            statut=nouveau_bilan.statut_hydrique,
            indice_stress=nouveau_bilan.indice_stress,
        )

    # 9. Construire le DTO de résumé pour la couche API / clients.
    resume = BilanHydriqueEspaceDTO(
        espace_id=espace.id,
        nom_espace=espace.nom,
        type_espace=espace.type_espace,
        date_bilan=date_du_calcul,
        statut_hydrique=nouveau_bilan.statut_hydrique,
        indice_stress=nouveau_bilan.indice_stress,
        localisation=espace.localisation,
        stress_sanitaire=nouveau_bilan.stress_sanitaire,
        co2_absorbe_jour=nouveau_bilan.co2_absorbe_jour,
        o2_produit_jour=nouveau_bilan.o2_produit_jour,
    )

    # 10. Retourner le résumé.
    return resume