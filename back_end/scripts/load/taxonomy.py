"""Chargement du catalogue botanique (plantes et insectes auxiliaires) depuis les exports iNaturalist.

Usage (depuis back_end/, DATABASE_URL pointant vers la base cible, schéma déjà migré) :
    python -m scripts.load.taxonomy [--dry-run]

- Une ligne du CSV est une *observation* : le catalogue est dédoublonné par espèce.
- Idempotent : une espèce déjà présente (même nom scientifique) n'est pas réinsérée.
- Aucune valeur inventée : pH et besoin en eau ne sont renseignés que lorsqu'une règle
  par famille botanique s'applique (estimation indicative, à faire valider) ; l'image
  est la photo iNaturalist de l'observation, sinon aucune.
"""
import argparse
import os
import sys

import pandas as pd

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from domain.models import Auxiliaire, Plante  # noqa: E402
from infrastructure.database import SessionLocal  # noqa: E402

DOSSIER_DONNEES = os.path.join(BACKEND, "..", "inaturalist")
FICHIERS = ["inaturalist_train (1).csv", "inaturalist_test (1).csv"]

# (mots-clés dans le nom, pH indicatif, besoin en eau) — première règle applicable retenue
REGLES_PHYSIOLOGIE = [
    (("rosa", "prunus", "malus", "fragaria"), 6.5, "Modéré"),
    (("cactus", "cactaceae", "succulent", "yucca", "agave"), 7.2, "Faible"),
    (("pinus", "picea", "abies", "juniperus"), 5.8, "Faible à modéré"),
    (("quercus", "ilex"), 6.0, "Faible à modéré"),
    (("acer", "maple"), 6.5, "Modéré"),
    (("solanum", "tomato", "potato"), 6.2, "Élevé"),
    (("lavandula", "thymus", "rosmarinus"), 7.0, "Très faible"),
    (("fern", "fougère", "polypodium"), 5.5, "Élevé"),
    (("lily", "lilium", "tulipa"), 6.5, "Modéré à élevé"),
]

ROLES_AUXILIAIRES = [
    (("bee", "bumble", "butterfly", "hover fly"), "Pollinisateur",
     "Assure la pollinisation des espèces à fleurs."),
    (("lady beetle", "ladybug", "lacewing", "mantis", "wasp"), "Prédateur",
     "Régule naturellement les ravageurs (pucerons, chenilles…)."),
]


def _texte(valeur) -> str | None:
    if pd.isna(valeur):
        return None
    texte = str(valeur).strip()
    return None if texte.lower() in ("", "none", "nan") else texte


def physiologie(nom: str) -> tuple[float | None, str | None]:
    nom = nom.lower()
    for mots, ph, eau in REGLES_PHYSIOLOGIE:
        if any(m in nom for m in mots):
            return ph, eau
    return None, None


def role_auxiliaire(nom: str) -> tuple[str, str] | None:
    nom = nom.lower()
    for mots, role, description in ROLES_AUXILIAIRES:
        if any(m in nom for m in mots):
            return role, description
    return None


def photo(valeur) -> str | None:
    url = _texte(valeur)
    if not url or not url.startswith("https://"):
        return None
    return url.replace("/square.", "/medium.")


def lire_observations() -> pd.DataFrame:
    chemins = [os.path.join(DOSSIER_DONNEES, f) for f in FICHIERS]
    manquants = [c for c in chemins if not os.path.exists(c)]
    if manquants:
        raise FileNotFoundError(f"Fichiers introuvables : {manquants}")
    df = pd.concat([pd.read_csv(c, usecols=["species_guess", "common_name", "taxon", "photos"]) for c in chemins])
    df["species_guess"] = df["species_guess"].map(_texte)
    df["taxon"] = df["taxon"].astype(str).str.strip()
    df = df.dropna(subset=["species_guess"])
    # Une espèce = une entrée ; on garde de préférence une observation avec photo
    df["a_photo"] = df["photos"].map(photo).notna()
    df["cle"] = df["species_guess"].str.lower()
    return df.sort_values("a_photo", ascending=False).drop_duplicates("cle")


def charger(dry_run: bool = False) -> None:
    df = lire_observations()
    db = SessionLocal()
    try:
        plantes_existantes = {n.lower() for (n,) in db.query(Plante.nom_scientifique) if n}
        auxiliaires_existants = {n.lower() for (n,) in db.query(Auxiliaire.nom) if n}

        nouvelles_plantes = []
        for row in df[df["taxon"] == "Plantae"].itertuples():
            if row.cle in plantes_existantes:
                continue
            ph, eau = physiologie(row.species_guess)
            nouvelles_plantes.append(Plante(
                nom_scientifique=row.species_guess,
                nom_commun=_texte(row.common_name) or row.species_guess,
                famille="Plantae",
                ph_ideal=ph,
                besoin_eau=eau,
                url_image=photo(row.photos),
            ))

        nouveaux_auxiliaires = []
        for row in df[df["taxon"] == "Insecta"].itertuples():
            role = role_auxiliaire(row.species_guess)
            if role is None or row.cle in auxiliaires_existants:
                continue
            nouveaux_auxiliaires.append(Auxiliaire(
                nom=row.species_guess, role=role[0], description=role[1], url_image=photo(row.photos),
            ))

        renseignes = sum(1 for p in nouvelles_plantes if p.ph_ideal is not None)
        print(f"Plantes à ajouter : {len(nouvelles_plantes)} (pH/eau estimés pour {renseignes}) ; "
              f"auxiliaires à ajouter : {len(nouveaux_auxiliaires)}.")
        if dry_run:
            print("Simulation (--dry-run) : aucune écriture.")
            return
        db.add_all(nouvelles_plantes + nouveaux_auxiliaires)
        db.commit()
        print("Catalogue chargé.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Charge le catalogue botanique depuis les CSV iNaturalist.")
    parser.add_argument("--dry-run", action="store_true", help="Compter sans écrire en base")
    charger(dry_run=parser.parse_args().dry_run)
