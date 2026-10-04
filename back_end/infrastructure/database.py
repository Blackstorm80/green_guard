from sqlalchemy import MetaData, create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

from config import settings
from infrastructure.rls import poser_contexte_transaction

DATABASE_URL = settings.database_url

# PostgreSQL : pas besoin de connect_args check_same_thread
connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

_options_pool = {} if DATABASE_URL.startswith("sqlite") else {
    "pool_size": settings.db_pool_size,
    "max_overflow": settings.db_max_overflow,
    "pool_timeout": settings.db_pool_timeout_s,  # échec rapide plutôt qu'une file d'attente de 30 s
}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True, **_options_pool)

if DATABASE_URL.startswith("sqlite"):
    # SQLite n'applique ON DELETE CASCADE qu'avec ce pragma (comportement aligné sur PostgreSQL)
    @event.listens_for(engine, "connect")
    def _activer_cles_etrangeres(dbapi_connection, _):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# Contexte d'organisation (RLS PostgreSQL) reposé au début de chaque transaction
event.listen(SessionLocal, "after_begin", poser_contexte_transaction)

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
