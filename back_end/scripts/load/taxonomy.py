import os
import sys
import pandas as pd
import random
#script pour extraire et charger le catalogue
# 1. CONFIGURATION DES CHEMINS
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from infrastructure.database import SessionLocal, engine
from domain.models import Plante, Auxiliaire, Base

def get_physio_data_enhanced(name):
    """
    Génère des données physiologiques (pH, besoins en eau) plus réalistes
    basées sur des mots-clés dans le nom de l'espèce.
    """
    name_low = str(name).lower()
    
    # Defaults
    ph_base, eau_base = 6.8, "Modéré" # (e.g., 300-500 mm/an)

    # Familles/Genres spécifiques
    if any(k in name_low for k in ["rosa", "prunus", "malus", "fragaria"]): # Rosaceae
        ph_base, eau_base = 6.5, "Modéré"
    elif any(k in name_low for k in ["cactus", "cactaceae", "succulent", "yucca", "agave"]):
        ph_base, eau_base = 7.2, "Faible" # (e.g., < 200 mm/an)
    elif any(k in name_low for k in ["pinus", "picea", "abies", "juniperus"]): # Conifères
        ph_base, eau_base = 5.8, "Faible à Modéré"
    elif any(k in name_low for k in ["quercus", "robur", "ilex"]): # Chênes
        ph_base, eau_base = 6.0, "Faible à Modéré"
    elif any(k in name_low for k in ["acer", "maple"]): # Érables
        ph_base, eau_base = 6.5, "Modéré"
    elif any(k in name_low for k in ["solanum", "tomato", "potato"]): # Solanaceae
        ph_base, eau_base = 6.2, "Élevé" # (e.g., > 600 mm/an)
    elif any(k in name_low for k in ["lavandula", "thymus", "rosmarinus"]): # Lamiaceae/Méditerranéen
        ph_base, eau_base = 7.0, "Très Faible"
    elif any(k in name_low for k in ["fern", "fougère", "polypodium"]):
        ph_base, eau_base = 5.5, "Élevé"
    elif any(k in name_low for k in ["lily", "lilium", "tulipa"]):
        ph_base, eau_base = 6.5, "Modéré à Élevé"
    
    ph_final = round(ph_base * random.uniform(0.97, 1.03), 1)
    return {"ph": ph_final, "eau": eau_base}

def is_beneficial_insect(name):
    beneficial_keywords = ["bee", "bumble", "lady beetle", "mantis", "wasp", "butterfly", "lacewing", "hover fly"]
    return any(k in str(name).lower() for k in beneficial_keywords)

def load_taxonomy():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    csv_path = os.path.abspath(os.path.join(project_root, "..", "inaturalist", "inaturalist_train (1).csv"))

    if not os.path.exists(csv_path):
        print(f"ERREUR : Fichier introuvable à l'adresse : {csv_path}")
        return

    try:
        print(f"Lecture du fichier : {csv_path}")
        df = pd.read_csv(csv_path)
        # Assurer que la colonne 'taxon' est de type string pour le filtrage
        df['taxon'] = df['taxon'].astype(str).str.strip()
        
        # --- PLANTES ---
        plantes_df = df[df["taxon"].str.contains("Plantae", case=False, na=False)]
        print(f"Traitement de {len(plantes_df)} plantes...")
        for _, row in plantes_df.iterrows():
            physio = get_physio_data_enhanced(row["species_guess"])
            
            # Gestion de l'URL de l'image
            img_url = ""
            if pd.notna(row["photos"]) and "http" in str(row["photos"]):
                img_raw = str(row["photos"])
                img_url = img_raw.replace("square", "medium")
            else:
                # Créer une URL de recherche si l'image est manquante
                search_query = str(row["species_guess"]).replace(" ", "+")
                img_url = f"https://www.google.com/search?q={search_query}+botany&tbm=isch"

            nom_commun_final = str(row["common_name"]) if pd.notna(row["common_name"]) and str(row["common_name"]).lower() != "nan" else str(row["species_guess"])

            db.add(Plante(
                nom_scientifique=str(row["species_guess"]),
                nom_commun=nom_commun_final,
                ph_ideal=physio["ph"],
                besoin_eau=physio["eau"],
                url_image=img_url,
                famille="Plantae" # Pourrait être affiné si l'info est dans le CSV
            ))
        
        # --- INSECTES ---
        insectes_df = df[df["taxon"].str.contains("Insecta", case=False, na=False)]
        count_ins = 0
        print(f"Traitement de {len(insectes_df)} insectes pour trouver les auxiliaires...")
        for _, row in insectes_df.iterrows():
            if is_beneficial_insect(row["species_guess"]):
                img_raw = str(row["photos"])
                img_clean = img_raw.replace("square", "medium")
                
                db.add(Auxiliaire(
                    nom=str(row["species_guess"]),
                    role="Pollinisateur/Predateur",
                    description="Favorise l'equilibre de l'ecosysteme.",
                    url_image=img_clean
                ))
                count_ins += 1
        
        db.commit()
        print(f"Importation terminée : {len(plantes_df)} plantes et {count_ins} insectes auxiliaires ajoutés.")

    except Exception as e:
        print(f"ERREUR CRITIQUE : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    load_taxonomy()