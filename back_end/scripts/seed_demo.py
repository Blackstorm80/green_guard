# back_end/scripts/seed_demo.py

import sys
import os
from sqlalchemy.orm import Session

# Add the project root to the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.database import SessionLocal, engine, Base
from domain.models import User, EspaceVert, ZoneIntelligente, Capteur, TypeCapteur, EspeceVegetale

def clear_data(db: Session):
    """Vide toutes les données des tables."""
    print("Nettoyage de la base de données...")
    # On supprime dans l'ordre inverse des dépendances
    db.query(Capteur).delete()
    db.query(EspaceVert).delete()
    db.query(ZoneIntelligente).delete()
    db.query(User).delete()
    db.query(EspeceVegetale).delete()
    db.commit()

def seed_data(db: Session):
    """Injecte les données de démo."""
    print("Injection des données de démo...")

    # --- 1. Utilisateur ---
    user = User(name="Demo User", email="demo@greenguard.com", role="admin")
    db.add(user)
    db.commit()
    db.refresh(user)
    print(f"Utilisateur créé: {user.name}")

    # --- 2. Espèces Végétales (Catalogue) ---
    espece1 = EspeceVegetale(
        nom_commun="Chêne", nom_scientifique="Quercus robur",
        humidite_sol_min=30, humidite_sol_max=70, coeff_cultural=0.9
    )
    espece2 = EspeceVegetale(
        nom_commun="Rosier", nom_scientifique="Rosa",
        humidite_sol_min=40, humidite_sol_max=80, coeff_cultural=1.2
    )
    db.add_all([espece1, espece2])
    db.commit()

    # --- 3. Zones ---
    zone1 = ZoneIntelligente(nom="Lyon-Est", user_id=user.id, centroid_lat=45.75, centroid_lon=4.85)
    zone2 = ZoneIntelligente(nom="Paris-Nord", user_id=user.id, centroid_lat=48.86, centroid_lon=2.35)
    db.add_all([zone1, zone2])
    db.commit()
    print("Zones créées.")

    # --- 4. Espaces Verts ---
    ev1 = EspaceVert(
        nom="Parc de la Tête d'Or", ville="Lyon", user_id=user.id, sante_percent=95,
        latitude=45.77, longitude=4.85, especes_vegetales=[espece1]
    )
    ev2 = EspaceVert(
        nom="Jardin des Tuileries", ville="Paris", user_id=user.id, sante_percent=80,
        latitude=48.86, longitude=2.32, especes_vegetales=[espece2]
    )
    ev3 = EspaceVert(
        nom="Parc de la Villette", ville="Paris", user_id=user.id, sante_percent=50, # Santé moyenne
        latitude=48.89, longitude=2.38, especes_vegetales=[espece1, espece2]
    )
    ev4 = EspaceVert(
        nom="Square de la Roquette", ville="Paris", user_id=user.id, sante_percent=30, # Stress hydrique
        latitude=48.85, longitude=2.38, especes_vegetales=[espece2]
    )
    ev5 = EspaceVert(
        nom="Forêt de Fausses-Reposes", ville="Versailles", user_id=user.id, sante_percent=20, # CO2 élevé
        latitude=48.80, longitude=2.13, especes_vegetales=[espece1]
    )
    db.add_all([ev1, ev2, ev3, ev4, ev5])
    db.commit()
    print("Espaces verts créés.")

    # --- 5. Capteurs et Mesures ---
    # Espace 4 (Stress Hydrique)
    capteur_sol_ev4 = Capteur(nom="Capteur Sol EV4", type=TypeCapteur.HUMIDITE_SOL, espace_id=ev4.id)
    db.add(capteur_sol_ev4)
    # Espace 5 (CO2 élevé)
    capteur_co2_ev5 = Capteur(nom="Capteur CO2 EV5", type=TypeCapteur.CO2, espace_id=ev5.id)
    db.add(capteur_co2_ev5)
    db.commit()
    print("Capteurs créés.")

    print("Données de démo injectées avec succès !")

if __name__ == "__main__":
    # Recréer les tables pour être sûr
    print("Recréation des tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # On ne vide pas car on drop/create
        # clear_data(db) 
        seed_data(db)
    finally:
        db.close()
