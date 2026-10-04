"""Règles pures des organisations (collectivités) : identifiant lisible et nom par défaut."""
import re
import unicodedata
from collections.abc import Callable

LONGUEUR_MAX_SLUG = 60
SLUG_PAR_DEFAUT = "organisation"


def generer_slug(nom: str) -> str:
    """« Ville de Saint-Étienne » → « ville-de-saint-etienne »."""
    ascii_ = unicodedata.normalize("NFKD", nom).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")
    return slug[:LONGUEUR_MAX_SLUG].rstrip("-") or SLUG_PAR_DEFAUT


def slug_disponible(base: str, existe: Callable[[str], bool]) -> str:
    """Premier slug libre parmi base, base-2, base-3…"""
    if not existe(base):
        return base
    suffixe = 2
    while True:
        candidat = f"{base[:LONGUEUR_MAX_SLUG - len(str(suffixe)) - 1]}-{suffixe}"
        if not existe(candidat):
            return candidat
        suffixe += 1


def nom_organisation_par_defaut(nom_utilisateur: str) -> str:
    return f"Organisation de {nom_utilisateur.strip()}"
