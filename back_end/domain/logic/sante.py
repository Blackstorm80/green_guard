from typing import Dict, Any, List, Optional
from domain.entities import EspeceVegetaleEntity, EspaceVertEntity
from domain.entities.alerte import AlerteEntity, TypeAlerte, NiveauAlerte
from sqlalchemy.orm import Session

def calculer_vpd(temperature: float, humidite_relative: float) -> float:
    """
    VPD = Déficit de Pression de Vapeur 
    Formule : VPD = SVP * (1 - HR/100)
    SVP = 0.6108 * exp(17.27 * T / (T + 237.3))  # Tetens equation from https://handwiki.org/wiki/Physics:Tetens_equation
    """
    svp = 0.6108 * (2.71828 ** (17.27 * temperature / (temperature + 237.3)))
    vpd = svp * (1 - humidite_relative / 100)
    return round(vpd, 2)

def calculer_stress_hydrique(
    humidite_sol: float, 
    vpd: float, 
    espece: EspeceVegetaleEntity
) -> Dict[str, float]:
    """
    Stress hydrique = f(humidité sol, VPD, seuils espèce)
    Retourne : {stress_percent, deviation_humidite, deviation_vpd}
    """
    # Déviation humidité sol (0-100%)
    humidite_deviation = 0.0
    if humidite_sol < espece.humidite_sol_min:
        humidite_deviation = (espece.humidite_sol_min - humidite_sol) / espece.humidite_sol_min * 100
    elif humidite_sol > espece.humidite_sol_max:
        humidite_deviation = (humidite_sol - espece.humidite_sol_max) / (100 - espece.humidite_sol_max) * 100
    
    # Déviation VPD
    vpd_deviation = 0.0
    if vpd < espece.vpd_min:
        vpd_deviation = (espece.vpd_min - vpd) / espece.vpd_min * 100
    elif vpd > espece.vpd_max:
        vpd_deviation = (vpd - espece.vpd_max) / (3.0 - espece.vpd_max) * 100  # max VPD ~3kPa
    
    # Stress pondéré (VPD plus critique que sol)
    stress_hydrique = (humidite_deviation * 0.4 + vpd_deviation * 0.6)
    stress_hydrique = min(stress_hydrique, 100.0)
    
    return {
        "stress_percent": round(stress_hydrique, 1),
        "deviation_humidite": round(humidite_deviation, 1),
        "deviation_vpd": round(vpd_deviation, 1)
    }

def calculer_stress_co2(co2_ppm: float, espece: EspeceVegetaleEntity) -> float:
    """Stress CO2 simple : 0 si < seuil, augmente linéairement après"""
    if co2_ppm <= espece.co2_seuil_stress:
        return 0.0
    return min((co2_ppm - espece.co2_seuil_stress) / 1000 * 100, 100.0)

def diagnostic_sante_espace(
    espace: EspaceVertEntity,
    mesures_iot: Dict[str, float],  # temp, humidite_rel, humidite_sol, co2
    db: Session
) -> Dict[str, Any]:
    """
    Diagn complet d'un espace vert
    Combine stress de toutes ses espèces + agrégats
    """
    result = {
        "espace_id": espace.id,
        "nom": espace.nom,
        "score_global": 0.0,
        "stresses": {},
        "recommandations": [],
        "alertes_generees": []
    }
    
    # Récupérer espèces de l'espace
    especes = espace.especes_vegetales or []
    if not especes:
        result["score_global"] = espace.sante_percent or 85.0
        return result
    
    scores_especes = []
    
    for espece in especes:
        # Calculs par espèce
        vpd = calculer_vpd(mesures_iot.get("temperature", 25), mesures_iot.get("humidite_rel", 60))
        stress_hydrique = calculer_stress_hydrique(
            mesures_iot.get("humidite_sol", 40), vpd, espece
        )
        stress_co2 = calculer_stress_co2(mesures_iot.get("co2", 400), espece)
        
        score_espece = 100 - (stress_hydrique["stress_percent"] * 0.7 + stress_co2 * 0.3)
        scores_especes.append(score_espece)
        
        result["stresses"][espece.nom_commun] = {
            "score": round(score_espece, 1),
            "stress_hydrique": stress_hydrique,
            "stress_co2": round(stress_co2, 1),
            "vpd_actuel": vpd
        }
        
        # Détecter seuils critiques → générer alerte
        if stress_hydrique["stress_percent"] > 70:
            alerte = AlerteEntity(
                espace_id=espace.id,
                user_id=espace.user_id,
                type=TypeAlerte.STRESS_HYDRIQUE,
                niveau=NiveauAlerte.URGENT,
                message=f"{espece.nom_commun}: stress hydrique critique ({stress_hydrique['stress_percent']:.0f}%)",
                valeur_seuil=f"humidité {humidite_sol:.0f}% VPD {vpd:.1f}kPa"
            )
            db.add(alerte)
            result["alertes_generees"].append(alerte.message)
        
        elif stress_hydrique["stress_percent"] > 40:
            alerte = AlerteEntity(
                espace_id=espace.id,
                user_id=espace.user_id,
                type=TypeAlerte.HUMIDITE_FAIBLE,
                niveau=NiveauAlerte.WARNING,
                message=f"{espece.nom_commun}: surveiller humidité ({stress_hydrique['stress_percent']:.0f}%)",
                valeur_seuil=f"humidité {humidite_sol:.0f}%"
            )
            db.add(alerte)
            result["alertes_generees"].append(alerte.message)
    
    # Score global espace (moyenne pondérée espèces)
    result["score_global"] = round(sum(scores_especes) / len(scores_especes), 1)
    
    # Recommandations métier
    if result["score_global"] < 60:
        result["recommandations"].append("Arrosage urgent - prioriser zones rouges")
    elif result["score_global"] < 80:
        result["recommandations"].append("Arrosage préventif - surveiller évolution")
    
    db.commit()
    return result
