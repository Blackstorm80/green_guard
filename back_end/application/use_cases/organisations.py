"""Cas d'usage des organisations : création (inscription, superadmin), paramètres, membres.

La création d'une organisation et la vérification d'unicité de l'e-mail portent sur toute l'instance :
l'appelant les exécute hors contexte d'organisation (contournement explicite de la RLS).
"""
from domain.logic.droits import ADMIN, ROLES, verifier_admin_restant
from domain.logic.organisations import generer_slug, nom_organisation_par_defaut, slug_disponible
from domain.logic.secheresse import CLE_PARAMETRES as CLE_SECHERESSE
from domain.models import Organisation, User
from domain.ports.organisation_repository import IOrganisationRepository


class EmailDejaUtiliseError(ValueError):
    pass


class SlugDejaUtiliseError(ValueError):
    pass


class MembreIntrouvableError(LookupError):
    pass


def _creer_organisation(repo: IOrganisationRepository, nom: str, slug: str | None) -> Organisation:
    if slug is None:
        slug = slug_disponible(generer_slug(nom), repo.slug_existe)
    elif repo.slug_existe(slug):
        raise SlugDejaUtiliseError(slug)
    organisation = Organisation(nom=nom.strip(), slug=slug)
    repo.ajouter(organisation)
    return organisation


def _creer_admin(repo: IOrganisationRepository, organisation: Organisation, name: str, email: str,
                 mot_de_passe_hache: str) -> User:
    admin = User(name=name, email=email, hashed_password=mot_de_passe_hache,
                 organisation_id=organisation.id, role=ADMIN)
    repo.ajouter(admin)
    return admin


def inscrire(repo: IOrganisationRepository, name: str, email: str, mot_de_passe_hache: str,
             nom_organisation: str | None = None) -> User:
    """Inscription libre (provisoire, avant l'invitation) : nouvelle organisation dont le compte est admin."""
    if repo.email_existe(email):
        raise EmailDejaUtiliseError(email)
    organisation = _creer_organisation(repo, nom_organisation or nom_organisation_par_defaut(name), None)
    admin = _creer_admin(repo, organisation, name, email, mot_de_passe_hache)
    repo.valider()
    return admin


def creer_organisation_avec_admin(repo: IOrganisationRepository, nom: str, slug: str | None, admin_name: str,
                                  admin_email: str, mot_de_passe_hache: str) -> Organisation:
    """Création par un superadmin : l'organisation et son premier administrateur, ou rien."""
    if repo.email_existe(admin_email):
        raise EmailDejaUtiliseError(admin_email)
    organisation = _creer_organisation(repo, nom, slug)
    _creer_admin(repo, organisation, admin_name, admin_email, mot_de_passe_hache)
    repo.valider()
    return organisation


def mettre_a_jour_organisation(repo: IOrganisationRepository, organisation: Organisation,
                               champs: dict) -> Organisation:
    if "nom" in champs and champs["nom"] is not None:
        organisation.nom = champs["nom"].strip()
    if "parametres" in champs:
        # Les règles sécheresse ont leur propre route, réservée à l'administrateur : jamais modifiées ici
        parametres = {k: v for k, v in (champs["parametres"] or {}).items() if k != CLE_SECHERESSE}
        existantes = (organisation.parametres or {}).get(CLE_SECHERESSE)
        if existantes is not None:
            parametres[CLE_SECHERESSE] = existantes
        organisation.parametres = parametres or (None if champs["parametres"] is None else {})
    repo.valider()
    return organisation


def definir_regles_secheresse(repo: IOrganisationRepository, organisation: Organisation,
                              regles: dict) -> Organisation:
    """Règles validées (schema/secheresse.py) ; nouveau dictionnaire : la colonne JSON est bien réécrite."""
    organisation.parametres = {**(organisation.parametres or {}), CLE_SECHERESSE: regles}
    repo.valider()
    return organisation


def modifier_membre(repo: IOrganisationRepository, organisation_id: int, membre_id: int,
                    role: str | None = None, actif: bool | None = None) -> User:
    membre = repo.get_membre(organisation_id, membre_id)
    if membre is None:
        raise MembreIntrouvableError(membre_id)
    nouveau_role = membre.role if role is None else role
    actif_apres = membre.is_active if actif is None else actif
    if nouveau_role not in ROLES:
        raise ValueError(f"Rôle inconnu : {nouveau_role}")
    verifier_admin_restant(membre.role, membre.is_active, nouveau_role, actif_apres,
                           repo.compter_admins_actifs(organisation_id))
    membre.role, membre.is_active = nouveau_role, actif_apres
    repo.valider()
    return membre
