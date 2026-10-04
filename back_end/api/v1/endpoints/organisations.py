"""Organisation de l'utilisateur connecté, ses membres, et création d'organisations (superadmin)."""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from api.deps.auth import exiger_role, exiger_superadmin, get_current_user, get_password_hash
from application.use_cases.organisations import (
    EmailDejaUtiliseError,
    MembreIntrouvableError,
    SlugDejaUtiliseError,
    creer_organisation_avec_admin,
    mettre_a_jour_organisation,
    modifier_membre,
)
from domain.logic.droits import ADMIN, ROLES_ADMINISTRATION, ROLES_GESTION, DernierAdministrateurError
from domain.models import User
from infrastructure.database import get_db
from infrastructure.repositories.organisation_repository_impl import OrganisationRepositoryImpl
from infrastructure.rls import contournement_rls
from schema.organisations import MembreRead, MembreUpdate, OrganisationCreate, OrganisationRead, OrganisationUpdate

router = APIRouter()


@router.get("/moi", response_model=OrganisationRead)
def lire_mon_organisation(current_user: User = Depends(get_current_user)):
    return current_user.organisation


@router.put("/moi", response_model=OrganisationRead)
def modifier_mon_organisation(
    data: OrganisationUpdate,
    current_user: User = Depends(exiger_role(*ROLES_GESTION)),
    db: Session = Depends(get_db),
):
    """Paramètres métier : gestionnaire ou administrateur. Nom de l'organisation : administrateur seul."""
    champs = data.model_dump(exclude_unset=True)
    if "nom" in champs and current_user.role != ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permissions insuffisantes")
    return mettre_a_jour_organisation(OrganisationRepositoryImpl(db), current_user.organisation, champs)


@router.get("/moi/membres", response_model=list[MembreRead])
def lister_membres(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return OrganisationRepositoryImpl(db).lister_membres(current_user.organisation_id)


@router.put("/moi/membres/{membre_id}", response_model=MembreRead)
def modifier_un_membre(
    membre_id: int,
    data: MembreUpdate,
    current_user: User = Depends(exiger_role(*ROLES_ADMINISTRATION)),
    db: Session = Depends(get_db),
):
    """Change le rôle ou désactive un membre. L'organisation garde toujours un administrateur actif."""
    try:
        return modifier_membre(OrganisationRepositoryImpl(db), current_user.organisation_id, membre_id,
                               role=data.role, actif=data.is_active)
    except MembreIntrouvableError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Membre introuvable") from None
    except DernierAdministrateurError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from None


@router.post("/", response_model=OrganisationRead, status_code=status.HTTP_201_CREATED)
def creer_organisation(
    data: OrganisationCreate,
    _: User = Depends(exiger_superadmin),
    db: Session = Depends(get_db),
):
    """Administrateur de la plateforme : crée une organisation et son premier administrateur."""
    # Opération hors du périmètre de l'organisation du superadmin ; la réponse est construite avant
    # la fin du contournement, la nouvelle organisation n'étant pas lisible depuis son contexte.
    with contournement_rls(db):
        try:
            organisation = creer_organisation_avec_admin(
                OrganisationRepositoryImpl(db), nom=data.nom, slug=data.slug, admin_name=data.admin.name,
                admin_email=data.admin.email, mot_de_passe_hache=get_password_hash(data.admin.password),
            )
        except SlugDejaUtiliseError:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Identifiant déjà utilisé.") from None
        except (EmailDejaUtiliseError, IntegrityError):
            db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT,
                                detail="Impossible de créer l'administrateur.") from None
        return OrganisationRead.model_validate(organisation)
