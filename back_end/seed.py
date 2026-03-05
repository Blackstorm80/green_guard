import random
import sys
import os
from sqlalchemy.orm import Session

# Ajout du chemin du projet pour permettre les imports relatifs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.database import engine, Base, SessionLocal
from domain.models import User, EspaceVert
from api.deps.auth import get_password_hash # Import de la fonction de hachage

# Les 5 types d'espaces requis (utilisés dans le nom puisqu'il n'y a pas de colonne type_espace)
TYPES_ESPACE = [
    "Parc public", 
    "Jardin partagé", 
    "Forêt urbaine", 
    "Toiture végétale", 
    "Terrain de sport"
]

VILLES = ["Saint-Priest", "Lyon", "Paris", "Marseille", "Bordeaux", "Lille"]

def seed_database():
    print("🧹 Nettoyage de la base de données...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        print("👤 Création des utilisateurs avec mots de passe hachés...")
        users = []

        # 1. Création de l'Admin (ID = 1 obligatoire)
        admin = User(
            id=1,
            email="admin@greenguard.com",
            hashed_password=get_password_hash("password"),
            name="Administrateur",
            role="admin"
        )
        users.append(admin)

        # 2. Création de 9 utilisateurs normaux
        for i in range(2, 11):
            user = User(
                id=i,
                email=f"user{i}@greenguard.fr",
                hashed_password=get_password_hash(f"password"),
                name=f"Utilisateur {i}",
                role="user"
            )
            users.append(user)

        # Sauvegarde des utilisateurs
        db.add_all(users)
        db.commit()

        print("🌳 Création des espaces verts...")
        espaces = []
        
        # 3. Création de 5 espaces par utilisateur
        for u in users:
            for type_esp in TYPES_ESPACE:
                espace = EspaceVert(
                    # Le type est injecté directement dans le nom de l'espace
                    nom=f"{type_esp} de {u.name}",
                    ville=random.choice(VILLES),
                    surface_m2=round(random.uniform(50.0, 5000.0), 2),
                    latitude=round(random.uniform(43.0, 49.0), 5),
                    longitude=round(random.uniform(-1.0, 5.0), 5),
                    sante_percent=round(random.uniform(60.0, 100.0), 1),
                    user_id=u.id
                )
                espaces.append(espace)

        # Sauvegarde des espaces
        db.add_all(espaces)
        db.commit()

        print("\n✅ Seeding terminé avec succès !")
        print(f"-> {len(users)} utilisateurs créés (dont Admin ID=1).")
        print(f"-> {len(espaces)} espaces verts créés (5 par utilisateur).")

    except Exception as e:
        print(f"❌ Erreur lors du seeding : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()