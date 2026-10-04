"""Multi-organisations : cloisonnement entre collectivités, rôles fins, patrimoine partagé, gestion."""
import pytest

from create_user import create_user
from domain.logic.droits import DernierAdministrateurError, permissions_du_role, verifier_admin_restant
from domain.logic.organisations import generer_slug, nom_organisation_par_defaut, slug_disponible
from domain.models import Notification, Organisation, User
from infrastructure.jobs.mise_a_jour_capteurs import executer_mise_a_jour
from tests.conftest import MOT_DE_PASSE, ajouter_membre, connecter, creer_compte, creer_espace

API = "/api/v1"


def moi(client, headers) -> dict:
    return client.get(f"{API}/users/me", headers=headers).json()


@pytest.fixture
def deux_organisations(client, db, meteo):
    """Ville A (admin Alice) et ville B (admin Bob), chacune avec un espace, une intervention et des mesures."""
    alice = creer_compte(client, "alice@example.com", organisation="Ville A")
    bob = creer_compte(client, "bob@example.com", organisation="Ville B")
    espace_a = creer_espace(client, alice, nom="Parc A", reserve_utile_max=10, coefficient_cultural=1.0)
    espace_b = creer_espace(client, bob, nom="Parc B", latitude=48.85, longitude=2.35)
    intervention_b = client.post(f"{API}/interventions/", json={"espace_id": espace_b["id"], "type": "arrosage"},
                                 headers=bob).json()
    meteo.et0 = 9.0                       # Parc A (RU 10) devient critique ; Parc B (RU 100) reste optimal
    executer_mise_a_jour(db, meteo_service=meteo)
    return {"alice": alice, "bob": bob, "espace_a": espace_a, "espace_b": espace_b, "intervention_b": intervention_b}


# --- Logique pure ---------------------------------------------------------------

def test_slug_lisible_et_unique():
    assert generer_slug("Ville de Saint-Étienne") == "ville-de-saint-etienne"
    assert generer_slug("  !!! ") == "organisation"
    assert len(generer_slug("x" * 200)) == 60
    pris = {"lyon", "lyon-2"}
    assert slug_disponible("lyon", pris.__contains__) == "lyon-3"
    assert slug_disponible("paris", pris.__contains__) == "paris"
    assert nom_organisation_par_defaut(" Alice ") == "Organisation de Alice"


def test_permissions_par_role():
    assert permissions_du_role("admin") == ["interventions", "gestion", "membres", "registre"]
    assert permissions_du_role("gestionnaire") == ["interventions", "gestion", "registre"]
    assert permissions_du_role("technicien") == ["interventions"]
    assert permissions_du_role("lecteur") == ["registre"]


def test_dernier_admin_protege():
    with pytest.raises(DernierAdministrateurError):
        verifier_admin_restant("admin", True, "gestionnaire", True, admins_actifs=1)
    with pytest.raises(DernierAdministrateurError):
        verifier_admin_restant("admin", True, "admin", False, admins_actifs=1)
    verifier_admin_restant("admin", True, "gestionnaire", True, admins_actifs=2)
    verifier_admin_restant("admin", False, "lecteur", False, admins_actifs=1)   # déjà inactif
    verifier_admin_restant("technicien", True, "lecteur", True, admins_actifs=1)


# --- Inscription et profil ----------------------------------------------------

def test_inscription_cree_une_organisation_dont_on_est_admin(client):
    alice = creer_compte(client, "alice@example.com")
    profil = moi(client, alice)
    assert profil["role"] == "admin" and profil["est_superadmin"] is False
    assert profil["organisation"]["nom"] == "Organisation de Alice"
    assert profil["permissions"] == ["interventions", "gestion", "membres", "registre"]
    organisation = client.get(f"{API}/organisations/moi", headers=alice).json()
    assert organisation["slug"] == "organisation-de-alice"

    bob = creer_compte(client, "bob@example.com", organisation="Ville de Lyon")
    carole = creer_compte(client, "carole@example.com", organisation="Ville de Lyon")
    slugs = {client.get(f"{API}/organisations/moi", headers=h).json()["slug"] for h in (bob, carole)}
    assert slugs == {"ville-de-lyon", "ville-de-lyon-2"}          # même nom, organisations distinctes
    assert moi(client, bob)["organisation"]["id"] != moi(client, carole)["organisation"]["id"]


