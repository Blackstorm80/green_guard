import os
import sys

# Ajustement du chemin pour l'architecture en Oignon
# On remonte d'un niveau pour que Python trouve 'infrastructure', 'domain', etc.
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root not in sys.path:
    sys.path.insert(0, root)

from infrastructure.database import SessionLocal
from domain import models
from api.deps.auth import get_password_hash

def setup_data():
    db = SessionLocal()
    try:
        print("--- DÉMARRAGE DE L'INJECTION DES DONNÉES DE DÉVELOPPEMENT ---")

        # 1. Création de l'utilisateur Nathan (s'il est inexistant)
        user = db.query(models.User).filter(models.User.email == "nathan@greentech.fr").first()
        if not user:
            user = models.User(
                name="Nathan Green",
                email="nathan@greentech.fr",
                hashed_password=get_password_hash("password123"),
                avatar_url="https://api.dicebear.com/7.x/avataaars/svg?seed=Nathan",
                role="admin"
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            print(f"Succès : Utilisateur {user.name} créé (ID: {user.id})")
        else:
            print(f"Info : L'utilisateur {user.name} existe déjà.")

        # 2. Création de la config de clustering pour Nathan (si inexistante)
        config = db.query(models.ClusteringConfig).filter(models.ClusteringConfig.id == user.id).first()
        if not config:
            config = models.ClusteringConfig(id=user.id)
            db.add(config)
            db.commit()
            print("Succès : Configuration de clustering par défaut créée pour Nathan.")
        else:
            print("Info : La configuration de clustering pour Nathan existe déjà.")

        # 3. Nettoyage des anciens espaces pour Nathan pour un test propre
        # On supprime d'abord les capteurs rattachés aux espaces de l'utilisateur pour éviter une IntegrityError
        espaces_existants = db.query(models.EspaceVert.id).filter(models.EspaceVert.user_id == user.id).all()
        espace_ids = [e.id for e in espaces_existants]
        if espace_ids:
            db.query(models.Capteur).filter(models.Capteur.espace_id.in_(espace_ids)).delete(synchronize_session=False)
        db.query(models.EspaceVert).filter(models.EspaceVert.user_id == user.id).delete()
        
        # 4. Injection des Espaces Verts pour Nathan
        espace1 = models.EspaceVert(
            nom="Parc de Test (Clustering)",
            # type_espace="parc",  # À décommenter quand la colonne existera dans models.py
            ville="Lyon",
            latitude=45.7700,
            longitude=4.8500,
            surface_m2=117000.0,
            user_id=user.id
        )
        
        espace2 = models.EspaceVert(
            nom="Jardin des Capteurs",
            # type_espace="jardin",  # À décommenter quand la colonne existera dans models.py
            ville="Lyon",
            latitude=45.7550,
            longitude=4.8200,
            surface_m2=6500.0,
            user_id=user.id
        )

        db.add_all([espace1, espace2])
        db.commit()
        db.refresh(espace1)
        db.refresh(espace2)
        print(f"Succès : 2 espaces verts créés pour {user.name}.")

        # 5. Injection de Capteurs pour les tests
        capteurs = [
            models.Capteur(
                nom="Sonde Humidité Jardin",
                type="HUMIDITE_SOL",
                emplacement="Zone B1",
                espace_id=espace2.id,
                est_actif=True
            ),
            models.Capteur(
                nom="Station Météo Parc",
                type="TEMPERATURE",
                emplacement="Centre du parc",
                espace_id=espace1.id,
                est_actif=True
            )
        ]
        
        db.add_all(capteurs)
        db.commit()
        
        print(f"Succès : {len(capteurs)} capteurs injectés.")

        print("--- INJECTION TERMINÉE AVEC SUCCÈS ---")

    except Exception as e:
        print(f"ERREUR CRITIQUE : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    setup_data()