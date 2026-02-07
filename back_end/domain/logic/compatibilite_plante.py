# Fichier: domain/logic/compatibilite_plante.py

def est_exposition_compatible(
    exposition_plante: str,
    exposition_espace: str,
) -> bool:
    """
    Vérifie si l'exposition réelle d'un espace est compatible
    avec les besoins en lumière d'une plante.

    Règles simples :
    - Une plante "Soleil" tolère "Soleil" ou "Mi-ombre".
    - Une plante "Mi-ombre" est la plus flexible.
    - Une plante "Ombre" ne tolère que "Ombre" ou "Mi-ombre".
    """
    if exposition_plante == "Soleil" and exposition_espace == "Ombre":
        return False
    if exposition_plante == "Ombre" and exposition_espace == "Soleil":
        return False
    return True