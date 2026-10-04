# GreenGuard — pistes d'évolution

> 2026-10-04 · Méthode : 6 analyses indépendantes (métier et eau, produit et front, données et IA,
> plateforme back, marché, confiance et conformité) ayant produit 42 pistes ; contre-expertise des
> faits externes (sources web citées en fin de document) et de la faisabilité dans le code ;
> 6 pistes écartées. Les défauts cités au § 0 ont été revérifiés un par un dans le code.

## 0. Avant toute évolution : défauts confirmés à corriger pour la v1.0

L'analyse a mis au jour des défauts qui avaient échappé à la recette. Tous ont été vérifiés dans le code.

| # | Défaut | Nature | Gravité |
|---|---|---|---|
| 1 | L'API est publiée sur le port 8000 de toutes les interfaces : en production, elle reste joignable sans passer par le proxy HTTPS | Sécurité (déploiement) | 🔴 |
| 2 | Derrière un proxy, toutes les requêtes semblent venir de la même adresse IP (seule `127.0.0.1` est considérée comme proxy de confiance) : 10 mauvais mots de passe par minute suffisent à bloquer la connexion de toute la collectivité | Sécurité (déni de service) | 🔴 |
| 3 | La documentation interactive (`/docs`, `/openapi.json`) est ouverte en production | Sécurité (exposition) | 🟠 |
| 4 | L'inscription est ouverte à n'importe qui, alors qu'un outil de collectivité devrait fonctionner sur invitation | Sécurité (produit) | 🟠 |
| 5 | Un arrosage validé n'est jamais compté dans le bilan : les interventions ne créent pas d'`ActionIrrigation`. L'espace reste « Critique » et l'alerte revient chaque jour | Fonctionnel | 🟠 |
| 6 | Le jour du bilan est calculé en UTC alors que la météo est en heure locale : entre 0 h et 2 h (heure de Paris), le bilan de la veille est écrasé | Fonctionnel | 🟠 |
| 7 | L'API météo gratuite d'Open-Meteo est réservée à un usage non commercial : une licence est nécessaire pour vendre le service | Juridique | 🟠 |
| 8 | Carbone affiché d'environ 18 kg CO₂/m²/an, un ordre de grandeur bien au-delà des références pour les espaces verts urbains | Crédibilité | 🟡 |
| 9 | Une partie des photos iNaturalist du catalogue est sous licence non commerciale | Juridique | 🟡 |

Les correctifs 1 à 6 et 8 représentent quelques jours de travail. Les points 7 et 9 sont des décisions du porteur de projet.

## 1. Le constat

Aujourd'hui, GreenGuard fait ce que font beaucoup d'outils : il affiche pour chaque espace un état du jour (Optimal, À surveiller, Critique) et gère des interventions. Trois défauts le rendent « standard ».

- **Il constate sans anticiper.** La météo n'est lue que pour le jour même, et l'alerte arrive quand l'espace est déjà critique.
- **Il ne voit pas l'eau apportée.** Un arrosage saisi n'est jamais compté dans le bilan, si bien qu'un espace arrosé reste « Critique » et l'alerte revient chaque jour.
- **Ses chiffres ne tiennent pas devant un expert.** Les seuils ne sont pas validés, la réserve est fixée à 100 mm partout, et le carbone affiché est 15 à 20 fois trop élevé.

Pourtant, l'application a déjà la base d'un positionnement rare. Elle calcule un bilan hydrique quotidien sur plusieurs sites sans aucun matériel. Et elle vise le marché français, où les arrêtés sécheresse et la sobriété en eau sont devenus des sujets politiques pour les élus.

## 2. Le positionnement proposé

> **GreenGuard, le copilote de l'eau des espaces verts publics : il dit quoi arroser, quand et combien, dans le respect des arrêtés sécheresse, et il prouve les économies, sans un seul capteur.**

### Pari 1 : passer du thermomètre au pilote d'arrosage

