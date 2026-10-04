"""Test de charge léger (phase 4) : flotte cible de 200 espaces verts.

À lancer contre une pile de RECETTE (jamais la production : le script crée un compte et 200 espaces).
    python -m scripts.charge.test_charge --api http://127.0.0.1:8100/api/v1 [--espaces 200]
Avec DATABASE_URL pointant vers la base de cette pile, le job horaire est aussi chronométré.

Seuils de réussite (v1) : p95 < 500 ms sur les routes de lecture sous 20 requêtes simultanées,
aucune erreur, job horaire < 60 s pour 200 espaces.
"""
import argparse
import asyncio
import os
import random
import statistics
import sys
import time
import uuid

import httpx

BACKEND = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

SEUIL_P95_MS = 500
SEUIL_JOB_S = 60
CONCURRENCE = 20
REQUETES_PAR_ROUTE = 200
CENTRE_LYON = (45.764, 4.8357)


def percentile(valeurs, p):
    valeurs = sorted(valeurs)
    return valeurs[min(len(valeurs) - 1, int(round(p / 100 * (len(valeurs) - 1))))]


async def preparer(client: httpx.AsyncClient, nb_espaces: int) -> dict:
    email = f"charge-{uuid.uuid4().hex[:8]}@example.com"
    mot_de_passe = uuid.uuid4().hex
    compte = {"name": "Test de charge", "email": email, "password": mot_de_passe}
    (await client.post("/auth/register", json=compte)).raise_for_status()
    r = await client.post("/auth/login", data={"username": email, "password": mot_de_passe})
    r.raise_for_status()
    entetes = {"Authorization": f"Bearer {r.json()['access_token']}"}

    aleatoire = random.Random(42)  # flotte reproductible : rayon d'environ 15 km autour de Lyon
    debut = time.perf_counter()
    for i in range(nb_espaces):
        (await client.post("/espaces-verts/", headers=entetes, json={
            "nom": f"Espace de charge {i + 1:03d}",
            "latitude": CENTRE_LYON[0] + aleatoire.uniform(-0.14, 0.14),
            "longitude": CENTRE_LYON[1] + aleatoire.uniform(-0.2, 0.2),
            "surface_m2": aleatoire.randint(200, 20000),
            "type_sol": aleatoire.choice(["Argileux", "Limoneux", "Sableux"]),
        })).raise_for_status()
    print(f"Création de {nb_espaces} espaces : {time.perf_counter() - debut:.1f} s")
    return entetes


async def mesurer(client: httpx.AsyncClient, entetes: dict, chemin: str, methode: str = "GET") -> dict:
    durees, erreurs = [], 0
    semaphore = asyncio.Semaphore(CONCURRENCE)

    async def une_requete():
        nonlocal erreurs
        async with semaphore:
            debut = time.perf_counter()
            r = await client.request(methode, chemin, headers=entetes)
            durees.append((time.perf_counter() - debut) * 1000)
            erreurs += r.status_code >= 400

    debut = time.perf_counter()
    await asyncio.gather(*(une_requete() for _ in range(REQUETES_PAR_ROUTE)))
    total = time.perf_counter() - debut
    return {
        "route": f"{methode} {chemin}", "p50": statistics.median(durees), "p95": percentile(durees, 95),
        "max": max(durees), "debit": REQUETES_PAR_ROUTE / total, "erreurs": erreurs,
    }


def chronometrer_job() -> float | None:
    if not os.getenv("DATABASE_URL"):
        print("DATABASE_URL absente : job horaire non chronométré.")
        return None
    from infrastructure.database import SessionLocal
    from infrastructure.jobs.mise_a_jour_capteurs import executer_mise_a_jour

    db = SessionLocal()
    try:
        debut = time.perf_counter()
        executer_mise_a_jour(db)  # vrais appels Open-Meteo (avec cache par point)
        return time.perf_counter() - debut
    finally:
        db.close()


async def main(api: str, nb_espaces: int) -> int:
    async with httpx.AsyncClient(base_url=api, timeout=30) as client:
        entetes = await preparer(client, nb_espaces)

        duree_job = chronometrer_job()
        if duree_job is not None:
            print(f"Job horaire ({nb_espaces} espaces, bilan + mesure + notifications) : {duree_job:.1f} s")

        debut = time.perf_counter()
        (await client.post("/zones/clustering/rebuild", headers=entetes)).raise_for_status()
        print(f"Recalcul des zones intelligentes : {(time.perf_counter() - debut) * 1000:.0f} ms")

        resultats = [await mesurer(client, entetes, chemin) for chemin in
                     ["/capteurs/dashboard", "/espaces-verts/", "/zones/", "/interventions/urgent", "/users/me"]]

    print(f"\n{REQUETES_PAR_ROUTE} requêtes par route, {CONCURRENCE} simultanées :")
    print(f"{'Route':32} {'p50':>8} {'p95':>8} {'max':>8} {'req/s':>7} {'erreurs':>8}")
    echec = False
    for r in resultats:
        ko = r["p95"] > SEUIL_P95_MS or r["erreurs"]
        echec |= bool(ko)
        print(f"{r['route']:32} {r['p50']:7.0f}ms {r['p95']:7.0f}ms {r['max']:7.0f}ms {r['debit']:7.1f} "
              f"{r['erreurs']:8d} {'KO' if ko else 'OK'}")
    if duree_job is not None and duree_job > SEUIL_JOB_S:
        echec = True
        print(f"Job horaire au-delà du seuil de {SEUIL_JOB_S} s : KO")
    print("\nRÉSULTAT :", "ÉCHEC" if echec else "RÉUSSITE")
    return 1 if echec else 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--api", default="http://127.0.0.1:8100/api/v1")
    parser.add_argument("--espaces", type=int, default=200)
    arguments = parser.parse_args()
    sys.exit(asyncio.run(main(arguments.api, arguments.espaces)))