def test_inscription_nom_d_organisation_borne(client):
    r = client.post(f"{API}/auth/register", json={"name": "A", "email": "a@example.com", "password": MOT_DE_PASSE,
                                                  "organisation": "x" * 121})
    assert r.status_code == 422


# --- Cloisonnement entre organisations ---------------------------------------------------

def test_isolation_des_espaces(client, deux_organisations):
    alice, espace_b = deux_organisations["alice"], deux_organisations["espace_b"]
    assert [e["nom"] for e in client.get(f"{API}/espaces-verts/", headers=alice).json()] == ["Parc A"]
    assert client.get(f"{API}/espaces-verts/{espace_b['id']}", headers=alice).status_code == 404
    assert client.put(f"{API}/espaces-verts/{espace_b['id']}", json={"nom": "x"}, headers=alice).status_code == 404
    assert client.delete(f"{API}/espaces-verts/{espace_b['id']}", headers=alice).status_code == 404


def test_isolation_des_interventions(client, deux_organisations):
    alice, espace_b = deux_organisations["alice"], deux_organisations["espace_b"]
    intervention_b = deux_organisations["intervention_b"]
    assert client.get(f"{API}/interventions/", headers=alice).json() == []
    assert client.get(f"{API}/interventions/?espace_id={espace_b['id']}", headers=alice).json() == []
    chemin = f"{API}/interventions/{intervention_b['id']}"
    assert client.get(chemin, headers=alice).status_code == 404
    assert client.put(chemin, json={"statut": "terminee"}, headers=alice).status_code == 404
    assert client.delete(chemin, headers=alice).status_code == 404
    r = client.post(f"{API}/interventions/", json={"espace_id": espace_b["id"], "type": "taille"}, headers=alice)
    assert r.status_code == 404
    urgentes = client.get(f"{API}/interventions/urgent", headers=alice).json()["interventions"]
    assert {u["espace_nom"] for u in urgentes} == {"Parc A"}
    assert client.get(f"{API}/interventions/urgent", headers=deux_organisations["bob"]).json()["total"] == 0


def test_isolation_des_capteurs_et_du_diagnostic(client, deux_organisations):
    alice, bob = deux_organisations["alice"], deux_organisations["bob"]
    espace_a, espace_b = deux_organisations["espace_a"], deux_organisations["espace_b"]
    dashboard = client.get(f"{API}/capteurs/dashboard", headers=alice).json()
    assert [c["nom"] for c in dashboard["capteurs"]] == ["Parc A"] and dashboard["statut"] == "Critique"
    filtre = client.get(f"{API}/capteurs/dashboard?espace_ids={espace_b['id']}", headers=alice).json()
    assert filtre["capteurs"] == []
    assert client.get(f"{API}/capteurs/dashboard", headers=bob).json()["statut"] == "Sain"

    assert client.post(f"{API}/health/diagnostic", json={"espace_id": espace_b["id"]}, headers=alice).status_code == 404
    r = client.post(f"{API}/health/diagnostic", json={"espace_id": espace_a["id"]}, headers=alice)
    assert r.json()["statut"] == "Critique"


def test_isolation_des_zones(client, deux_organisations):
    alice, bob = deux_organisations["alice"], deux_organisations["bob"]
    assert client.post(f"{API}/zones/clustering/rebuild", headers=bob).status_code == 201
    assert client.get(f"{API}/zones/", headers=alice).json() == []
    assert client.post(f"{API}/zones/clustering/rebuild", headers=alice).status_code == 201
    zones_b = client.get(f"{API}/zones/", headers=bob).json()
    assert len(zones_b) == 1 and zones_b[0]["nb_espaces"] == 1      # le recalcul d'Alice n'a pas touché B
    assert sum(z["nb_espaces"] for z in client.get(f"{API}/zones/", headers=alice).json()) == 1


