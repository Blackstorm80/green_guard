# Use cases - Bilan hydrique

## 1. Générer les bilans pour tous les espaces

**Nom technique**  
`generer_bilans_hydriques_pour_tous_les_espaces`

**But métier**  
Calculer le bilan hydrique d’une date donnée pour tous les espaces verts gérés, enregistrer ces bilans, et renvoyer un résumé pour le tableau de bord.

**Entrées**

- `date_du_calcul: date`
- `espace_vert_repo: IEspaceVertRepository`
- `bilan_repo: IBilanHydriqueRepository`
- `meteo_service: IMeteoService`
- `notification_service: INotificationService | None`
- `arrosage_par_defaut_mm: float` (optionnel, par défaut 0.0)

**Sortie**

- `list[BilanHydriqueEspaceDTO]`  
  Pour chaque espace :
  - `espace_id: int`
  - `nom_espace: str`
  - `type_espace: str`
  - `date_bilan: date`
  - `statut_hydrique: str`
  - `indice_stress: float`
  - `localisation: str | None`

**Étapes principales**

1. Récupérer tous les espaces via `espace_vert_repo.list_tous()`.
2. Pour chaque espace :
   - Récupérer le dernier bilan via `bilan_repo.get_dernier_bilan_pour_espace(espace.id)`.
   - Appeler `calculer_bilan_hydrique_pour_jour(...)` avec la date du calcul.
   - Sauvegarder le bilan via `bilan_repo.sauvegarder(...)`.
   - Construire un `BilanHydriqueEspaceDTO` avec les infos utiles.
3. Retourner la liste des DTO.

**Erreurs / cas particuliers**

- Erreurs des services externes (météo, notifications) gérées au niveau application ou API.


## 2. Générer le bilan pour un espace

**Nom technique**  
`generer_bilan_hydrique_pour_un_espace`

**But métier**  
Calculer le bilan hydrique d’une date donnée pour un espace précis, par exemple pour une fiche détaillée ou un recalcul ciblé.

**Entrées**

- `espace_id: int`
- `date_du_calcul: date`
- `espace_vert_repo: IEspaceVertRepository`
- `bilan_repo: IBilanHydriqueRepository`
- `meteo_service: IMeteoService`
- `notification_service: INotificationService | None`
- `arrosage_jour_mm: float` (optionnel)

**Sortie**

- `BilanHydriqueEspaceDTO` pour cet espace :
  - `espace_id`
  - `nom_espace`
  - `type_espace`
  - `date_bilan`
  - `statut_hydrique`
  - `indice_stress`
  - `localisation`

**Étapes principales**

1. Récupérer l’espace via `espace_vert_repo.get_by_id(espace_id)`.
   - Si aucun espace trouvé : lever une exception métier (par ex. `EspaceVertIntrouvableError`).
2. Récupérer le dernier bilan via `bilan_repo.get_dernier_bilan_pour_espace(espace_id)`.
3. Appeler `calculer_bilan_hydrique_pour_jour(...)` avec la date du calcul.
4. Sauvegarder le bilan via `bilan_repo.sauvegarder(...)`.
5. Construire et retourner un `BilanHydriqueEspaceDTO`.

