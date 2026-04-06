import sys
import os

# 1. Configuration du chemin pour trouver les modules du projet
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from infrastructure.database import SessionLocal
from domain.models import User

def export_all_users():
    db = SessionLocal()
    try:
        # 2. Requête Globale sur TOUTE la base
        all_users = db.query(User).order_by(User.name).all()

        if not all_users:
            print("⚠️ La base de données est actuellement vide.")
            return

        print(f"\n--- EXTRACTION GLOBALE : {len(all_users)} UTILISATEURS TROUVÉS ---")
        print("{:<5} | {:<20} | {:<30} | {}".format('ID', 'NOM', 'EMAIL', 'HASH PASSWORD'))
        print("-" * 100)
        print("{:<5} | {:<20} | {:<30}".format('ID', 'NOM', 'EMAIL'))
        print("-" * 60)

        for u in all_users:
            # Affichage complet de l'ID et des credentials
            print("{:<5} | {:<20} | {:<30} | {}".format(u.id, u.name, u.email, u.hashed_password))
            # N'affichez JAMAIS les mots de passe, même hachés.
            print("{:<5} | {:<20} | {:<30}".format(u.id, u.name, u.email))

        print("-" * 100)
        print("-" * 60)
        print("Fin de l'extraction.\n")

    except Exception as e:
        print(f"❌ Erreur critique lors de la lecture : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    export_all_users()