def test_isolation_des_indicateurs_vegetaux(client, deux_organisations):
    alice, bob = deux_organisations["alice"], deux_organisations["bob"]
    etat_a = client.get(f"{API}/vegetal/etat-global", headers=alice).json()
    assert etat_a["total_espaces"] == 1 and etat_a["espaces_critique"] == 1
    etat_b = client.get(f"{API}/vegetal/etat-global", headers=bob).json()
    assert etat_b["total_espaces"] == 1 and etat_b["espaces_critique"] == 0
    impact = client.get(f"{API}/vegetal/impact-carbone", headers=bob).json()
    assert len(impact["detail_par_zone"]) == 1


def test_isolation_des_notifications(client, db, deux_organisations):
    alice, bob = deux_organisations["alice"], deux_organisations["bob"]
    notifications_alice = client.get(f"{API}/notifications/", headers=alice).json()
    assert len(notifications_alice) == 1 and "Parc A" in notifications_alice[0]["message"]
    assert client.get(f"{API}/notifications/", headers=bob).json() == []
    assert client.get(f"{API}/users/me/notifications", headers=bob).json() == []
    r = client.post(f"{API}/notifications/{notifications_alice[0]['id']}/mark-as-read", headers=bob)
    assert r.status_code == 404


def test_isolation_des_membres(client, db, deux_organisations):
    alice, bob = deux_organisations["alice"], deux_organisations["bob"]
    membres = client.get(f"{API}/organisations/moi/membres", headers=alice).json()
    assert [m["email"] for m in membres] == ["alice@example.com"]
    id_bob = moi(client, bob)["id"]
    r = client.put(f"{API}/organisations/moi/membres/{id_bob}", json={"role": "lecteur"}, headers=alice)
    assert r.status_code == 404
    assert moi(client, bob)["role"] == "admin"


# --- Patrimoine partagé au sein d'une organisation --------------------------------------

def test_patrimoine_partage_entre_membres(client, db, meteo):
    alice = creer_compte(client, "alice@example.com", organisation="Ville A")
    gaston = ajouter_membre(client, db, alice, "gaston@example.com", "gestionnaire")
    espace = creer_espace(client, alice, nom="Parc commun")
    assert [e["id"] for e in client.get(f"{API}/espaces-verts/", headers=gaston).json()] == [espace["id"]]

    r = client.put(f"{API}/espaces-verts/{espace['id']}", json={"nom": "Parc renommé"}, headers=gaston)
    assert r.status_code == 200 and r.json()["cree_par"] == moi(client, alice)["id"]
    intervention = client.post(f"{API}/interventions/", json={"espace_id": espace["id"], "type": "taille"},
                               headers=gaston).json()
    assert [i["id"] for i in client.get(f"{API}/interventions/", headers=alice).json()] == [intervention["id"]]

    assert client.post(f"{API}/zones/clustering/rebuild", headers=gaston).status_code == 201
    assert len(client.get(f"{API}/zones/", headers=alice).json()) == 1


def test_espace_conserve_apres_depart_du_createur(client, db):
    alice = creer_compte(client, "alice@example.com")
    gaston = ajouter_membre(client, db, alice, "gaston@example.com", "gestionnaire")
    espace = creer_espace(client, gaston)
    db.query(User).filter(User.email == "gaston@example.com").delete()
    db.commit()
    restant = client.get(f"{API}/espaces-verts/{espace['id']}", headers=alice).json()
    assert restant["cree_par"] is None                                # historique effacé, espace conservé


def test_alerte_critique_envoyee_aux_membres_qui_interviennent(client, db, meteo):
    alice = creer_compte(client, "alice@example.com")
    tech = ajouter_membre(client, db, alice, "tech@example.com", "technicien")
    elu = ajouter_membre(client, db, alice, "elu@example.com", "lecteur")
    creer_espace(client, alice, nom="Square sec", reserve_utile_max=10, coefficient_cultural=1.0)
    meteo.et0 = 9.0
    for _ in range(2):
        executer_mise_a_jour(db, meteo_service=meteo)
    assert len(client.get(f"{API}/notifications/", headers=alice).json()) == 1
    assert len(client.get(f"{API}/notifications/", headers=tech).json()) == 1
    assert client.get(f"{API}/notifications/", headers=elu).json() == []
    assert db.query(Notification).count() == 2


