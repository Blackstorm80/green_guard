# back_end/scripts/fix_passwords.py

import sys
import os
from sqlalchemy.orm import Session

# Add the project root to the python path to allow relative imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from infrastructure.database import SessionLocal
from domain.models import User
from api.deps.auth import get_password_hash

def migrate_passwords():
    """
    Scans the User table and hashes any plain-text or missing passwords.
    """
    db: Session = SessionLocal()
    print(">> Démarrage du script de migration des mots de passe...")
    
    updated_count = 0
    skipped_count = 0
    
    try:
        users = db.query(User).all()
        
        if not users:
            print("Aucun utilisateur trouvé dans la base de données.")
            return

        for user in users:
            # La signature d'un hash bcrypt est de commencer par '$2b$'
            is_hashed = user.hashed_password and user.hashed_password.startswith("$2b$")

            if is_hashed:
                print(f"OK: Mot de passe pour '{user.email}' est déjà haché. Ignoré.")
                skipped_count += 1
                continue

            # Si le mot de passe n'est pas haché, il est soit en clair, soit manquant.
            # Nous le remplaçons par un mot de passe par défaut sécurisé.
            plain_password = user.hashed_password if user.hashed_password else "defaultpassword"
            
            print(f"ATTENTION: Mot de passe pour '{user.email}' non haché. Mise à jour...")
            
            # Hachage du mot de passe (soit la valeur existante, soit un défaut)
            hashed = get_password_hash(plain_password)
            user.hashed_password = hashed
            
            db.add(user)
            updated_count += 1

        if updated_count > 0:
            db.commit()
            print(f"\nSUCCES: {updated_count} mot(s) de passe ont été mis à jour avec succès.")
        else:
            print("\nINFO: Tous les mots de passe étaient déjà conformes.")

        if skipped_count > 0:
            print(f"INFO: {skipped_count} utilisateur(s) étaient déjà à jour.")

    except Exception as e:
        print(f"ERREUR: Erreur critique lors de la migration : {e}")
        db.rollback()
    finally:
        db.close()
        print(">> Script de migration terminé.")

if __name__ == "__main__":
    migrate_passwords()
