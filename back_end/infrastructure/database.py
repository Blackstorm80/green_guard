# back_end/infrastructure/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from domain.models import Base # IMPORTANT: Importer la Base du domaine

# URL de la base de données.
# Utilisation de SQLite pour la simplicité du développement.
SQLALCHEMY_DATABASE_URL = "sqlite:///./green_guard.db"

# Création du moteur de base de données.
# `connect_args` est spécifique à SQLite pour autoriser les connexions multithread.
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# Création de la 'fabrique' de sessions. C'est elle qui créera les sessions
# pour chaque requête.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """
    Initialise la base de données en créant toutes les tables
    définies dans les modèles du domaine.
    """
    # Base.metadata.create_all() est la commande magique qui prend tous les
    # héritiers de Base et les crée dans la DB connectée au moteur.
    Base.metadata.create_all(bind=engine)

def get_db():
    """
    Injecteur de dépendances pour les routes FastAPI.
    Fournit une session de base de données à une route et s'assure
    qu'elle est correctement fermée après la requête.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
