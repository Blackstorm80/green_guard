from application.dto.capteurs import DashboardCapteursDTO, LectureCapteurDTO, MetriquesDashboardDTO
from application.dto.meteo import MeteoDTO
from application.use_cases.meteo import obtenir_meteo_actuelle
from domain.ports.capteurs import STATUT_SANS_DONNEE, EspaceIdentifie, ICapteurService
from domain.ports.meteo import IMeteoService, MeteoIndisponibleError

SEUIL_CO2_MOYEN_PPM = 800
SEUIL_CO2_MAUVAIS_PPM = 1200
# Point de repli pour la météo extérieure quand l'utilisateur n'a aucun espace (Lyon)
LATITUDE_PAR_DEFAUT, LONGITUDE_PAR_DEFAUT = 45.764, 4.8357


def _moyenne(valeurs: list[float]) -> float | None:
    return round(sum(valeurs) / len(valeurs), 1) if valeurs else None


def _qualite_air(co2_moyen: float | None) -> str:
    if co2_moyen is None:
        return "Inconnue"
    if co2_moyen < SEUIL_CO2_MOYEN_PPM:
        return "Bonne"
    if co2_moyen < SEUIL_CO2_MAUVAIS_PPM:
        return "Moyenne"
    return "Mauvaise"


def _synthese(metrics: MetriquesDashboardDTO) -> tuple[str, str]:
    if metrics.espaces_suivis == 0:
        return "En attente", "Aucun espace vert enregistré pour le moment."
    if metrics.espaces_avec_donnees == 0:
        return "En attente", "Aucune mesure reçue : les premiers relevés arrivent au prochain cycle."
    if metrics.espaces_critiques:
        return "Critique", f"{metrics.espaces_critiques} espace(s) en stress hydrique critique."
    if metrics.espaces_stress:
        return "Attention", f"{metrics.espaces_stress} espace(s) à surveiller."
    return "Sain", "Tous les espaces suivis sont dans des conditions optimales."


def obtenir_dashboard_capteurs(
    espaces: list[EspaceIdentifie],
    capteur_service: ICapteurService,
    meteo_service: IMeteoService,
) -> DashboardCapteursDTO:
    """Tableau de bord des espaces fournis (déjà filtrés sur l'utilisateur par l'appelant)."""
    lectures = [LectureCapteurDTO.model_validate(l) for l in capteur_service.lectures_actuelles(espaces)]
    avec_donnees = [l for l in lectures if l.statut != STATUT_SANS_DONNEE]

    co2_moyen = _moyenne([l.co2_ppm for l in lectures if l.co2_ppm is not None])
    metrics = MetriquesDashboardDTO(
        sante_globale_percent=_moyenne([l.sante_percent for l in avec_donnees if l.sante_percent is not None]),
        espaces_suivis=len(lectures),
        espaces_avec_donnees=len(avec_donnees),
        espaces_stress=sum(1 for l in avec_donnees if l.statut != "Optimal"),
        espaces_critiques=sum(1 for l in avec_donnees if l.statut == "Critique"),
        co2_moyen_ppm=co2_moyen,
        qualite_air=_qualite_air(co2_moyen),
    )
    statut, message = _synthese(metrics)

    lat, lon = (espaces[0].latitude, espaces[0].longitude) if espaces else (LATITUDE_PAR_DEFAUT, LONGITUDE_PAR_DEFAUT)
    meteo: MeteoDTO | None
    try:
        meteo = obtenir_meteo_actuelle(lat, lon, meteo_service)
    except MeteoIndisponibleError:
        meteo = None

    return DashboardCapteursDTO(
        statut=statut,
        message=message,
        meteo_exterieure=meteo,
        capteurs=lectures,
        metrics=metrics,
    )
