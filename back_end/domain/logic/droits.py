"""Rôles d'un membre dans son organisation et droits associés (relus en base à chaque requête)."""

ADMIN = "admin"
GESTIONNAIRE = "gestionnaire"
TECHNICIEN = "technicien"
LECTEUR = "lecteur"
ROLES = (ADMIN, GESTIONNAIRE, TECHNICIEN, LECTEUR)

# Lecteur (élu) : consultation seule. Chaque niveau ajoute des droits au précédent.
ROLES_INTERVENTION = (ADMIN, GESTIONNAIRE, TECHNICIEN)   # créer, terminer une intervention
ROLES_GESTION = (ADMIN, GESTIONNAIRE)                    # espaces, zones, paramètres métier, indicateurs
ROLES_ADMINISTRATION = (ADMIN,)                          # membres de l'organisation

# Droits exposés au front (/users/me) pour afficher ou masquer les actions
PERMISSIONS = {
    "interventions": ROLES_INTERVENTION,
    "gestion": ROLES_GESTION,
    "membres": ROLES_ADMINISTRATION,
}


def permissions_du_role(role: str) -> list[str]:
    return [permission for permission, roles in PERMISSIONS.items() if role in roles]


class DernierAdministrateurError(ValueError):
    """La modification laisserait l'organisation sans administrateur actif."""


def verifier_admin_restant(role_actuel: str, actif_actuel: bool, nouveau_role: str, actif_apres: bool,
                           admins_actifs: int) -> None:
    """Refuse de retirer le dernier administrateur actif (rétrogradation ou désactivation)."""
    perd_l_administration = role_actuel == ADMIN and actif_actuel and (nouveau_role != ADMIN or not actif_apres)
    if perd_l_administration and admins_actifs <= 1:
        raise DernierAdministrateurError(
            "L'organisation doit conserver au moins un administrateur actif."
        )