- **Problème.** Le chef d'équipe ne peut pas planifier ses tournées 2 à 3 jours à l'avance. Il arrose parfois la veille d'une pluie de 15 mm, et le bouton « Arroser » crée une intervention sans volume.
- **Ce que GreenGuard ferait :**
  - prévoir la réserve en eau sur 7 jours ;
  - donner la date de bascule (« Critique jeudi, arroser mercredi au plus tard ») ;
  - proposer une décision explicite : arroser, reporter car la pluie arrive, ou rien à faire ;
  - chiffrer la dose en litres et en minutes ;
  - recalculer le bilan dès que l'agent valide l'arrosage.
- **Pourquoi personne ne le fait aussi bien.** Les GMAO des collectivités gèrent des bons de travaux sans modèle agronomique. Les programmateurs connectés n'anticipent que pour un site équipé de vannes automatiques. Or une grande partie de l'arrosage public se fait au tuyau ou à la tonne à eau (jeunes arbres, massifs).
- **Valeur mesurable.**
  - 2 à 4 jours d'anticipation, contre 0 aujourd'hui.
  - Chaque arrosage par aspersion évité avant une pluie de 15 mm sur 1 ha économise environ 200 m³ (15 mm × 10 000 m² / rendement 0,75).
  - Les fausses alertes répétées après un arrosage disparaissent.

### Pari 2 : le mode sécheresse conforme

- **Problème.** En été, les arrêtés préfectoraux encadrent ou interdisent l'arrosage des espaces verts. D'après le guide national 2023, il est interdit de 11 h à 18 h en alerte et en principe totalement interdit en alerte renforcée et en crise. Aujourd'hui, GreenGuard peut recommander « arrosage sans délai » en pleine crise.
- **Ce que GreenGuard ferait :**
  - lire chaque jour le niveau VigiEau au point exact de chaque espace ;
  - bloquer ou décaler les recommandations ;
  - trier l'eau disponible : jeunes plantations, puis arbres, puis massifs ;
  - tenir un registre exportable de chaque arrosage, avec le niveau en vigueur et la dérogation éventuelle (jeunes plantations de moins de 2 ans par défaut, paramétrable).
- **Pourquoi personne ne le fait aussi bien.** À notre connaissance, aucun outil du marché ne croise le besoin calculé avec l'arrêté en vigueur, ni ne fournit un registre prêt pour un contrôle. L'API VigiEau est publique, gratuite et sans clé.
- **Valeur mesurable.**
  - Objectif : zéro arrosage hors créneau autorisé. Une infraction relève en général d'une contravention de 5e classe, à confirmer selon l'arrêté.
  - Préparation d'un contrôle de la DDT : un export au lieu de plusieurs heures de reconstitution.
  - **Contrainte de calendrier :** à livrer avant mi-mai 2027.

### Pari 3 : la preuve des économies d'eau, opposable

- **Problème.** Un élu doit pouvoir dire « nous avons économisé X m³ et Y € » devant le conseil, l'agence de l'eau ou un financeur. Aujourd'hui, aucun chiffre n'est vérifiable après coup : le bilan ne conserve ni l'évapotranspiration, ni la pluie, ni l'arrosage, ni les pertes.
- **Ce que GreenGuard ferait :**
  - conserver tous les termes du bilan, jour par jour ;
  - comparer trois volumes : la référence convenue avec le client, le volume recommandé et le volume réel ;
  - corriger les économies de l'effet météo (« à climat constant ») ;
  - produire un rapport annuel où chaque chiffre renvoie à sa méthode, utilisable pour le rapport développement durable, l'annexe budget vert et un dossier Fonds vert.
