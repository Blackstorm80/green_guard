"""Mode sécheresse : niveau VigiEau des espaces de l'organisation, relevé à la demande, registre des arrosages."""
from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from api.deps.auth import exiger_role, get_current_user
from api.deps.rate_limit import RateLimiter
from application.dto.secheresse import EtatSecheresseDTO
from application.use_cases.generer_bilans_hydriques_journaliers import bornes_du_jour
from application.use_cases.secheresse import actualiser_restrictions, etat_secheresse, registre_csv
from config import settings
from domain.logic.droits import ROLES_GESTION, ROLES_REGISTRE
from domain.logic.secheresse import regles_depuis_parametres
from domain.models import User
from domain.ports.vigieau import IVigieauService
from infrastructure.database import get_db
from infrastructure.repositories.espace_vert_repository_impl import EspaceVertRepositoryImpl
from infrastructure.repositories.restriction_secheresse_repository_impl import (
    RegistreSecheresseRepositoryImpl,
    RestrictionSecheresseRepositoryImpl,
)
from infrastructure.services.vigieau import VigieauService

router = APIRouter()
PERIODE_REGISTRE_MAX_JOURS = 1096   # 3 ans
# Bornes des dates du registre (hors de ces bornes, les conversions de fuseau débordent)
JOUR_MIN, JOUR_MAX = date(2000, 1, 1), date(2100, 12, 31)
# Actualisation à la demande : par organisation, pour qu'une panne VigiEau (délai d'attente par espace)
# ne puisse pas monopoliser les connexions à force de clics
limiteur_actualisation = RateLimiter(max_requetes=5, fenetre_s=600)
# Durée maximale des appels VigiEau d'une actualisation à la demande : le reste est relevé par le worker
BUDGET_ACTUALISATION_S = 60


def get_vigieau_service() -> IVigieauService:
    return VigieauService()


def _etat(db: Session, user: User) -> EtatSecheresseDTO:
    espaces = EspaceVertRepositoryImpl(db).list_par_organisation(user.organisation_id)
    return etat_secheresse(espaces, RestrictionSecheresseRepositoryImpl(db),
                           regles_depuis_parametres(user.organisation.parametres), settings.fuseau)


@router.get("/etat", response_model=EtatSecheresseDTO)
def lire_etat(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Niveau VigiEau du jour de chaque espace (relevé chaque jour par le worker) et synthèse.
    Espaces triés par priorité d'arrosage : jeunes plantations, arbres, massifs, puis le reste."""
    return _etat(db, current_user)


@router.post("/actualiser", response_model=EtatSecheresseDTO)
def actualiser(
    current_user: User = Depends(exiger_role(*ROLES_GESTION)),
    db: Session = Depends(get_db),
    vigieau: IVigieauService = Depends(get_vigieau_service),
):
    """Relève tout de suite le niveau du jour de chaque espace (cache VigiEau par point et par jour).
    Cinq actualisations par organisation et par tranche de dix minutes au plus (429 au-delà) ; appels
    VigiEau limités à BUDGET_ACTUALISATION_S secondes (les espaces restants sont relevés par le worker)."""
    limiteur_actualisation.consommer(f"organisation:{current_user.organisation_id}:secheresse")
    maintenant = datetime.now(UTC)
    espaces = EspaceVertRepositoryImpl(db).list_par_organisation(current_user.organisation_id)
    actualiser_restrictions(espaces, RestrictionSecheresseRepositoryImpl(db), vigieau,
                            maintenant.astimezone(settings.fuseau).date(), maintenant,
                            liberer=db.commit, budget_s=BUDGET_ACTUALISATION_S)
    db.commit()
    return _etat(db, current_user)


@router.get("/registre", response_class=Response,
            responses={200: {"content": {"text/csv": {}}, "description": "Registre CSV (« ; », UTF-8 avec BOM)"}})
def exporter_registre(
    du: date | None = Query(None, ge=JOUR_MIN, le=JOUR_MAX,
                            description="Premier jour (inclus) ; défaut : 1er janvier de l'année du jour « au »"),
    au: date | None = Query(None, ge=JOUR_MIN, le=JOUR_MAX, description="Dernier jour (inclus) ; défaut : aujourd'hui"),
    current_user: User = Depends(exiger_role(*ROLES_REGISTRE)),
    db: Session = Depends(get_db),
):
    """Registre des arrosages réalisés : niveau VigiEau en vigueur, plage autorisée, dérogation et agent,
    figés au moment de chaque arrosage. Prêt pour un contrôle (DDT, police de l'eau)."""
    au = au or datetime.now(settings.fuseau).date()
    du = du or au.replace(month=1, day=1)
    if du > au:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail="La date de début doit précéder la date de fin.")
    if (au - du).days >= PERIODE_REGISTRE_MAX_JOURS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                            detail="Période trop longue : 3 ans au plus par export.")
    debut, _ = bornes_du_jour(du, settings.fuseau)
    fin, _ = bornes_du_jour(au + timedelta(days=1), settings.fuseau)
    lignes = RegistreSecheresseRepositoryImpl(db).lister(current_user.organisation_id, debut, fin)
    return Response(
        content=registre_csv(lignes, settings.fuseau).encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="registre_secheresse_{du}_{au}.csv"'},
    )
