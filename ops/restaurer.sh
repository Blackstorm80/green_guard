#!/usr/bin/env sh
# Restauration d'une sauvegarde GreenGuard dans une base PostgreSQL.
#
# Usage :
#   ops/restaurer.sh <fichier.dump> <base_cible>
#
# - base_cible différente de « greenguard » : la base est (re)créée, la production n'est pas touchée.
#   C'est le mode à utiliser pour TESTER une sauvegarde (exercice mensuel recommandé).
# - base_cible = « greenguard » : restauration de production. Exige CONFIRMER_ECRASEMENT=oui,
#   et l'arrêt préalable du backend et du worker (docker compose stop backend worker).
# Variable : COMPOSE_PROJECT (défaut : greenguard)
set -eu

FICHIER="${1:?Usage : ops/restaurer.sh <fichier.dump> <base_cible>}"
CIBLE="${2:?Usage : ops/restaurer.sh <fichier.dump> <base_cible>}"
PROJET="${COMPOSE_PROJECT:-greenguard}"
psql_db() { docker compose -p "$PROJET" exec -T db psql -U greenguard -v ON_ERROR_STOP=1 "$@"; }

[ -f "$FICHIER" ] || { echo "ERREUR : fichier introuvable : $FICHIER" >&2; exit 1; }
case "$CIBLE" in
  *[!a-z0-9_]*) echo "ERREUR : nom de base invalide (a-z, 0-9, _) : $CIBLE" >&2; exit 1 ;;
esac

if [ "$CIBLE" = "greenguard" ] && [ "${CONFIRMER_ECRASEMENT:-non}" != "oui" ]; then
  echo "ERREUR : restaurer sur « greenguard » écrase la production." >&2
  echo "Arrêter backend et worker, puis relancer avec CONFIRMER_ECRASEMENT=oui." >&2
  exit 1
fi

psql_db -d postgres -c "DROP DATABASE IF EXISTS ${CIBLE} WITH (FORCE);"
psql_db -d postgres -c "CREATE DATABASE ${CIBLE} OWNER greenguard;"
docker compose -p "$PROJET" exec -T db pg_restore -U greenguard -d "$CIBLE" --no-owner --exit-on-error < "$FICHIER"

echo "Restauration OK dans « ${CIBLE} ». Révision du schéma :"
psql_db -d "$CIBLE" -tAc "SELECT version_num FROM alembic_version;"
