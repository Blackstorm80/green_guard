"""Crée un compte en base (administration de l'instance).

Exemple : python create_user.py --email admin@ville.fr --password "…" --organisation ville-de-lyon --role admin
"""
from sqlalchemy.orm import Session

from api.deps.auth import get_password_hash
from domain.logic.droits import ADMIN, ROLES
from domain.models import Organisation, User
from infrastructure.database import SessionLocal
from infrastructure.rls import contournement_rls

SLUG_PAR_DEFAUT = "defaut"
NOM_PAR_DEFAUT = "Organisation par défaut"


def create_user(email: str, password: str, name: str = "Admin", organisation: str = SLUG_PAR_DEFAUT,
                role: str = ADMIN, superadmin: bool = False, nom_organisation: str | None = None,
                db: Session | None = None) -> User | None:
    """Crée l'utilisateur dans l'organisation désignée par son slug (créée si absente)."""
    if role not in ROLES:
        raise ValueError(f"Rôle inconnu : {role} (valeurs possibles : {', '.join(ROLES)})")
    session = db or SessionLocal()
    try:
        # Script d'administration : opère hors de toute organisation, contournement explicite de la RLS
        with contournement_rls(session):
            if session.query(User).filter(User.email == email).first():
                print(f"L'utilisateur avec l'email {email} existe déjà.")
                return None
            orga = session.query(Organisation).filter(Organisation.slug == organisation).first()
            if orga is None:
                nom = nom_organisation or (NOM_PAR_DEFAUT if organisation == SLUG_PAR_DEFAUT else organisation)
                orga = Organisation(nom=nom, slug=organisation)
                session.add(orga)
                session.flush()
                print(f"Organisation créée : {orga.nom} ({orga.slug})")
            user = User(name=name, email=email, hashed_password=get_password_hash(password),
                        organisation_id=orga.id, role=role, est_superadmin=superadmin)
            session.add(user)
            session.commit()
            print(f"Utilisateur créé avec succès : id={user.id}, email={user.email}, "
                  f"organisation={orga.slug}, rôle={user.role}{', superadmin' if superadmin else ''}")
            return user
    finally:
        if db is None:
            session.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Crée un utilisateur en base.")
    parser.add_argument("--email", required=True, help="Email de l'utilisateur")
    parser.add_argument("--password", required=True, help="Mot de passe")
    parser.add_argument("--name", default="Admin", help="Nom affiché")
    parser.add_argument("--organisation", default=SLUG_PAR_DEFAUT,
                        help="Slug de l'organisation (créée si absente)")
    parser.add_argument("--nom-organisation", default=None, help="Nom de l'organisation si elle est créée")
    parser.add_argument("--role", default=ADMIN, choices=ROLES, help="Rôle dans l'organisation")
    parser.add_argument("--superadmin", action="store_true",
                        help="Administrateur de la plateforme (peut créer des organisations)")
    args = parser.parse_args()
    create_user(email=args.email, password=args.password, name=args.name, organisation=args.organisation,
                role=args.role, superadmin=args.superadmin, nom_organisation=args.nom_organisation)
