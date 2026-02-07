Rapport global – Côté backend
2. Ports (interfaces de domaine à ajouter)
A. Arrosage

python
from typing import Protocol
from datetime import datetime

class IArrosageService(Protocol):
    def lancer_arrosage(
        self,
        espace_id: int,
        quantite_mm: float,
    ) -> None:
        """Arrosage immédiat équivalent à 'quantite_mm' sur l'espace."""

    def programmer_arrosage(
        self,
        espace_id: int,
        date_heure: datetime,
        quantite_mm: float,
    ) -> None:
        """Programme un arrosage à une date/heure donnée."""

    def definir_mode_arrosage(
        self,
        espace_id: int,
        mode: str,  # "auto" | "manuel" | "suspendu"
    ) -> None:
        """Change le mode d'arrosage pour l'espace."""

B. Couverture / ombrage

python
class ICouvertureService(Protocol):
    def deployer_couverture(self, espace_id: int) -> None: ...
    def retracter_couverture(self, espace_id: int) -> None: ...
    def definir_mode_couverture(
        self,
        espace_id: int,
        mode: str,  # "auto" | "manuel"
    ) -> None: ...

C. Alertes et interventions (hydrique, sanitaire, lumière)

python
class IAlertesRepository(Protocol):
    def marquer_alerte_traitee(self, alerte_id: int) -> None: ...
    def marquer_alerte_en_cours(self, alerte_id: int) -> None: ...
    def ignorer_alerte_temporairement(self, alerte_id: int, jusqu_a: datetime) -> None: ...

    # Optionnel : type_alerte, sous_surveillance, faux_positif...
    # def lister_alertes_actives(self, type_alerte: str | None = None) -> list[AlerteEntity]: ...


class IInterventionRepository(Protocol):
    def creer_intervention(
        self,
        espace_id: int,
        type_intervention: str,  # "hydrique", "sanitaire", "lumiere", ...
        description: str,
        gerant_id: int | None,
    ) -> int:  # id de l'intervention
        ...

Tu peux utiliser type_alerte et type_intervention pour distinguer hydrique / sanitaire / lumière sans multiplier les tables.
3. Use cases (application) à créer
A. Hydrique / arrosage

    declencher_arrosage_immediat(espace_id, quantite_mm, arrosage_service, espace_repo, intervention_repo, ...)

    programmer_arrosage_espace(espace_id, date_heure, quantite_mm, arrosage_service, ...)

    changer_mode_arrosage(espace_id, mode, arrosage_service, ...)

B. Couverture / lumière

    deployer_couverture_espace(espace_id, couverture_service, ...)

    retracter_couverture_espace(espace_id, couverture_service, ...)

    changer_mode_couverture(espace_id, mode, couverture_service, ...)

C. Gestion générique des alertes

    marquer_alerte_en_cours(alerte_id, alertes_repo, ...)

    marquer_alerte_traitee(alerte_id, alertes_repo, ...)

    ignorer_alerte_temporairement(alerte_id, jusqu_a, alertes_repo, ...)

D. Stress sanitaire (spécifique)

    creer_intervention_sanitaire_depuis_alerte(alerte_id, description, gerant_id, intervention_repo, alertes_repo, ...)

    marquer_alerte_sanitaire_sous_surveillance(alerte_id, alertes_repo, ...)

    marquer_alerte_sanitaire_faux_positif(alerte_id, alertes_repo, ...)

4. CO₂ absorbé et O₂ produit (logique métier + dashboard)
A. Nouveau module de domaine (ex : bilan_carbone.py)

    Fonctions d’estimation :

python
def estimer_co2_absorbe_jour(
    espace_vert: EspaceVertEntity,
    stress_hydrique: float,
    stress_sanitaire: float | None,
) -> float:
    """
    Estimation de CO2 absorbé (kg/jour).
    Basée sur une valeur de référence par type d'espace / surface,
    puis modulée par les stress.
    """


def estimer_o2_produit_jour(
    espace_vert: EspaceVertEntity,
    stress_hydrique: float,
    stress_sanitaire: float | None,
) -> float:
    """
    Estimation de O2 produit (kg/jour).
    Même principe que pour le CO2.
    """

    Principe simple :

        base_co2 / base_o2 par type_espace.

        facteur = (1 - stress_hydrique) * (1 - (stress_sanitaire or 0)) borné entre 0 et 1.

        co2_absorbe = base_co2 * facteur, o2_produit = base_o2 * facteur.

    Intégration :

        soit ajout de champs co2_absorbe_jour, o2_produit_jour dans BilanHydriqueJournalierEntity,

        soit calcul à la volée dans le use case dashboard.

B. Use case “dashboard”

    Lire tous les espaces + dernier bilan du jour.

    Calculer :

        total_espaces

        espaces_en_stress (statut hydrique “Critique”)

        sante_globale (score global)

        co2_total_jour = somme des co2_absorbe_jour

        o2_total_jour = somme des o2_produit_jour.

    Retourner un JSON avec ces valeurs, plus les stats par zone et les listes d’alertes/interventions.

5. Endpoints API à exposer
Actions hydriques / lumière / alertes

    Arrosage :

        POST /espaces/{id}/arrosage – body : { "quantite_mm": 5.0 }

        POST /espaces/{id}/arrosage/programmer – body : { "date_heure": "...", "quantite_mm": 10.0 }

        POST /espaces/{id}/arrosage/mode – body : { "mode": "auto" | "manuel" | "suspendu" }

    Couverture :

        POST /espaces/{id}/couverture/deployer

        POST /espaces/{id}/couverture/retracter

        POST /espaces/{id}/couverture/mode – body : { "mode": "auto" | "manuel" }

    Alertes (génériques) :

        POST /alertes/{id}/en-cours

        POST /alertes/{id}/resoudre

        POST /alertes/{id}/ignorer – body : { "jusqu_a": "..." }

    Interventions :

        POST /alertes/{id}/intervention

            body : { "type": "hydrique" | "sanitaire" | "lumiere", "description": "...", "gerant_id": 42 }

Dashboard / indicateurs CO₂ / O₂

    GET /dashboard?date=YYYY-MM-DD

        Retourne :

            section global avec CO₂ / O₂, santé globale, etc.,

            liste des zones,

            listes d’alertes et d’interventions.