- **Pourquoi personne ne le fait aussi bien.** Les plateformes ESG ne savent pas calculer l'eau d'un parc, et les études ponctuelles coûtent cher. Ici, la preuve est continue et couvre tout le patrimoine.
- **Valeur mesurable.** Exemple : 10 ha arrosés par aspersion consomment environ 27 000 m³ par saison. Les systèmes pilotés par l'évapotranspiration affichent couramment 15 à 30 % d'économie (ordre de grandeur à confirmer sur un pilote). À 20 %, cela fait environ 5 400 m³ par an, soit 10 à 20 k€ selon le prix local du m³.
- **Contrainte de calendrier :** les termes du bilan doivent être stockés dès la v1.1, sinon il n'y aura pas de rapport crédible à l'automne 2027.

## 3. Pistes par domaine

Effort : S = quelques jours, M = 2 à 4 semaines, L = 1 à 2 mois, pour une petite équipe.

### Métier & eau

| Piste | Ce que ça apporte | Effort | Horizon |
|---|---|---|---|
| Boucle arrosage → bilan, et dose chiffrée | Un arrosage validé remonte la réserve ; volume pré-rempli en litres | S (lot 1), puis M (feuille de route) | v1.0.x / v1.1 |
| Conserver tous les termes du bilan | Évapotranspiration, pluie, arrosage et pertes stockés : historique, recalcul et preuves deviennent possibles | S | v1.1 |
| Moteur hydrique de référence FAO (« FAO-56 paysager ») | Réserve calculée selon le sol et les racines, statuts fondés sur la physique, rattrapage des jours manqués | L | v1.1 |
| Prévision à 7 jours, décision « reporter » | Date de bascule, arrosage reporté avant la pluie | M | v1.1 |
| Mode sécheresse VigiEau | Conformité, tri de l'eau, registre | L (2 lots) | v1.1 et v1.2 |
| Plantations sous garantie et tournées | Arrosage à la tonne à eau planifié, taux de reprise suivi | M | v1.2 |
| Comptabilité de l'eau et rapport d'impact | m³ et € économisés, rapport annuel sourcé | L | v1.2 |
| Indicateurs environnementaux | Carbone ramené à un ordre de grandeur défendable, « kWh de fraîcheur » | S, puis M | v1.1 → v2 |
| Priorités canicule | Réserver l'eau aux espaces proches d'écoles, de crèches et d'EHPAD | M | v2 |
| Simulateur de conversion (gazon → prairie) | m³ et € par an d'un choix de plantation | M | v2 |

- **Moteur FAO-56.** C'est la crédibilité de tout le reste. Avec le modèle actuel, un gazon sur limon semble tenir environ 25 jours sans eau, contre environ 11 en réalité : l'alerte arrive 2 à 5 fois trop tard. Il faut un agronome partenaire pour valider les tables de sols et de végétaux, sinon on remplace un arbitraire par un autre.
- **Prévision.** Le service Météo-France (dans Open-Meteo) ne couvre que 2 à 4 jours. Au-delà, jusqu'à J+7, il faut un modèle global. La probabilité de pluie est régionale (environ 27 km) et doit être présentée comme indicative. On ne décide pas au-delà de J+3, et une relance automatique est prévue si la pluie annoncée n'est pas tombée.
- **Mode sécheresse, lot 1 (v1.1).** Niveau VigiEau par espace et par jour, pastilles et blocage dans l'interface, champ « source d'eau » (réseau, forage, rivière), registre CSV.
- **Mode sécheresse, lot 2 (v1.2).** Règles paramétrables selon l'arrêté-cadre de chaque département, tri de l'eau, PDF, dérogations.

### Front & expérience

