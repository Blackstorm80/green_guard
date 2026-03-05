from sqlalchemy.orm import Session

from infrastructure.database import SessionLocal
from domain.models import User
from api.deps.auth import get_password_hash

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
    print("Création de l'utilisateur de démo...")
    create_user(email="admin@demo.com", password="admin123", name="Admin Demo")