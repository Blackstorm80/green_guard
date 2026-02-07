# Fichier : domain/logic/stress_sanitaire.py

from typing import Sequence


def calculer_stress_sanitaire_jour(
    temperatures_horaires: Sequence[float],
    humidites_horaires: Sequence[float],
) -> float:
    """
    Calcule un indice de stress sanitaire journalier entre 0 et 1
    à partir de séries horaires de température et d'humidité.

    - 0 : pas de stress sanitaire lié aux conditions T/H
    - 1 : stress sanitaire maximal (conditions très défavorables)

    La logique actuelle est volontairement simple et paramétrable :
    - zone de confort température : 15–24 °C
    - zone de confort humidité : 40–70 %
    - au-delà de ces zones, le stress augmente linéairement jusqu'à 1
      à partir d'extrêmes (5 °C, 35 °C, 20 %, 90 %).
    """

    # Sécurité : si listes vides ou None, on retourne 0.0 par défaut.
    if not temperatures_horaires or not humidites_horaires:
        return 0.0

    n = min(len(temperatures_horaires), len(humidites_horaires))
    if n == 0:
        return 0.0

    scores_horaires: list[float] = []

    for i in range(n):
        T = float(temperatures_horaires[i])
        H = float(humidites_horaires[i])

        score_T = _score_thermique(T)
        score_H = _score_humidite(H)

        # Combinaison simple : moyenne des deux scores
        score_horaire = (score_T + score_H) / 2.0
        scores_horaires.append(score_horaire)

    # Moyenne journalière
    stress_moyen = sum(scores_horaires) / len(scores_horaires)

    # Clamp dans [0, 1] pour robustesse
    stress_normalise = max(0.0, min(1.0, stress_moyen))
    return stress_normalise


def _score_thermique(T: float) -> float:
    """
    Retourne un score de stress thermique entre 0 et 1 pour une température T (°C).

    Zone de confort : 15–24 °C -> score 0.
    Extrêmes : <= 5 °C ou >= 35 °C -> score 1.
    Transition linéaire entre ces bornes.
    """
    zone_min = 15.0
    zone_max = 24.0
    min_extreme = 5.0   # en dessous : stress max
    max_extreme = 35.0  # au-dessus : stress max

    # Zone neutre
    if zone_min <= T <= zone_max:
        return 0.0

    # Froid : [min_extreme, zone_min] -> [1, 0]
    if T < zone_min:
        if T <= min_extreme:
            return 1.0
        return (zone_min - T) / (zone_min - min_extreme)

    # Chaleur : [zone_max, max_extreme] -> [0, 1]
    if T >= max_extreme:
        return 1.0
    return (T - zone_max) / (max_extreme - zone_max)


def _score_humidite(H: float) -> float:
    """
    Retourne un score de stress lié à l'humidité entre 0 et 1.

    Zone de confort : 40–70 % -> score 0.
    Extrêmes : <= 20 % ou >= 90 % -> score 1.
    Transition linéaire entre ces bornes.
    """
    zone_min = 40.0
    zone_max = 70.0
    min_extreme = 20.0   # air très sec
    max_extreme = 90.0   # air très humide

    # Zone neutre
    if zone_min <= H <= zone_max:
        return 0.0

    # Trop sec : [min_extreme, zone_min] -> [1, 0]
    if H < zone_min:
        if H <= min_extreme:
            return 1.0
        return (zone_min - H) / (zone_min - min_extreme)

    # Trop humide : [zone_max, max_extreme] -> [0, 1]
    if H >= max_extreme:
        return 1.0
    return (H - zone_max) / (max_extreme - zone_max)