from sqlalchemy.orm import Session

from api.deps.auth import get_password_hash
from domain.models import User
from infrastructure.database import SessionLocal


def create_user(email: str, password: str, name: str = "Admin"):
    """Crée un utilisateur admin avec un mot de passe haché."""
    db: Session = SessionLocal()
    try:
        # Vérifier si l'email existe déjà
        existing = db.query(User).filter(User.email == email).first()
        if existing:
            print(f"L'utilisateur avec l'email {email} existe déjà.")
            return

        hashed_password = get_password_hash(password)
        user = User(
            name=name,
            email=email,
            hashed_password=hashed_password,
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Utilisateur créé avec succès : id={user.id}, email={user.email}")
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Crée un utilisateur admin en base.")
    parser.add_argument("--email", required=True, help="Email de l'administrateur")
    parser.add_argument("--password", required=True, help="Mot de passe de l'administrateur")
    parser.add_argument("--name", default="Admin", help="Nom affiché")
    args = parser.parse_args()
    create_user(email=args.email, password=args.password, name=args.name)
