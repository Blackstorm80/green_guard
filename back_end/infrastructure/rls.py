"""Contexte d'organisation des transactions PostgreSQL pour la Row Level Security (défense en profondeur).

Les politiques RLS (migration 0002) n'exposent que les lignes dont l'organisation vaut le paramètre
`app.organisation_id`, sauf si `app.contourner_rls` vaut `on`. Ces paramètres sont posés en local
à la transaction (équivalent de SET LOCAL) : ils disparaissent au commit. Ils sont donc reposés au
début de CHAQUE transaction (événement after_begin) à partir de `session.info`.

Pourquoi `session.info` et non une ContextVar : FastAPI exécute chaque dépendance synchrone et la
route dans des appels distincts au pool de threads, chacun sur une COPIE du contexte ; une ContextVar
renseignée par la dépendance d'authentification serait invisible de la route. La session, elle, est
partagée par toute la requête.

Sous SQLite, rien n'est exécuté : le filtrage applicatif par organisation reste la première barrière.
"""
import logging
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import text
from sqlalchemy.engine import Connection, Engine
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

CLE_ORGANISATION = "organisation_id"
CLE_CONTOURNEMENT = "contourner_rls"

_POSER_CONTEXTE = text(
    "SELECT set_config('app.organisation_id', :organisation, true), "
    "set_config('app.contourner_rls', :contourner, true)"
)


def _appliquer(connexion: Connection, info: dict) -> None:
    if connexion.dialect.name != "postgresql":
        return
    organisation_id = info.get(CLE_ORGANISATION)
    # Les deux paramètres sont toujours réécrits : aucune valeur ne survit d'une transaction à l'autre
    connexion.execute(_POSER_CONTEXTE, {
        "organisation": "" if organisation_id is None else str(int(organisation_id)),
        "contourner": "on" if info.get(CLE_CONTOURNEMENT) else "off",
    })


def poser_contexte_transaction(session: Session, _transaction, connexion: Connection) -> None:
    """Écouteur after_begin enregistré sur la fabrique de sessions (infrastructure/database.py)."""
    _appliquer(connexion, session.info)


def _reappliquer(session: Session) -> None:
    """Met à jour la transaction en cours ; les suivantes le seront par after_begin."""
    transaction = session.get_transaction()
    if transaction is not None and transaction.is_active:
        _appliquer(session.connection(), session.info)


def definir_organisation(session: Session, organisation_id: int | None) -> None:
    session.info[CLE_ORGANISATION] = organisation_id
    _reappliquer(session)


@contextmanager
def contournement_rls(session: Session) -> Iterator[Session]:
    """Lève la RLS le temps d'un bloc, pour les seules opérations qui précèdent ou dépassent une
    organisation : lecture du compte à l'authentification, inscription, création d'organisation,
    worker et scripts d'administration."""
    precedent = session.info.get(CLE_CONTOURNEMENT, False)
    session.info[CLE_CONTOURNEMENT] = True
    _reappliquer(session)
    try:
        yield session
    finally:
        session.info[CLE_CONTOURNEMENT] = precedent
        _reappliquer(session)


def rls_effective(engine: Engine) -> bool | None:
    """False si le rôle de connexion ignore la RLS (superutilisateur ou BYPASSRLS) ; None hors PostgreSQL."""
    if engine.dialect.name != "postgresql":
        return None
    with engine.connect() as connexion:
        ignore = connexion.execute(text(
            "SELECT rolsuper OR rolbypassrls FROM pg_roles WHERE rolname = current_user"
        )).scalar()
    return not ignore


def avertir_si_rls_inoperante(engine: Engine) -> None:
    try:
        effective = rls_effective(engine)
    except Exception:
        logger.warning("Impossible de vérifier le rôle de connexion PostgreSQL (RLS).", exc_info=True)
        return
    if effective is False:
        logger.warning(
            "Rôle PostgreSQL superutilisateur ou BYPASSRLS : l'isolation des organisations par la base (RLS) "
            "est inopérante, seul le filtrage applicatif s'applique. Connecter l'API avec un rôle dédié "
            "(voir documentation/exploitation.md)."
        )
