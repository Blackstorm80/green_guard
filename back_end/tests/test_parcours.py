"""Parcours de bout en bout : critère de sortie de la phase 1."""
from domain.models import BilanHydriqueJournalier, Mesure
from infrastructure.jobs.mise_a_jour_capteurs import executer_mise_a_jour
from tests.conftest import MOT_DE_PASSE, creer_compte, creer_espace

API = "/api/v1"


# --- Authentification ---------------------------------------------------------

def test_inscription_refuse_mot_de_passe_faible(client):
    r = client.post(f"{API}/auth/register", json={"name": "Bob", "email": "bob@example.com", "password": "1"})
    assert r.status_code == 422


def test_inscription_ignore_role_et_organisation_fournis(client):
    alice = creer_compte(client)
    organisation_alice = client.get(f"{API}/users/me", headers=alice).json()["organisation"]["id"]
    r = client.post(f"{API}/auth/register", json={
        "name": "Eve", "email": "eve@example.com", "password": MOT_DE_PASSE,
        "role": "lecteur", "est_superadmin": True, "organisation_id": organisation_alice,
    })
    assert r.status_code == 201
    token = client.post(f"{API}/auth/login", data={"username": "eve@example.com", "password": MOT_DE_PASSE}).json()
    me = client.get(f"{API}/users/me", headers={"Authorization": f"Bearer {token['access_token']}"}).json()
    # Toujours administrateur d'une organisation NEUVE, jamais superadmin
    assert me["role"] == "admin" and me["est_superadmin"] is False
    assert me["organisation"]["id"] != organisation_alice


def test_email_deja_utilise_message_generique(client):
    creer_compte(client)
    r = client.post(f"{API}/auth/register", json={"name": "A", "email": "alice@example.com", "password": MOT_DE_PASSE})
    assert r.status_code == 400
    assert "email" not in r.json()["detail"].lower()


def test_login_mauvais_mot_de_passe(client):
    creer_compte(client)
    r = client.post(f"{API}/auth/login", data={"username": "alice@example.com", "password": "mauvais-mot-de-passe"})
    assert r.status_code == 401


def test_compte_desactive_perd_l_acces(client, db):
    headers = creer_compte(client)
    from domain.models import User
    db.query(User).update({User.is_active: False})
    db.commit()
    assert client.get(f"{API}/users/me", headers=headers).status_code == 401


def test_routes_protegees_sans_jeton(client):
    for chemin in ["/users/me", "/espaces-verts/", "/zones/", "/capteurs/dashboard", "/catalogue/plantes",
                   "/meteo/actuelle?lat=45&lon=4", "/interventions/", "/notifications/"]:
        assert client.get(f"{API}{chemin}").status_code == 401, chemin


# --- Espaces verts -------------------------------------------------------------

def test_crud_espace_vert(client):
    headers = creer_compte(client)
    espace = creer_espace(client, headers, ph_actuel=6.5, exposition="Soleil")
    me = client.get(f"{API}/users/me", headers=headers).json()
    assert espace["organisation_id"] == me["organisation"]["id"] and espace["cree_par"] == me["id"]
    assert espace["ph_actuel"] == 6.5

    assert len(client.get(f"{API}/espaces-verts/", headers=headers).json()) == 1
    assert client.get(f"{API}/espaces-verts/{espace['id']}", headers=headers).status_code == 200

    r = client.put(f"{API}/espaces-verts/{espace['id']}", json={"nom": "Parc renommé"}, headers=headers)
    assert r.status_code == 200 and r.json()["nom"] == "Parc renommé" and r.json()["ph_actuel"] == 6.5

    assert client.delete(f"{API}/espaces-verts/{espace['id']}", headers=headers).status_code == 204
    assert client.get(f"{API}/espaces-verts/{espace['id']}", headers=headers).status_code == 404