# --- Droits par rôle -----------------------------------------------------------------------

def test_lecteur_consulte_sans_rien_ecrire(client, db, meteo):
    alice = creer_compte(client, "alice@example.com")
    elu = ajouter_membre(client, db, alice, "elu@example.com", "lecteur")
    espace = creer_espace(client, alice)
    intervention = client.post(f"{API}/interventions/", json={"espace_id": espace["id"], "type": "arrosage"},
                               headers=alice).json()

    for chemin in ["/espaces-verts/", f"/espaces-verts/{espace['id']}", "/zones/", "/capteurs/dashboard",
                   "/interventions/", f"/interventions/{intervention['id']}", "/interventions/urgent",
                   "/organisations/moi", "/organisations/moi/membres", "/catalogue/plantes"]:
        assert client.get(f"{API}{chemin}", headers=elu).status_code == 200, chemin
    assert client.post(f"{API}/health/diagnostic", json={"espace_id": espace["id"]}, headers=elu).status_code == 200

    ecritures = [
        ("post", "/espaces-verts/", {"nom": "X", "latitude": 45.0, "longitude": 4.0}),
        ("put", f"/espaces-verts/{espace['id']}", {"nom": "X"}),
        ("delete", f"/espaces-verts/{espace['id']}", None),
        ("post", "/zones/clustering/rebuild", None),
        ("post", "/interventions/", {"espace_id": espace["id"], "type": "taille"}),
        ("put", f"/interventions/{intervention['id']}", {"statut": "terminee"}),
        ("delete", f"/interventions/{intervention['id']}", None),
        ("put", "/organisations/moi", {"parametres": {"seuil": 1}}),
        ("put", f"/organisations/moi/membres/{moi(client, alice)['id']}", {"role": "lecteur"}),
        ("post", "/organisations/", {"nom": "X", "admin": {"name": "X", "email": "x@example.com",
                                                          "password": MOT_DE_PASSE}}),
    ]
    for methode, chemin, corps in ecritures:
        r = client.request(methode.upper(), f"{API}{chemin}", json=corps, headers=elu)
        assert r.status_code == 403, (methode, chemin, r.status_code)
    for chemin in ["/vegetal/etat-global", "/vegetal/impact-carbone"]:
        assert client.get(f"{API}{chemin}", headers=elu).status_code == 403
    assert moi(client, elu)["permissions"] == ["registre"]   # registre sécheresse : consultation


def test_technicien_intervient_sans_gerer_le_patrimoine(client, db):
    alice = creer_compte(client, "alice@example.com")
    tech = ajouter_membre(client, db, alice, "tech@example.com", "technicien")
    espace = creer_espace(client, alice)

    r = client.post(f"{API}/interventions/", json={"espace_id": espace["id"], "type": "arrosage"}, headers=tech)
    assert r.status_code == 201
    intervention = r.json()
    assert intervention["cree_par"] == moi(client, tech)["id"]
    r = client.put(f"{API}/interventions/{intervention['id']}", json={"statut": "terminee"}, headers=tech)
    assert r.status_code == 200 and r.json()["realisee_le"] is not None
    assert client.delete(f"{API}/interventions/{intervention['id']}", headers=tech).status_code == 403

    assert client.post(f"{API}/espaces-verts/", json={"nom": "X", "latitude": 45.0, "longitude": 4.0},
                       headers=tech).status_code == 403
    assert client.put(f"{API}/espaces-verts/{espace['id']}", json={"nom": "X"}, headers=tech).status_code == 403
    assert client.post(f"{API}/zones/clustering/rebuild", headers=tech).status_code == 403
    assert client.get(f"{API}/vegetal/etat-global", headers=tech).status_code == 403
    assert client.put(f"{API}/organisations/moi", json={"parametres": {}}, headers=tech).status_code == 403


