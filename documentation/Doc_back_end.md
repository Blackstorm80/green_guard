# Documentation technique du back-end GreenGuard

> À jour au 2026-10-04 (phase 3, multi-organisations). Le **contrat d'API de référence** est le schéma OpenAPI
> généré par FastAPI : `http://localhost:8000/docs` (Swagger) ou `/openapi.json`, servis
> uniquement si `ENABLE_DOCS=true` (développement ; 404 sinon).

## 1. Architecture

Architecture en couches (Onion) : les dépendances vont toujours vers le domaine.

| Couche | Dossier | Rôle |
|---|---|---|
| Domaine | `domain/logic/`, `domain/ports/`, `domain/models.py` | Calculs purs (moteur hydrique FAO-56, bilan hydrique, prévision à 7 jours et décision, stress, clustering, arrosage, carbone, droits par rôle, slugs d'organisation) et interfaces (ports) |
| Application | `application/use_cases/`, `application/dto/` | Orchestration des cas d'usage, objets de sortie |
| Infrastructure | `infrastructure/` | Base de données, repositories, services externes (Open-Meteo), job planifié, logs |
| API | `api/`, `schema/`, `main.py` | Routes FastAPI, authentification, middlewares, schémas de validation |

Écart connu (ADR-3, post-v1) : les entités du domaine sont encore des modèles SQLAlchemy
(`domain/models.py`). La logique de `domain/logic/` n'accède jamais à la base, ce qui la
rend testable sans base (voir `tests/test_domaine.py`).

```text
back_end/
├── main.py                      # Application FastAPI : middlewares, CORS, routes (préfixe unique /api/v1)
├── worker.py                    # Service worker : tâches planifiées (une seule instance)
├── config.py                    # Seul module qui lit les variables d'environnement
├── api/
│   ├── deps/auth.py             # bcrypt, JWT (PyJWT), cookie de session, CSRF, exiger_role / exiger_superadmin
│   ├── deps/rate_limit.py       # Limitation de débit (login, inscription)
│   ├── middleware.py            # En-têtes de sécurité, X-Request-ID, journal d'accès, erreur 500 générique
│   └── v1/endpoints/            # Une ressource par fichier
├── application/use_cases/       # capteurs, interventions, zones, météo, végétal, bilans journaliers (génération,
│                                # rattrapage), bilans hydriques (historique, diagnostic expliqué), prévision, organisations
├── domain/logic/                # fao56 (moteur hydrique), bilan_hydrique, prevision (7 jours, décision), stress_sanitaire,
│                                # arrosage, bilan_carbone, clustering,
│                                # droits (rôles → permissions), organisations (slug, nom par défaut)
├── infrastructure/
│   ├── database.py              # Moteur SQLAlchemy, convention de nommage des contraintes
│   ├── rls.py                   # Contexte d'organisation des transactions PostgreSQL (Row Level Security)
│   ├── jobs/mise_a_jour_capteurs.py   # bilans du jour, mesures, alertes (stress critique, arrosage à prévoir)
│   ├── repositories/            # espaces verts, bilans hydriques, apports d'eau (arrosages), organisations et membres
│   └── services/                # Open-Meteo (conditions, série passée, prévision ; cache par point), lecture capteurs groupée
├── alembic/                     # Migrations : seule source du schéma
├── scripts/load/taxonomy.py     # Chargement du catalogue iNaturalist
└── tests/                       # pytest (SQLite par défaut, PostgreSQL via TEST_DATABASE_URL)
```

## 2. Ressources de l'API (`/api/v1`)

Une instance sert plusieurs **organisations** (collectivités) totalement cloisonnées ; les membres
d'une même organisation partagent son patrimoine. Lecture : tout membre. Écriture : selon le rôle (§ 3).

| Préfixe | Lecture | Écriture | Contenu |
|---|---|---|---|
| `/auth` | public (limité en débit) | public | `POST /login` (formulaire OAuth2), `POST /register` (JSON, crée une organisation), `POST /logout` |
| `/users` | connecté | — | `GET /me` (dont `organisation {id, nom}`, `role`, `permissions`, `est_superadmin`), `GET /me/notifications` (`espace_id` : espace concerné par une alerte, ou `null`) |
| `/organisations` | connecté | voir colonne Contenu | `GET /moi` ; `PUT /moi` (paramètres : gestionnaire ; nom : admin) ; `GET /moi/membres` ; `PUT /moi/membres/{id}` (admin : rôle, désactivation) ; `POST /` (superadmin : organisation + premier admin) |
| `/espaces-verts` | connecté | gestionnaire | CRUD complet (`reserve_utile_effective_mm` en lecture, `debit_arrosage_l_min` facultatif) ; `GET /{id}/bilans?jours=30` (historique des bilans et de leurs termes, 1 à 365 jours, par date croissante) ; `GET /{id}/prevision` (réserve projetée J..J+7, dates de bascule, décision ; 409 sans bilan FAO-56 récent, 502 si la météo prévue est indisponible ; § 4) |
| `/zones` | connecté | gestionnaire | `GET /`, `POST /clustering/rebuild` |
| `/capteurs` | connecté | — | `GET /dashboard` (synthèse, lectures avec `dose_recommandee`, `decision` et `date_bascule` de la prévision à 7 jours, `date_calcul`, météo extérieure) |
| `/interventions` | connecté | technicien (création, suivi) ; gestionnaire (suppression) | `GET /urgent`, CRUD ; un arrosage terminé avec un volume est compté dans le bilan (`arrosage_compte_mm` en lecture, § 4) |
| `/notifications` | connecté (les siennes) | connecté (les siennes) | liste, `POST /{id}/mark-as-read` |
| `/catalogue` | connecté | — | `GET /plantes`, `GET /auxiliaires` (pagination `offset`/`limit`) |
| `/meteo` | connecté | — | `GET /actuelle?lat&lon`, `GET /{ville}` |
| `/vegetal` | gestionnaire | — | `GET /etat-global`, `GET /impact-carbone` (patrimoine de l'organisation) |
| `/health` | public / connecté | — | `GET /live`, `GET /ready` (base), `POST /diagnostic` (lecture seule : statut, message, `explication` calculée, `dose_recommandee`, `conseil_arrosage`, mesures et termes du dernier bilan) |

« gestionnaire » se lit « gestionnaire ou admin », « technicien » « technicien, gestionnaire ou admin ».

Règle d'isolation : toute ressource est filtrée sur l'**organisation** de l'utilisateur (directement,
ou via l'espace auquel elle est rattachée) ; les notifications restent personnelles. Un objet d'une
autre organisation répond **404** (et non 403), pour ne pas révéler son existence.

**Inscription (provisoire)** : `POST /auth/register` crée une nouvelle organisation (`organisation`,
facultatif, sinon « Organisation de <nom> ») dont le compte est administrateur. Rejoindre une
organisation existante passera par une invitation (lot Confiance) ; d'ici là, l'admin de la plateforme
ajoute les agents avec `create_user.py --organisation <slug> --role <rôle>`.

## 3. Sécurité

- **Session** : JWT HS256 (60 min, `iat`, `jti`, `type`) dans le cookie `gg_session`
  (`HttpOnly`, `Secure`, `SameSite=Lax`, chemin `/api`). L'en-tête `Authorization: Bearer`
  reste accepté pour Swagger et les scripts.
- **CSRF** : une écriture authentifiée par cookie exige l'en-tête `X-Requested-With`.
- **Mots de passe** : bcrypt, 12 caractères minimum. **`SECRET_KEY`** : 32 caractères minimum.
- **Rôles** dans l'organisation, relus en base à chaque requête (jamais depuis le jeton) ; un compte
  désactivé perd l'accès immédiatement. Dépendance `exiger_role(*roles)` sur toutes les routes d'écriture
  (`domain/logic/droits.py`) :

  | Rôle | Droits |
  |---|---|
  | `lecteur` (élu) | consultation seule |
  | `technicien` | + créer et suivre (terminer) une intervention |
  | `gestionnaire` | + espaces, zones, suppression d'intervention, paramètres métier, indicateurs végétaux |
  | `admin` | + nom de l'organisation, membres (rôle, désactivation) ; l'organisation garde toujours un admin actif |

  `est_superadmin` (administrateur de la plateforme, indépendant du rôle) : création d'organisations.
- **Isolation par la base** (défense en profondeur, PostgreSQL) : Row Level Security avec
  `FORCE ROW LEVEL SECURITY` (migration `0002_organisations`). Politique :
  `organisation_id = app.organisation_id OR app.contourner_rls = 'on'` sur `organisations`, `users`,
  `espaces_verts`, `zones_intelligentes`, `clustering_configs` (la configuration d'instance, sans
  organisation, reste lisible par tous) ; sous-requête sur `espaces_verts` pour les tables rattachées
  à un espace (mesures, bilans, capteurs, interventions, alertes, arrosages, zone_espaces) ; sur `users`
  pour les notifications. Le contexte est posé en local à la transaction (`set_config(…, true)`, comme
  `SET LOCAL`) et donc **reposé au début de chaque transaction** par l'événement `after_begin` de la
  fabrique de sessions, à partir de `session.info` renseigné par l'authentification (`infrastructure/rls.py`).
  Contournement explicite et limité : lecture du compte à l'authentification, inscription, création
  d'organisation, liste des organisations par le worker (chaque organisation est ensuite traitée dans
  son contexte), scripts d'administration, migrations Alembic. **La RLS ne s'applique pas à un
  superutilisateur ni à un rôle `BYPASSRLS`** : l'API doit se connecter avec un rôle dédié
  (voir `exploitation.md`) ; sinon elle l'indique au démarrage par un avertissement. Sous SQLite, seul le
  filtrage applicatif s'applique.
- **Limitation de débit** (en mémoire, fenêtre `AUTH_RATE_WINDOW_S`) : la connexion est limitée
  par identifiant (e-mail en minuscules, `AUTH_RATE_LIMIT`) **et** par IP (`AUTH_RATE_LIMIT_IP`, large :
  toute une collectivité peut sortir par la même IP) ; l'inscription par IP (`AUTH_RATE_LIMIT`).
  Le 429 est identique que le compte existe ou non. Derrière un reverse proxy, l'IP du client n'est
  connue que si ce proxy figure dans `TRUSTED_PROXIES` (`--forwarded-allow-ips` d'uvicorn).
- **Documentation interactive** (`/docs`, `/redoc`, `/openapi.json`) : fermée par défaut (`ENABLE_DOCS`).
- **En-têtes** : CSP stricte (sauf `/docs` quand elle est ouverte), `X-Frame-Options: DENY`, `nosniff`,
  `Referrer-Policy`, HSTS si `HSTS=true`. Les erreurs 500 ne renvoient qu'un message
  générique et un `request_id` à retrouver dans les logs.

## 4. Métier

### Bilan hydrique journalier (moteur FAO-56 paysager)
`domain/logic/fao56.py` (calcul pur) et `application/use_cases/generer_bilans_hydriques_journaliers.py`,
appelé chaque heure par le worker. Référence : FAO Irrigation and Drainage Paper 56 (1998), chapitre 8.

Le « jour » est celui de `FUSEAU_HORAIRE` (Europe/Paris par défaut), pour le bilan comme pour les
cumuls météo demandés à Open-Meteo : un passage à 0 h 30 (heure de Paris) produit le bilan du jour
qui commence sans écraser celui de la veille. Arrosages et notifications sont comptés sur ce même jour
(voir « Boucle arrosage → bilan » pour l'origine des arrosages).

**Réserve de l'espace.** `TAW = Δθ × Zr × 1000` (mm). Δθ par texture (FAO-56 tableau 19, milieu de
fourchette) : Sableux 0,08 ; Limoneux 0,155 ; Limon-Argileux 0,155 ; Argileux 0,16 ; inconnue 0,14.
Zr = `profondeur_racinaire` (cm / 100) si renseignée, sinon selon le type d'espace : gazon, pelouse,
Square 0,3 m ; Jardin, massif 0,4 ; Parc 0,5 ; arbres, Rue 0,8 ; Toiture 0,15 ; autre 0,4.
`RAW = p × TAW`, p = 0,5. **Règle de surcharge** : `reserve_utile_max` est facultatif ; NULL (cas par
défaut) = TAW calculée ; une valeur saisie la remplace. `reserve_utile_effective_mm` (lecture) donne
la réserve réellement utilisée. `coefficient_cultural` est le coefficient paysager KL (défaut 0,8, gazon).

**Bilan d'une journée** sur l'épuisement racinaire Dr (mm, 0 = réserve pleine) :
1. Météo du jour (Open-Meteo) : ET0 et cumul de pluie, mis en cache par point (~10 km, 15 min).
2. Point de départ : `epuisement_fin_mm` du dernier bilan **antérieur** au jour (réserve pleine s'il
   n'y en a pas ; pour un bilan `historique-v1`, indice de stress × TAW actuelle).
3. Pluie efficace Pe = pluie si pluie ≥ 2 mm, sinon 0 (petite pluie interceptée et ré-évaporée ;
   ruissellement négligé). Ks = 1 si Dr ≤ RAW, sinon (TAW − Dr) / (TAW − RAW), évalué sur Dr de début
   de journée. ETc = ET0 × KL × Ks.
4. `Dr_fin = Dr_début − Pe − arrosage + ETc + DP`, borné à [0, TAW] ; DP = drainage profond (eau au-delà
   de la capacité au champ), calculé et conservé. ETc est bornée par l'eau restante : le bilan est fermé.
5. Statut : *Optimal* si Dr ≤ RAW ; *A surveiller* jusqu'à RAW + (TAW − RAW) / 2 ; *Critique* au-delà.
   `indice_stress = Dr / TAW` ; `reserve_utile_fin_journee = TAW − Dr`.
6. Tous les termes sont **conservés** dans `bilans_hydriques` (`et0_mm`, `kl`, `ks`, `etc_mm`, `pluie_mm`,
   `pluie_efficace_mm`, `arrosage_mm`, `drainage_mm`, `epuisement_debut_mm`, `epuisement_fin_mm`,
   `taw_mm`, `raw_mm`, `version_modele` = `fao56-paysager-1`, `source_meteo`). Les bilans antérieurs
   (migration `0003_moteur_fao56`) portent `version_modele = historique-v1` et des termes NULL.
7. Le bilan du jour est **remplacé** s'il existe déjà (idempotent : relancer ne décompte pas deux fois).
8. Une mesure est enregistrée ; un espace *Critique* déclenche une notification (une par jour).

**Rattrapage.** Si le dernier bilan date de plus d'un jour (worker arrêté…), chaque jour manquant est
recalculé dans l'ordre avec la série journalière passée d'Open-Meteo (`start_date`/`end_date`, ET0 et
pluie dans le fuseau métier) et les arrosages de chaque jour, puis le jour courant. 92 jours au plus
(limite d'Open-Meteo) : au-delà, la chaîne repart du dernier bilan connu. Si la série est indisponible
ou incomplète, rien n'est écrit pour l'espace (ni le jour courant, pour ne pas enchaîner sur un trou) ;
le rattrapage est retenté au passage suivant.

**Diagnostic expliqué.** `POST /health/diagnostic` ajoute une phrase calculée sur les 30 derniers bilans,
par exemple « Réserve à 34 % : il a manqué 18 mm depuis la dernière pluie (9 mm, il y a 2 jours) ;
évapotranspiration de 4,2 mm/j. » (ETc moyenne sur 7 jours ; absente pour un bilan `historique-v1`).

Comparé à l'ancien modèle (réserve fixe de 100 mm, facteur de sol empirique, seuils 0,3 / 0,6 sur la
réserve), un gazon sur limon (Zr 0,3 m, TAW 46,5 mm) à ET0 4 mm/j sans pluie passe « A surveiller » au
jour 8 au lieu de 10 et « Critique » au jour 12 au lieu de 19 (même coefficient 0,8). Les tables de sols
et de profondeurs restent **à faire valider par un agronome partenaire**.

### Boucle arrosage → bilan
`application/use_cases/interventions.py` (`synchroniser_action_irrigation`), appelé par chaque écriture
d'une intervention (`POST`, `PUT`, `DELETE /interventions`), dans la même transaction.

- Une intervention de type `arrosage` **terminée** (passée à `terminee`, ou créée directement avec
  `statut: "terminee"`) avec `volume_eau_l > 0` crée un apport `actions_irrigation` :
  `quantite_mm = volume_eau_l / surface_m2` (1 L/m² = 1 mm), horodaté à `realisee_le` (posée à
  l'instant de la saisie si absente). Le volume saisi est le volume réellement versé : l'efficacité du
  système n'est pas déduite, l'excédent éventuel sort du bilan par drainage.
- `actions_irrigation.intervention_id` est **unique** : terminer de nouveau, ou corriger le volume, met
  à jour l'apport existant, jamais de double comptage. Repasser l'intervention en `planifiee` ou
  `en_cours` (annulation : `realisee_le` est effacée), changer son type, ramener le volume à 0 ou la
  supprimer retire l'apport.
- **Surface inconnue** (nulle ou absente) : refus **422** avec un message clair (« Surface de l'espace
  inconnue : renseignez sa surface… »), rien n'est enregistré. Choix retenu plutôt qu'une hauteur d'eau
  saisie à la main : une seule source de vérité (le volume), et la surface sert aussi à la dose.
  Un arrosage terminé **sans** volume reste accepté et ne compte rien. `realisee_le` dans le futur
  (au-delà de 5 min de décalage d'horloge) : 422. Volume borné à 10 000 m³.
- **Recalcul immédiat** (`recalculer_bilan_espace`) après validation : bilan du jour de l'espace
  recalculé avec le cas d'usage du worker (météo du cache Open-Meteo, 15 min). Pour un arrosage daté
  d'un jour passé, les bilans existants depuis ce jour sont d'abord recalculés dans l'ordre avec la série
  journalière (92 jours au plus). Si la météo est indisponible, l'intervention est tout de même validée :
  le passage horaire suivant recompte l'apport du jour (un jour passé non corrigé garde son bilan).
- Migration `0004_boucle_arrosage` : les arrosages déjà terminés avec un volume (et une surface connue)
  reçoivent leur apport ; les bilans passés ne sont pas recalculés.

### Dose recommandée
`domain/logic/arrosage.py` (`dose_recommandee`, calcul pur), exposée dans chaque lecture de
`GET /capteurs/dashboard` et dans `POST /health/diagnostic` : `dose_recommandee: {mm, litres, minutes}`.

- `mm` = épuisement Dr du dernier bilan (quantité qui ramène la réserve à la capacité au champ),
  plafonné à la TAW, au dixième.
- `litres` = mm × `surface_m2` / efficacité, arrondi au litre ; efficacité selon `type_irrigation` :
  goutte-à-goutte 0,9 ; aspersion 0,75 ; manuel / tuyau 0,7 ; autre ou non renseigné 0,75.
  `null` si la surface est inconnue.
- `minutes` = litres / `debit_arrosage_l_min` (débit de l'espace, facultatif), à la minute supérieure ;
  `null` sans débit.
- `null` pour un bilan `historique-v1` (termes inconnus) ou sans bilan.
- Exemple : Dr 30 mm sur 1 000 m² en aspersion → 40 000 L ; à 100 L/min → 400 min.
  Le diagnostic ajoute `conseil_arrosage`, par exemple « Pour remplir la réserve : 30 mm, soit 40 000 L
  (400 min au débit de l'arrosage). » (`null` si la réserve est pleine).

Le front pré-remplit le volume d'un arrosage déclenché depuis le tableau de bord avec `litres`
(modifiable) et demande le volume réel au moment de « Terminer » (page Rapports).

### Prévision à 7 jours et décision d'arrosage
`domain/logic/prevision.py` (calcul pur), `application/use_cases/prevision.py`.

- **Météo prévue** : `OpenMeteoService.recuperer_prevision_journaliere` interroge l'API de prévision
  d'Open-Meteo (`daily=et0_fao_evapotranspiration,precipitation_sum,precipitation_probability_max`,
  `timezone=FUSEAU_HORAIRE`, `forecast_days=8` : le premier jour renvoyé est aujourd'hui, il en faut donc
  8 pour couvrir J..J+7). Même cache par point (~10 km, 15 min) et même verrou anti-appels concurrents
  que les conditions du jour, délai d'attente de 10 s ; la clé de cache contient le **jour métier**, si bien
  qu'une prévision mise en cache avant minuit n'est pas resservie le lendemain. Un **échec est mémorisé
  60 s** pour ce point, afin qu'un fournisseur en panne ne coûte pas un délai d'attente à chaque lecture du
  tableau de bord. Les valeurs reçues sont contrôlées (nombres finis ; ET0 de 0 à 30 mm, pluie de 0 à
  1 000 mm, probabilité de 0 à 100 %) : une réponse aberrante est traitée comme une panne et n'est pas mise
  en cache. Au-delà de 1 000 entrées, chaque écriture purge les entrées expirées du cache.
- **Projection** : à partir du dernier bilan FAO-56 (du jour, repris tel quel ; ou de la veille, auquel cas
  le jour courant est projeté avec la météo du jour), même moteur que le bilan (`calculer_journee`),
  jour par jour jusqu'à J+7, **sans arrosage futur**. Bilan plus ancien, bilan `historique-v1` ou jour de
  prévision sans ET0 : pas de prévision.
- **Pluie comptée (règle prudente)** : J : cumul du jour (comme le bilan) ; J+1 et J+2 (fenêtre de la
  consigne d'arrosage) : cumul compté seulement si la pluie est **acquise** (probabilité ≥ 70 % **et**
  cumul ≥ 5 mm), sinon 0 ; J+3 à J+7 (indicatif) : cumul × probabilité (probabilité inconnue : 0). Le seuil
  de pluie efficace (2 mm) s'applique ensuite. Sous-estimer la pluie fait au pire arroser un peu tôt ; la
  surestimer laisserait un espace sans eau : une pluie seulement probable ne supprime jamais la consigne.
- **Dates de bascule** : premier jour de la série en « A surveiller » (ou pire) et premier jour en
  « Critique » (J s'il l'est déjà). `date_bascule` du tableau de bord = bascule en Critique.
- **Décision** (horizon de décision J+3 ; au-delà, la prévision est indicative) :

  | Code | Condition | Texte (exemple) |
  |---|---|---|
  | `arroser` | Critique à J+2 ou avant, pluie acquise comprise | « Arroser au plus tard le mardi 14 juillet : critique prévu le mercredi 15 juillet. Pour remplir la réserve : 32,8 mm, soit 43 785 L (438 min au débit de l'arrosage). » |
  | `reporter` | sans pluie, Critique à J+2 ou avant, **mais** la pluie acquise de J+1 ou J+2 maintient l'espace hors Critique jusqu'à J+2 au moins | « Reporter l'arrosage : pluie de 12 mm attendue demain (probabilité 80 %). » (+ « Critique prévu ensuite le … : à surveiller. » si la bascule tombe à J+3) |
  | `surveiller` | Critique entre J+3 et J+7 | « Critique prévu le samedi 18 juillet : à surveiller (prévision indicative). » |
  | `rien` | aucune bascule en Critique sur 7 jours | « Aucun besoin d'arrosage prévu sur 7 jours. » (+ date de passage « à surveiller » éventuelle) |

  `arroser` porte `date_limite` (veille de la bascule, au plus tôt aujourd'hui) et `dose_recommandee`
  (§ Dose recommandée) calculée sur l'épuisement projeté au jour limite ; `reporter` porte `jour_pluie`
  et `pluie_attendue_mm`. La décision est recalculée à chaque lecture : si la pluie annoncée n'est pas
  tombée, le bilan du lendemain le constate et la décision repasse d'elle-même à `arroser`.
- **`GET /espaces-verts/{id}/prevision`** : `jours[]` (J..J+7 : `reserve_mm`, `reserve_percent`, `statut`,
  `et0_mm`, `pluie_mm`, `probabilite_pluie_pct`, `pluie_comptee_mm`, `pluie_acquise`, `indicatif`,
  `issu_du_bilan`), `date_bascule_a_surveiller`, `date_bascule_critique`, `decision`, `avertissement`
  (incertitude : indicative au-delà de J+3, probabilité régionale ~27 km), `source_meteo`.
- **Tableau de bord** : chaque lecture porte `decision` et `date_bascule` ; la réponse porte `date_calcul`
  (jour métier du serveur, référence du front pour situer `date_bascule`). La météo prévue est lue par
  point (un appel pour tous les espaces d'un même point de ~10 km, grâce au cache). Au premier échec du
  fournisseur, les points suivants ne sont pas interrogés : les champs restent `null` et le reste du
  tableau de bord est servi normalement ; toute autre erreur de prévision ne prive que l'espace concerné.
- **Alerte du worker** : quand la décision d'un espace est `arroser`, une notification
  `arrosage_a_prevoir` (« Arrosage à prévoir sur « Square Gare » au plus tard le mardi 14 juillet. Pour
  remplir la réserve : … ») est émise **une fois par espace, par destinataire et par jour** (membres
  pouvant intervenir), même si la date limite change dans la journée. Un espace déjà Critique ne la reçoit
  pas (l'alerte de stress critique suffit). Météo prévue indisponible, ou toute autre erreur de prévision
  (journalisée) : rien n'est émis, les bilans, mesures et alertes de stress sont tout de même enregistrés. Les alertes portent `notifications.espace_id` (migration `0005_prevision_notifications`,
  `ON DELETE SET NULL` : l'historique survit à la suppression de l'espace ; les alertes de stress déjà
  émises y sont rattachées quand leur message désigne sans ambiguïté un espace de l'organisation).

### Impact carbone (estimation grossière)
`domain/logic/bilan_carbone.py` : séquestration des arbres urbains selon Nowak & Crane (2002),
0,306 kg C par m² de couvert arboré et par an, soit ≈ 1,12 kg CO₂/m²/an (× 44/12), appliquée comme
**majorant** (surface supposée entièrement arborée), réduite par le stress du jour puis projetée sur
l'année (× 365). `GET /vegetal/impact-carbone` renvoie `estimation_grossiere: true` et `methode`
(texte court à afficher avec le chiffre) ; totaux et détail par zone portent sur la même période.

### Zones intelligentes
`domain/logic/clustering.py` : K-Means sur les coordonnées projetées en km. Nombre de zones
dans `clustering_configs.n_clusters` (configuration de l'organisation, sinon celle de l'instance,
sinon 5). Les zones appartiennent à l'organisation : un recalcul remplace celles de toute l'organisation. Les centroïdes et rayons sont en coordonnées réelles.

## 5. Configuration (variables d'environnement)

| Variable | Défaut | Rôle |
|---|---|---|
| `DATABASE_URL` | — (obligatoire) | Connexion PostgreSQL |
| `SECRET_KEY` | — (obligatoire, ≥ 32) | Signature des JWT |
| `FRONTEND_URL` | — | Origine CORS supplémentaire |
| `COOKIE_SECURE` | `true` | Cookie de session réservé à HTTPS (localhost accepté) |
| `ACCESS_TOKEN_MINUTES` | `60` | Durée de session |
| `AUTH_RATE_LIMIT` / `AUTH_RATE_WINDOW_S` | `10` / `60` | Connexion : tentatives par identifiant ; inscription : par IP (par fenêtre, en s) |
| `AUTH_RATE_LIMIT_IP` | `100` | Connexion : tentatives par IP et par fenêtre |
| `TRUSTED_PROXIES` | `127.0.0.1` | Proxys (adresses ou CIDR) dont `X-Forwarded-For` est cru (CMD du Dockerfile) |
| `ENABLE_DOCS` | `false` | Ouvre `/docs`, `/redoc`, `/openapi.json` (développement) |
| `FUSEAU_HORAIRE` | `Europe/Paris` | Jour métier du bilan et des cumuls météo (nom IANA) |
| `ENABLE_SCHEDULER` | `false` | Job intégré à l'API (développement sans worker) |
| `LOG_FORMAT` / `LOG_LEVEL` | `text` / `INFO` | `json` en production |
| `HSTS` | `false` | À activer derrière HTTPS |

## 6. Exploitation

- **Migrations** : `alembic upgrade head` (lancé automatiquement au démarrage du conteneur).
  Après toute modification de `domain/models.py` : `alembic revision --autogenerate -m "…"`,
  relire le fichier généré, puis vérifier `alembic check`.
- **Worker** : un seul `python worker.py` (service `worker` de docker-compose).
- **Catalogue** : `python -m scripts.load.taxonomy [--dry-run]` (idempotent).
- **Comptes** : `python create_user.py --email … --password … [--organisation <slug>] [--nom-organisation …]
  [--role admin|gestionnaire|technicien|lecteur] [--superadmin]` (organisation `defaut` si non précisée,
  créée si absente ; rôle `admin` par défaut).
- **Sondes** : `/api/v1/health/live` (processus) et `/api/v1/health/ready` (base).
- **Qualité** : `ruff check .` et `pytest --cov=…` (seuil CI : 85 %). La CI rejoue les tests et
  les migrations sur PostgreSQL et audite les dépendances.

## 7. Dépannage

| Symptôme | Cause probable |
|---|---|
| L'API refuse de démarrer : « SECRET_KEY trop courte » | Générer une clé de 64 caractères hexadécimaux |
| 401 alors que l'utilisateur vient de se connecter | Cookie `Secure` sur une origine HTTP autre que localhost : `COOKIE_SECURE=false` en local |
| 403 « protection CSRF » | Requête par cookie sans en-tête `X-Requested-With` |
| 429 sur la connexion | Limitation de débit : attendre la durée de `Retry-After` |
| Tableau de bord « En attente » | Aucun passage du worker encore : `python -m infrastructure.jobs.mise_a_jour_capteurs` |
| Décision de prévision absente du tableau de bord | Pas encore de bilan FAO-56 du jour ou de la veille, ou Open-Meteo injoignable (échec mémorisé 60 s) |
| `Can't locate revision ab36bd25cc59` | Base créée avant la migration v1 : recréer la base de développement |
| Avertissement « RLS inopérante » au démarrage | L'API se connecte en superutilisateur : créer le rôle applicatif (`exploitation.md`) |
| 403 « Permissions insuffisantes » | Rôle insuffisant pour l'action (lecteur, technicien) : à changer par un admin de l'organisation |
| Requêtes SQL manuelles sans résultat (rôle applicatif) | Normal sous RLS : `SELECT set_config('app.organisation_id', '<id>', false)` ou `set_config('app.contourner_rls', 'on', false)` dans la session psql |