def test_isolation_entre_utilisateurs(client):
    alice = creer_compte(client, "alice@example.com")
    bob = creer_compte(client, "bob@example.com")
    espace = creer_espace(client, alice)

    assert client.get(f"{API}/espaces-verts/", headers=bob).json() == []
    assert client.get(f"{API}/espaces-verts/{espace['id']}", headers=bob).status_code == 404
    assert client.put(f"{API}/espaces-verts/{espace['id']}", json={"nom": "x"}, headers=bob).status_code == 404
    assert client.delete(f"{API}/espaces-verts/{espace['id']}", headers=bob).status_code == 404
    dashboard = client.get(f"{API}/capteurs/dashboard?espace_ids={espace['id']}", headers=bob).json()
    assert dashboard["capteurs"] == []
    r = client.post(f"{API}/interventions/", json={"espace_id": espace["id"], "type": "arrosage"}, headers=bob)
    assert r.status_code == 404


def test_validation_coordonnees(client):
    headers = creer_compte(client)
    r = client.post(f"{API}/espaces-verts/", json={"nom": "X", "latitude": 120, "longitude": 4}, headers=headers)
    assert r.status_code == 422


# --- Dashboard, job planifié et bilan hydrique --------------------------------

def test_dashboard_sans_donnee_est_honnete(client):
    headers = creer_compte(client)
    creer_espace(client, headers)
    d = client.get(f"{API}/capteurs/dashboard", headers=headers).json()
    assert d["statut"] == "En attente"
    assert d["capteurs"][0]["statut"] == "Sans donnée"
    assert d["capteurs"][0]["temperature_c"] is None
    assert d["metrics"]["sante_globale_percent"] is None


def test_job_alimente_le_dashboard(client, db, meteo):
    headers = creer_compte(client)
    creer_espace(client, headers, reserve_utile_max=100, coefficient_cultural=1.0)
    executer_mise_a_jour(db, meteo_service=meteo)

    d = client.get(f"{API}/capteurs/dashboard", headers=headers).json()
    lecture = d["capteurs"][0]
    assert lecture["statut"] == "Optimal"
    assert lecture["reserve_eau_mm"] == 95.0          # réserve pleine (100) - ET0 (5)
    assert lecture["sante_percent"] == 95.0
    assert lecture["temperature_c"] == 22.0
    assert d["statut"] == "Sain"
    assert d["meteo_exterieure"]["temperature_c"] == 22.0


def test_job_idempotent_dans_la_journee(client, db, meteo):
    headers = creer_compte(client)
    creer_espace(client, headers)
    for _ in range(5):
        executer_mise_a_jour(db, meteo_service=meteo)

    bilans = db.query(BilanHydriqueJournalier).all()
    assert len(bilans) == 1                           # un seul bilan par espace et par jour
    assert bilans[0].reserve_utile_fin_journee == 95.0  # ET0 décomptée une seule fois
    assert db.query(Mesure).count() == 5              # une mesure par passage


def test_job_meteo_indisponible_ne_plante_pas(client, db, meteo):
    headers = creer_compte(client)
    creer_espace(client, headers)
    meteo.disponible = False
    executer_mise_a_jour(db, meteo_service=meteo)
    assert db.query(BilanHydriqueJournalier).count() == 0


def test_stress_critique_genere_une_intervention_urgente(client, db, meteo):
    headers = creer_compte(client)
    creer_espace(client, headers, reserve_utile_max=10)
    meteo.et0 = 9.0                                   # réserve 10 → 1 mm : stress 0,9
    executer_mise_a_jour(db, meteo_service=meteo)

    urgent = client.get(f"{API}/interventions/urgent", headers=headers).json()
    assert urgent["total"] == 1
    assert urgent["interventions"][0]["priorite"] == "critical"
    assert client.get(f"{API}/capteurs/dashboard", headers=headers).json()["statut"] == "Critique"


# --- Interventions, zones, météo, catalogue, santé ----------------------------