def test_gestionnaire_gere_le_patrimoine_mais_pas_les_membres(client, db):
    alice = creer_compte(client, "alice@example.com", organisation="Ville A")
    gaston = ajouter_membre(client, db, alice, "gaston@example.com", "gestionnaire")
    espace = creer_espace(client, gaston)
    intervention = client.post(f"{API}/interventions/", json={"espace_id": espace["id"], "type": "taille"},
                               headers=gaston).json()
    assert client.delete(f"{API}/interventions/{intervention['id']}", headers=gaston).status_code == 204
    assert client.get(f"{API}/vegetal/etat-global", headers=gaston).status_code == 200

    r = client.put(f"{API}/organisations/moi", json={"parametres": {"seuil_critique": 0.6}}, headers=gaston)
    assert r.status_code == 200 and r.json()["parametres"] == {"seuil_critique": 0.6}
    assert client.put(f"{API}/organisations/moi", json={"nom": "Autre nom"}, headers=gaston).status_code == 403
    id_alice = moi(client, alice)["id"]
    r = client.put(f"{API}/organisations/moi/membres/{id_alice}", json={"role": "lecteur"}, headers=gaston)
    assert r.status_code == 403
    assert client.delete(f"{API}/espaces-verts/{espace['id']}", headers=gaston).status_code == 204


def test_role_relu_en_base_a_chaque_requete(client, db):
    alice = creer_compte(client, "alice@example.com")
    assert client.post(f"{API}/espaces-verts/", json={"nom": "X", "latitude": 45.0, "longitude": 4.0},
                       headers=alice).status_code == 201
    db.query(User).update({User.role: "lecteur"})
    db.commit()
    # Même jeton : le nouveau rôle s'applique immédiatement
    assert client.post(f"{API}/espaces-verts/", json={"nom": "Y", "latitude": 45.0, "longitude": 4.0},
                       headers=alice).status_code == 403


# --- Gestion de l'organisation et des membres --------------------------------------------

def test_admin_renomme_et_parametre_son_organisation(client):
    alice = creer_compte(client, "alice@example.com")
    r = client.put(f"{API}/organisations/moi", json={"nom": "Ville de Lyon", "parametres": {"ru": 80}},
                   headers=alice)
    assert r.status_code == 200 and r.json()["nom"] == "Ville de Lyon" and r.json()["parametres"] == {"ru": 80}
    assert moi(client, alice)["organisation"]["nom"] == "Ville de Lyon"
    assert client.put(f"{API}/organisations/moi", json={"nom": ""}, headers=alice).status_code == 422
    trop = {"cle": "x" * 10_001}
    assert client.put(f"{API}/organisations/moi", json={"parametres": trop}, headers=alice).status_code == 422


def test_admin_change_le_role_et_desactive_un_membre(client, db):
    alice = creer_compte(client, "alice@example.com")
    tech = ajouter_membre(client, db, alice, "tech@example.com", "technicien")
    id_tech = moi(client, tech)["id"]

    r = client.put(f"{API}/organisations/moi/membres/{id_tech}", json={"role": "gestionnaire"}, headers=alice)
    assert r.status_code == 200 and r.json()["role"] == "gestionnaire"
    assert moi(client, tech)["permissions"] == ["interventions", "gestion", "registre"]
    r = client.put(f"{API}/organisations/moi/membres/{id_tech}", json={"role": "superadmin"}, headers=alice)
    assert r.status_code == 422

    r = client.put(f"{API}/organisations/moi/membres/{id_tech}", json={"is_active": False}, headers=alice)
    assert r.status_code == 200 and r.json()["is_active"] is False
    assert client.get(f"{API}/users/me", headers=tech).status_code == 401     # accès perdu immédiatement
    assert client.put(f"{API}/organisations/moi/membres/999999", json={"role": "lecteur"},
                      headers=alice).status_code == 404


