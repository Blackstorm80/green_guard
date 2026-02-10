# back_end/infrastructure/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# URL de la base de données.
# Pour l'instant, on utilise SQLite pour la simplicité du développement.
# Le fichier sera créé à la racine du conteneur ou du projet.
SQLALCHEMY_DATABASE_URL = "sqlite:///./green_guard.db"
# Pour PostgreSQL plus tard : "postgresql://user:password@db/green_guard"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db_session():
    """Dépendance FastAPI pour obtenir une session DB."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()