def test_crud_interventions(client):
    headers = creer_compte(client)
    espace = creer_espace(client, headers)
    r = client.post(f"{API}/interventions/", json={"espace_id": espace["id"], "type": "arrosage"}, headers=headers)
    assert r.status_code == 201
    intervention = r.json()
    assert intervention["statut"] == "planifiee"

    r = client.put(f"{API}/interventions/{intervention['id']}", json={"statut": "terminee"}, headers=headers)
    assert r.json()["statut"] == "terminee" and r.json()["realisee_le"] is not None

    assert len(client.get(f"{API}/interventions/?espace_id={espace['id']}", headers=headers).json()) == 1
    assert client.delete(f"{API}/interventions/{intervention['id']}", headers=headers).status_code == 204


def test_type_intervention_invalide(client):
    headers = creer_compte(client)
    espace = creer_espace(client, headers)
    r = client.post(f"{API}/interventions/", json={"espace_id": espace["id"], "type": "piratage"}, headers=headers)
    assert r.status_code == 422


def test_zones_intelligentes(client):
    headers = creer_compte(client)
    for i, (lat, lon) in enumerate([(45.76, 4.83), (45.761, 4.831), (48.85, 2.35), (48.851, 2.351)]):
        creer_espace(client, headers, nom=f"E{i}", latitude=lat, longitude=lon)
    assert client.post(f"{API}/zones/clustering/rebuild", headers=headers).status_code == 201

    zones = client.get(f"{API}/zones/", headers=headers).json()
    assert 1 <= len(zones) <= 4
    assert sum(z["nb_espaces"] for z in zones) == 4
    for z in zones:   # centroïdes en vraies coordonnées (Lyon ou Paris), pas en valeurs normalisées
        assert 45 < z["centroid_lat"] < 49 and 2 < z["centroid_lon"] < 5
    espaces = client.get(f"{API}/espaces-verts/", headers=headers).json()
    assert all(e["zone_id"] is not None for e in espaces)


def test_meteo(client, meteo):
    headers = creer_compte(client)
    assert client.get(f"{API}/meteo/actuelle?lat=45.7&lon=4.8", headers=headers).json()["temperature_c"] == 22.0
    assert client.get(f"{API}/meteo/Lyon", headers=headers).status_code == 200
    meteo.disponible = False
    r = client.get(f"{API}/meteo/Lyon", headers=headers)
    assert r.status_code == 502 and "indisponible" in r.json()["detail"]


def test_catalogue_et_notifications(client):
    headers = creer_compte(client)
    assert client.get(f"{API}/catalogue/plantes", headers=headers).json() == []
    assert client.get(f"{API}/catalogue/auxiliaires", headers=headers).json() == []
    assert client.get(f"{API}/notifications/", headers=headers).json() == []
    assert client.get(f"{API}/users/me/notifications", headers=headers).json() == []


def test_sondes_de_sante(client):
    assert client.get(f"{API}/health/live").json() == {"status": "ok"}
    assert client.get(f"{API}/health/ready").json() == {"status": "ok"}


def test_diagnostic_espace(client, db, meteo):
    headers = creer_compte(client)
    espace = creer_espace(client, headers)
    r = client.post(f"{API}/health/diagnostic", json={"espace_id": espace["id"]}, headers=headers)
    assert r.json()["statut"] == "Sans donnée"
    executer_mise_a_jour(db, meteo_service=meteo)
    r = client.post(f"{API}/health/diagnostic", json={"espace_id": espace["id"]}, headers=headers)
    assert r.json()["statut"] == "Optimal"


def test_stress_critique_notifie_le_proprietaire_une_fois_par_jour(client, db, meteo):
    headers = creer_compte(client)
    creer_espace(client, headers, nom="Square sec", reserve_utile_max=10)
    meteo.et0 = 9.0
    for _ in range(3):
        executer_mise_a_jour(db, meteo_service=meteo)

    notifications = client.get(f"{API}/notifications/", headers=headers).json()
    assert len(notifications) == 1
    assert "Square sec" in notifications[0]["message"] and notifications[0]["is_read"] is False
