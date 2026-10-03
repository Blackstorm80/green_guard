# Cas d'usage

> Source de vérité : le code (`back_end/application/use_cases/`). Ce document en est le résumé
> fonctionnel, mis à jour le 2026-10-04 (décision HR-5 : le code fait foi).

## 1. Générer les bilans hydriques du jour

**Fonction** : `generer_bilans_hydriques_journaliers` (`generer_bilans_hydriques_journaliers.py`)
**Déclencheur** : service worker, toutes les heures (premier passage au démarrage).

**Entrées** : espaces à traiter, repository des bilans, service météo, fonction donnant le cumul
d'arrosage du jour par espace, date du calcul (aujourd'hui par défaut).

**Sortie** : `RapportGeneration` : espaces traités (espace, bilan, conditions météo) et identifiants
des espaces ignorés.

**Étapes**
1. Pour chaque espace, récupérer la météo du jour (ET0 et pluie cumulée).
   Météo indisponible ou ET0 absente : l'espace est ignoré pour ce passage, sans erreur.
2. Calculer le bilan à partir du dernier bilan **antérieur** à la date.
3. Créer le bilan du jour, ou **remplacer** celui qui existe déjà (idempotence).

**Suite (job)** : enregistrement d'une mesure par espace et notification du propriétaire si
l'espace est *Critique* (au plus une par espace et par jour).

## 2. Tableau de bord

**Fonction** : `obtenir_dashboard_capteurs` (`capteurs.py`), route `GET /capteurs/dashboard`.
Lecture groupée des dernières mesures et des derniers bilans des espaces de l'utilisateur
(2 requêtes au total), métriques agrégées (santé, espaces en stress ou critiques, CO₂),
synthèse (*Sain*, *Attention*, *Critique*, *En attente*) et météo extérieure.
Sans mesure, un espace est marqué *Sans donnée* : aucune valeur n'est inventée.

## 3. Interventions urgentes

**Fonction** : `lister_interventions_urgentes` (`interventions.py`), route `GET /interventions/urgent`.
Détection à partir des lectures : stress hydrique *Critique* (priorité critique), CO₂ > 1 200 ppm
et température > 32 °C (priorité haute). Tri par priorité réelle puis par date, identifiants stables.

## 4. Zones intelligentes

**Fonction** : `reconstruire_zones` (`zones.py`), route `POST /zones/clustering/rebuild`.
Regroupe les espaces de l'utilisateur (K-Means géographique), remplace ses zones, calcule pour
chacune centroïde, rayon et santé moyenne.