| Piste | Ce que ça apporte | Effort | Horizon |
|---|---|---|---|
| Vue carte du parc | Les espaces critiques repérés d'un coup d'œil ; la liste reste l'alternative accessible | M | v1.1 |
| Carnet de santé de l'espace | Courbe de réserve sur 90 jours, phrase « pourquoi c'est critique » | M | v1.1 |
| Import du patrimoine (CSV + géocodage d'adresses) | 200 espaces importés en moins d'une heure au lieu d'environ 10 h ; démo sur la vraie commune du prospect | M | v1.1 |
| Curseur temporel J-30 à J+7 sur la carte | Voir son parc « sécher », l'effet démo | M | v1.2 |
| Alertes actionnables et point du matin par e-mail | « Planifier », « Reporter 24 h » en un clic ; alertes regroupées par zone | M | v1.2 |
| Mode terrain « Ma tournée » (mobile) | Un geste « Fait » avec volume pré-rempli | M | v1.2 |
| Bulletin mensuel pour l'élu | 4 chiffres en langage clair, PDF prêt pour le conseil | M | v1.2 |
| Page publique et données ouvertes | Transparence en période de restriction, publication sur data.gouv.fr | M | v2 |

- **Carte.** Fond Plan IGN, dont le service vectoriel est signalé en bêta, avec un fond OpenStreetMap en secours. Les pastilles ont des formes différentes en plus des couleurs (accessibilité). Il faut autoriser les tuiles IGN dans la politique de sécurité du site (CSP).
- **Mode terrain.** Pas de géolocalisation continue des agents : c'est une donnée de surveillance des salariés, qui impose une information préalable et un passage devant le comité social territorial. Le mode hors-ligne (application installable) ne vient que si un pilote en confirme le besoin.

### Back & plateforme

| Piste | Ce que ça apporte | Effort | Horizon |
|---|---|---|---|
| Jour du bilan calculé à l'heure de Paris | Supprime l'écrasement du bilan de la veille entre 0 h et 2 h | S | avant v1.0 |
| Exploitation minimale | Licence météo commerciale, signal de vie du worker, remontée des espaces ignorés, suivi des erreurs (Sentry/GlitchTip) | S | v1.1 |
| Archivage au lieu de la suppression | Un espace supprimé n'efface plus son historique ni la preuve | S | v1.1 |
| Distinguer mesures « modèle » et « capteur » | Évite de mélanger demain données simulées et données réelles | S | v1.1 |
| Multi-organisations, isolées par la base de données | Équipes, élu en lecture seule, une seule instance pour plusieurs collectivités | L | v1.2 |
| Prestataires de marchés, contrats et secteurs | Une entreprise du paysage ne voit que son lot, pendant la durée du contrat | L | v2 |
| Socle géographique PostGIS et export vers QGIS | Vraies surfaces, noms de zones parlants (« Quartier Gare ») | L | à la demande |
| API publique et webhooks | Intégration avec les GMAO | L | v2, à la demande |

- **Multi-organisations.** Un piège technique a été repéré : le contexte d'organisation doit être reposé à chaque transaction, sinon l'application se bloque. Il faut aussi faire tourner les tests sur PostgreSQL, car les tests actuels sous SQLite ne vérifient pas ce cloisonnement.
- **Licence météo.** L'offre commerciale Standard d'Open-Meteo suffit pour les prévisions. L'archive, l'historique et les ensembles exigent l'offre Professional. Les données ouvertes de Météo-France sont l'alternative.

### Données & IA

| Piste | Ce que ça apporte | Effort | Horizon |
|---|---|---|---|
| Valider la prévision sur les saisons passées | Chiffrer les arrosages évités et les reports à tort avant de promettre | S | v1.1 |
| Composition végétale de chaque espace | Besoin en eau selon ce qui est réellement planté ; référentiel d'espèces françaises (TAXREF) | L | v1.2 |
| Capteurs réels LoRaWAN, une sonde par zone | Recaler le modèle avec environ 30 sondes au lieu de 300 | L | v1.2, si un pilote est équipé |
| Satellite Sentinel-2 | Vérification indépendante du modèle, indice de confiance par espace | L | v2 |
| Biocontrôle par degrés-jours | Traiter les chenilles au bon stade (processionnaire du pin d'abord) | M | v2 |
| Retrait du dossier inaturalist/ | Ménage du dépôt | S | v1.1 |

- **Validation de la prévision.** Elle se fait avec l'API « Previous Runs » d'Open-Meteo, archivée seulement depuis janvier 2024 : on valide donc sur 2024-2026.
- **Identification par photo (Pl@ntNet).** C'est une option, pas le cœur : gratuite jusqu'à 500 identifications par jour en usage non commercial, offre Pro payante au-delà.
- **Satellite.** Seuls les grands espaces sont observables : environ 0,2 ha pour l'indice de vigueur (NDVI), 0,5 ha pour l'indice d'eau (NDMI). Il faut d'abord la carte et PostGIS. Le quota gratuit de Copernicus (10 000 unités de traitement par mois) suffit pour un client, pas pour plusieurs.
- **Biocontrôle.** Il dépend de la composition végétale, et un expert (FREDON ou INRAE) doit valider le modèle avant toute alerte.

### Confiance & conformité

| Piste | Ce que ça apporte | Effort | Horizon |
|---|---|---|---|
| **Correctifs d'exposition** | Ferme des brèches encore ouvertes, voir ci-dessous | S | **avant v1.0** |
| Sauvegardes hors serveur, restauration chronométrée | Perte de données maximale : 5 minutes au lieu de 24 h ; temps de reprise mesuré chaque semaine | M | v1.1 |
| Inscription sur invitation, réinitialisation du mot de passe, double authentification | Fin de l'inscription libre ; double authentification obligatoire pour les rôles admin et manager | M | v1.1 |
| Journal d'audit et sessions révocables | « Qui a supprimé quoi » ; la déconnexion coupe vraiment l'accès | M | v1.1 |
| Audit d'accessibilité RGAA et déclaration fournie | Évite au client une sanction et un audit à ses frais | M | v1.1 |
| Kit RGPD et licences des images | Accord de sous-traitance, registre, durées de conservation, images sous licence | M | v1.1 |
| Connexion unique (SSO) : OIDC générique, Entra ID, ProConnect | Les agents se connectent avec leur compte habituel | M | v1.2 |

**Point honnête sur la sécurité.** La reprise a bien colmaté l'essentiel, mais l'analyse a révélé quatre problèmes à corriger avant le 1er décembre :

- l'API est publiée sur le port 8000 de toutes les interfaces, ce qui contourne le proxy HTTPS ;
- la documentation Swagger est ouverte en production ;
- derrière le proxy, tous les utilisateurs partagent la même adresse IP : un seul attaquant peut bloquer la connexion de toute la collectivité, la limite de 10 tentatives par minute devenant collective ;
- l'API météo gratuite est réservée à un usage non commercial.

**Autres points de conformité :**

- **ProConnect** est en principe ouvert à un éditeur qui agit pour une collectivité, à confirmer avec la DINUM. Il faut un OIDC générique pour les comptes privés (prestataires).
- **RGAA.** Une nouvelle version 5 est annoncée pour fin 2026. Il vaut mieux auditer sur la 5 si elle est publiée, ou au minimum sur la 4.1.2 complétée des critères WCAG 2.2.
- **Images du catalogue.** Une partie des photos iNaturalist est sous licence non commerciale (« NC ») ou tous droits réservés, donc inutilisable par un service payant. Si le catalogue est abandonné, le plus simple est de retirer les images.

## 4. Feuille de route

**Avant la v1.0 (d'ici au 1er décembre 2026)**

1. Corriger les expositions : port, documentation, IP derrière le proxy.
2. Souscrire la licence météo commerciale.
3. Calculer le jour du bilan à l'heure de Paris.
4. Lot 1 de la boucle arrosage → bilan (S), car c'est un défaut fonctionnel visible en démo.
5. Étiqueter le carbone « estimation grossière ».

**v1.1 (T1 2027) : fiabiliser le cœur et tenir le calendrier sécheresse**

Ordre imposé par les dépendances :

1. Conserver les termes du bilan. C'est la base de l'historique, de la prévision et des preuves.
2. Moteur FAO-56, avec l'agronome partenaire.
3. Prévision à 7 jours et validation sur 2024-2026.
4. Mode sécheresse, lot 1.

En parallèle :

- côté utilisateurs : carte, carnet de santé, import ;
- côté confiance : sauvegardes, invitation et double authentification, journal d'audit, RGAA, RGPD, archivage.

*La v1.1 est chargée. Avec 2 à 3 personnes, la priorité va à la boucle, aux termes du bilan, à la prévision, à VigiEau et aux correctifs de confiance. FAO-56 et l'import peuvent glisser de quelques semaines.*

**v1.2 (T2 2027) : être prêt pour l'été et pour plusieurs clients**

- Mode sécheresse, lot 2, avant juin.
- Multi-organisations. C'est le prérequis pour vendre à une deuxième collectivité ; d'ici là, une instance par client.
- Curseur J+7, alertes actionnables, mode terrain, plantations et tournées, bulletin pour l'élu.
- Générateur du rapport d'impact (premier rapport de saison complet à l'automne).
- Composition végétale, connexion unique OIDC, capteurs si un pilote est équipé.

**v2 (S2 2027) : élargir la valeur**

- PostGIS, puis satellite (PostGIS et carte d'abord).
- Simulateur de conversion, priorités canicule, biocontrôle (après la composition).
- Données ouvertes, prestataires et contrats, API publique si un client la demande.

**Au-delà**

Palette végétale 2050 et règle de diversification 10-20-30, solveur de tournées, probabilités par ensembles météo, application installable hors-ligne, hébergement SecNumCloud pour les clients qui l'exigent.

## 5. Ce que je déconseille

- **Faire de l'IA avec le dossier inaturalist/.** Les vecteurs d'images sont tronqués, la flore est surtout nord-américaine, et le jeu contient des araignées et des oies des neiges.
- **TimescaleDB.** Le volume de données est faible et PostgreSQL suffit. Il suffit d'arrêter de stocker 24 mesures calculées par jour.
- **Un diagnostic complet des îlots de chaleur** (satellite Landsat, LiDAR, données INSEE Filosofi). C'est un métier d'étude à part entière. On garde seulement la couche des zones climatiques du Cerema. Ne pas promettre TRISHNA, dont le lancement est prévu vers octobre 2027.
- **Une calibration statistique lourde ou la détection de fuites par télérelève** sans données réelles. On garde des règles simples : sonde figée, saut impossible.
- **Un modèle de survie des plantations.** Il faut 3 ans de données qui n'existent pas encore.
- **Le signalement citoyen anonyme avec photo, et l'identification Pl@ntNet ouverte aux citoyens.** Cela élargit la surface d'attaque et la charge de modération pour peu de valeur.
- **Le temps réel et les notifications push avant le mode terrain.** Le calcul est horaire ; un rafraîchissement périodique suffit.
- **Les modèles de rapport CSRD/ESRS.** Les collectivités n'y sont pas soumises, et les seuils ont été fortement relevés en 2026.
- **Une file de tâches et un monitoring lourd avant environ 2 000 espaces.**
- **Mélanger la stratégie commerciale et le backlog technique.** Pour l'offre « achetable sans appel d'offres », le seuil de dispense de procédure est de **60 000 € HT** depuis le 1er avril 2026 (décret n° 2025-1386), et non plus 40 000 €.

## 6. Sources vérifiées

**Météo**
- Open-Meteo, variables, prévision jusqu'à 16 jours et rattrapage jusqu'à 92 jours : https://open-meteo.com/en/docs
- Open-Meteo, service Météo-France (AROME 2 jours, ARPEGE 4 jours) : https://open-meteo.com/en/docs/meteofrance-api
- Open-Meteo, offres et conditions d'usage : https://open-meteo.com/en/pricing · https://open-meteo.com/en/terms
- Open-Meteo, Previous Runs (prévisions archivées) et Ensemble : https://open-meteo.com/en/docs/previous-runs-api · https://open-meteo.com/en/docs/ensemble-api
- Météo-France, évapotranspiration quotidienne en données ouvertes : https://www.data.gouv.fr/datasets/donnees-etp-spatialisees-quotidiennes

**Sécheresse**
- API VigiEau : https://github.com/MTES-MCT/vigieau-api · https://www.data.gouv.fr/dataservices/api-vigieau
- Données sécheresse VigiEau : https://www.data.gouv.fr/datasets/donnee-secheresse-vigieau
- Guide sécheresse 2023 (dérogation pour les plantations de moins de 2 ans, interdictions) : https://www.banquedesterritoires.fr/la-secheresse-menace-malgre-les-pluies-printanieres

**Cartographie et territoire**
- Géocodage des adresses, transféré à l'IGN : https://www.data.gouv.fr/posts/lapi-adresse-de-la-base-adresse-nationale-est-transferee-a-lign-10
- Tuiles vectorielles Plan IGN : https://guides.data.gouv.fr/reutiliser-des-donnees/utiliser-les-api-geographiques/utiliser-les-tuiles-vectorielles
- Zones climatiques locales du Cerema (93 territoires) : https://www.data.gouv.fr/datasets/cartographie-des-zones-climatiques-locales-lcz-des-93-territoires-de-plus-de-50-000-habitants-en-france
- Base permanente des équipements de l'INSEE : https://www.insee.fr/fr/metadonnees/source/operation/s2278/processus-statistique
- PostGIS chez Scaleway : https://www.scaleway.com/en/managed-postgresql-mysql/

**Satellite**
- Quotas Copernicus : https://documentation.dataspace.copernicus.eu/Quotas.html

**Végétal et climat**
- WUCOLS : https://wucols.ucdavis.edu/project-background
- Pl@ntNet (offres) : https://my.plantnet.org/pricing
- Jeu AVEC de Plante & Cité : https://www.data.gouv.fr/datasets/avec-adaptation-du-vegetal-au-climat-de-demain
- TRACC : https://www.consultations-publiques.developpement-durable.gouv.fr/IMG/pdf/arrete_notice_tracc.pdf
- SESAME (Cerema) : https://www.cerema.fr/fr/print/pdf/node/14358
- i-Tree Eco à l'international : https://www.itreetools.org/tools/i-tree-eco/i-tree-eco-international
- Licences des photos iNaturalist : https://www.inaturalist.org/posts/30692-tech-tip-tuesday-understanding-licensing

**Données ouvertes et financements**
- Schéma « arbres urbains » : https://www.data.gouv.fr/datasets/arbres-urbains
- Budget vert : https://www.senat.fr/questions/base/2024/qSEQ241000617.html
- Fonds vert, mesure renaturation : https://aides-territoires.beta.gouv.fr/aides/financer-des-solutions-d-adaptation-au-changement-climatique-fondees-sur-la-renaturation-des-villes-et-des-villages/

**Identité, sécurité, conformité**
- ProConnect, éligibilité : https://partenaires.proconnect.gouv.fr/docs/fournisseur-service/eligibilite_installation
- CNIL, mots de passe (délibération 2022-100) : https://cnil.fr/sites/cnil/files/atoms/files/deliberation-2022-100-du-21-juillet-2022_recommandation-aux-mots-de-passe.pdf
- CNIL, journalisation : https://cnil.fr/la-cnil-publie-une-recommandation-relative-aux-mesures-de-journalisation
- Prestataires qualifiés SecNumCloud : https://www.donneespersonnelles.fr/secnumcloud-certification
- RGAA 5 annoncé : https://binclusive.io/en/blog/rgaa-5-france-digital-accessibility-standard
- Seuil de dispense de procédure à 60 000 € HT : https://blog.landot-avocats.net/2026/04/01/marches-publics-relevement-du-seuil-de-dispense-de-procedure-a-60-000-e-des-aujourdhui/