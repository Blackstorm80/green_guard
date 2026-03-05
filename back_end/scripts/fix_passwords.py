# back_end/scripts/fix_passwords.py
import sys
import os
from sqlalchemy.orm import Session

# Ajout du chemin du projet pour permettre les imports relatifs
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from infrastructure.database import SessionLocal
from domain.models import User
from api.deps.auth import get_password_hash, verify_password

def migrate_passwords():
    """
    Script pour trouver et hacher les mots de passe en texte clair dans la base de données.
    """
    db = SessionLocal()
    print("🔍 Démarrage de l'audit des mots de passe...")
    
    try:
        users_to_update = []
        all_users = db.query(User).all()

        for user in all_users:
            password_is_plaintext = False
            
            # Heuristique simple: les hashs Bcrypt sont longs et commencent par $2b$
            # On vérifie si le mot de passe est un hash valide en essayant de le vérifier contre une chaîne improbable
            # Si verify lève une erreur (ou retourne False), c'est probablement du texte clair
            try:
                # Si le mot de passe est un hash valide, la ligne ci-dessous ne lèvera pas d'erreur
                # et retournera False. Si c'est du texte clair, passlib lèvera une erreur.
                if not user.hashed_password.startswith("$2b$"):
                   password_is_plaintext = True
            except Exception:
                password_is_plaintext = True
            
            if password_is_plaintext:
                print(f"  - [!] Mot de passe en clair trouvé pour l'utilisateur: {user.email}")
                # On suppose que la valeur actuelle est le mot de passe en clair
                plaintext_password = user.hashed_password
                user.hashed_password = get_password_hash(plaintext_password)
                users_to_update.append(user)

        if not users_to_update:
            print("✅ Aucun mot de passe en clair trouvé. La base de données est sécurisée.")
            return

        print(f"
🔄 Hachage et mise à jour de {len(users_to_update)} mot(s) de passe...")
        db.commit()
        print("✅ Migration des mots de passe terminée avec succès.")

    except Exception as e:
        print(f"❌ Erreur lors de la migration des mots de passe : {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    migrate_passwords()
