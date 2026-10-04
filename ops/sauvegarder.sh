#!/usr/bin/env sh
# Sauvegarde de la base PostgreSQL de GreenGuard (format personnalisé pg_dump, compressé).
#
# Usage : ops/sauvegarder.sh [dossier_de_sortie]        (défaut : ./sauvegardes)
# Variables : COMPOSE_PROJECT (défaut : greenguard), RETENTION_JOURS (défaut : 14)
#
# À planifier chaque nuit (cron) et à copier HORS du serveur (stockage objet, autre machine).
set -eu

PROJET="${COMPOSE_PROJECT:-greenguard}"
DOSSIER="${1:-./sauvegardes}"
RETENTION="${RETENTION_JOURS:-14}"
HORODATAGE="$(date -u +%Y%m%dT%H%M%SZ)"
FICHIER="${DOSSIER}/greenguard-${HORODATAGE}.dump"

mkdir -p "$DOSSIER"
# pg_dump s'exécute dans le conteneur : aucun mot de passe ne transite par la ligne de commande
docker compose -p "$PROJET" exec -T db pg_dump -U greenguard -d greenguard --format=custom --compress=9 > "$FICHIER"

# Une sauvegarde vide ou illisible est une fausse sécurité : vérification immédiate
TAILLE=$(wc -c < "$FICHIER")
if [ "$TAILLE" -lt 1024 ]; then
  echo "ERREUR : sauvegarde anormalement petite (${TAILLE} octets) : $FICHIER" >&2
  exit 1
fi
docker compose -p "$PROJET" exec -T db pg_restore --list < "$FICHIER" > /dev/null

# Rotation : suppression des sauvegardes locales plus anciennes que la rétention
find "$DOSSIER" -name 'greenguard-*.dump' -type f -mtime +"$RETENTION" -delete

echo "Sauvegarde OK : $FICHIER (${TAILLE} octets)"
