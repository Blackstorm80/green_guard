import os
from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "Variable d'environnement DATABASE_URL manquante. "
        "Exemple: postgresql://greenguard:secret@localhost:5432/greenguard"
    )

# PostgreSQL : pas besoin de connect_args check_same_thread
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

if DATABASE_URL.startswith("sqlite"):
    # SQLite n'applique ON DELETE CASCADE qu'avec ce pragma (comportement aligné sur PostgreSQL)
    @event.listens_for(engine, "connect")
    def _activer_cles_etrangeres(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Contraintes nommées de façon déterministe : indispensable pour que les migrations
# Alembic puissent les modifier ou les supprimer de la même manière sur PostgreSQL et SQLite.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}

Base = declarative_base(metadata=MetaData(naming_convention=NAMING_CONVENTION))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