def test_le_dernier_admin_ne_peut_pas_se_retirer(client, db):
    alice = creer_compte(client, "alice@example.com")
    id_alice = moi(client, alice)["id"]
    for corps in ({"role": "gestionnaire"}, {"is_active": False}):
        r = client.put(f"{API}/organisations/moi/membres/{id_alice}", json=corps, headers=alice)
        assert r.status_code == 409, corps
    assert moi(client, alice)["role"] == "admin"

    second = ajouter_membre(client, db, alice, "second@example.com", "admin")
    r = client.put(f"{API}/organisations/moi/membres/{id_alice}", json={"role": "gestionnaire"}, headers=alice)
    assert r.status_code == 200
    # Le second admin est désormais le dernier : il ne peut pas non plus se rétrograder
    id_second = moi(client, second)["id"]
    r = client.put(f"{API}/organisations/moi/membres/{id_second}", json={"role": "lecteur"}, headers=second)
    assert r.status_code == 409


# --- Superadmin et script d'administration ---------------------------------------------

def test_superadmin_cree_une_organisation_et_son_admin(client, db):
    alice = creer_compte(client, "alice@example.com")
    corps = {"nom": "Métropole", "slug": "metropole",
             "admin": {"name": "Marc", "email": "marc@example.com", "password": MOT_DE_PASSE}}
    assert client.post(f"{API}/organisations/", json=corps, headers=alice).status_code == 403

    db.query(User).filter(User.email == "alice@example.com").update({User.est_superadmin: True})
    db.commit()
    r = client.post(f"{API}/organisations/", json=corps, headers=alice)
    assert r.status_code == 201 and r.json()["slug"] == "metropole" and r.json()["nom"] == "Métropole"

    marc = connecter(client, "marc@example.com")
    profil = moi(client, marc)
    assert profil["role"] == "admin" and profil["organisation"]["nom"] == "Métropole"
    creer_espace(client, alice, nom="Parc d'Alice")
    assert client.get(f"{API}/espaces-verts/", headers=marc).json() == []     # le superadmin ne partage rien

    doublon = {**corps, "admin": {**corps["admin"], "email": "autre@example.com"}}
    assert client.post(f"{API}/organisations/", json=doublon, headers=alice).status_code == 409
    email_pris = {**corps, "slug": "metropole-2"}
    assert client.post(f"{API}/organisations/", json=email_pris, headers=alice).status_code == 409
    assert db.query(Organisation).filter(Organisation.slug == "metropole-2").count() == 0   # rien de créé
    invalide = {**corps, "slug": "Pas Un Slug"}
    assert client.post(f"{API}/organisations/", json=invalide, headers=alice).status_code == 422


def test_superadmin_slug_genere_si_absent(client, db):
    alice = creer_compte(client, "alice@example.com")
    db.query(User).update({User.est_superadmin: True})
    db.commit()
    r = client.post(f"{API}/organisations/", headers=alice, json={
        "nom": "Ville de Saint-Étienne", "admin": {"name": "S", "email": "s@example.com", "password": MOT_DE_PASSE}})
    assert r.status_code == 201 and r.json()["slug"] == "ville-de-saint-etienne"


def test_script_create_user(client, db):
    utilisateur = create_user("chef@example.com", MOT_DE_PASSE, name="Chef", organisation="ville-de-lyon",
                              nom_organisation="Ville de Lyon", role="gestionnaire", db=db)
    assert utilisateur.role == "gestionnaire" and utilisateur.est_superadmin is False
    assert create_user("chef@example.com", MOT_DE_PASSE, db=db) is None             # e-mail déjà pris
    create_user("tech@example.com", MOT_DE_PASSE, organisation="ville-de-lyon", role="technicien", db=db)
    create_user("root@example.com", MOT_DE_PASSE, superadmin=True, db=db)           # organisation par défaut

    lyon = db.query(Organisation).filter(Organisation.slug == "ville-de-lyon").one()
    assert lyon.nom == "Ville de Lyon" and len(lyon.membres) == 2
    racine = db.query(User).filter(User.email == "root@example.com").one()
    assert racine.est_superadmin and racine.role == "admin"
    assert racine.organisation.slug == "defaut" and racine.organisation.nom == "Organisation par défaut"
    with pytest.raises(ValueError, match="Rôle inconnu"):
        create_user("x@example.com", MOT_DE_PASSE, role="manager", db=db)
    assert moi(client, connecter(client, "tech@example.com"))["organisation"]["nom"] == "Ville de Lyon"
