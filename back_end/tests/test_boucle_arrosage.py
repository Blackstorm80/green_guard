"""Boucle arrosage → bilan : apport compté à la fin d'un arrosage, recalcul immédiat, dose recommandée."""
from datetime import UTC, datetime, time, timedelta

import pytest

from config import settings
from domain.logic.arrosage import (
    ArrosageNonComptableError,
    DoseRecommandee,
    SurfaceInconnueError,
    dose_recommandee,
    efficacite_irrigation,
    formuler_dose,
    horodatage_arrosage,
    quantite_apportee_mm,
)
from domain.logic.fao56 import VERSION_MODELE
from domain.models import ActionIrrigation, BilanHydriqueJournalier
from infrastructure.jobs.mise_a_jour_capteurs import executer_mise_a_jour
from tests.conftest import ajouter_membre, creer_compte, creer_espace

API = "/api/v1"
TAW, RAW = 46.5, 23.25          # limon, square (Zr 0,3 m)
SURFACE = 100


# --- Domaine : conversion et dose -------------------------------------------------------

@pytest.mark.parametrize("libelle, efficacite", [
    ("Goutte-à-goutte", 0.9), ("GOUTTE A GOUTTE", 0.9), ("goutte_a_goutte", 0.9), ("Aspersion", 0.75),
    ("Manuel", 0.7), ("tuyau", 0.7), ("Aucune", 0.75), (None, 0.75), ("", 0.75),
])
def test_efficacite_par_type_d_irrigation(libelle, efficacite):
    assert efficacite_irrigation(libelle) == efficacite


def test_quantite_apportee_un_litre_par_metre_carre_vaut_un_mm():
    assert quantite_apportee_mm(5000, 1000) == 5.0
    assert quantite_apportee_mm(150, 12.5) == 12.0
    for surface in (None, 0, -3):
        with pytest.raises(SurfaceInconnueError, match="Surface de l'espace inconnue"):
            quantite_apportee_mm(100, surface)


def test_horodatage_de_l_arrosage():
    maintenant = datetime(2026, 7, 14, 10, 0, tzinfo=UTC)
    assert horodatage_arrosage(datetime(2026, 7, 14, 9, 0), maintenant) == datetime(2026, 7, 14, 9, 0, tzinfo=UTC)
    paris = datetime.fromisoformat("2026-07-14T11:30:00+02:00")
    assert horodatage_arrosage(paris, maintenant) == datetime(2026, 7, 14, 9, 30, tzinfo=UTC)
    assert horodatage_arrosage(maintenant + timedelta(minutes=4), maintenant)   # décalage d'horloge toléré
    with pytest.raises(ArrosageNonComptableError, match="futur"):
        horodatage_arrosage(maintenant + timedelta(hours=1), maintenant)


@pytest.mark.parametrize("epuisement, taw, surface, irrigation, debit, attendu", [
    # 30 mm sur 1 000 m² en aspersion : 30 000 L / 0,75
    (30, TAW, 1000, "Aspersion", None, DoseRecommandee(30.0, 40000.0, None)),
    # goutte-à-goutte : 18 mm × 100 m² / 0,9 = 2 000 L, à 20 L/min = 100 min
    (18, TAW, 100, "Goutte-à-goutte", 20, DoseRecommandee(18.0, 2000.0, 100.0)),
    # tuyau : 7 mm × 10 m² / 0,7 = 100 L
    (7, 50, 10, "Manuel", None, DoseRecommandee(7.0, 100.0, None)),
    # efficacité par défaut 0,75 ; minutes arrondies à la minute supérieure (1 000 / 30 = 33,3)
    (7.5, 50, 100, None, 30, DoseRecommandee(7.5, 1000.0, 34.0)),
    # épuisement supérieur à la TAW : plafonné à la TAW
    (80, TAW, 10, "Manuel", None, DoseRecommandee(46.5, 664.0, None)),
    # réserve pleine : rien à apporter
    (0, TAW, 100, "Aspersion", 10, DoseRecommandee(0.0, 0.0, 0.0)),
    # surface inconnue : ni litres ni minutes, même avec un débit
    (12.34, TAW, None, "Aspersion", 10, DoseRecommandee(12.3, None, None)),
    (12, TAW, 0, None, None, DoseRecommandee(12.0, None, None)),
])
def test_dose_recommandee(epuisement, taw, surface, irrigation, debit, attendu):
    assert dose_recommandee(epuisement, taw, surface, irrigation, debit) == attendu


def test_conseil_chiffre():
    assert formuler_dose(DoseRecommandee(30.0, 40000.0, 400.0)) == (
        "Pour remplir la réserve : 30 mm, soit 40 000 L (400 min au débit de l'arrosage).")
    assert formuler_dose(DoseRecommandee(12.5, 1667.0, None)) == "Pour remplir la réserve : 12,5 mm, soit 1 667 L."
    assert formuler_dose(DoseRecommandee(12.5, None, None)) == "Pour remplir la réserve : 12,5 mm."
    assert formuler_dose(DoseRecommandee(0.0, 0.0, None)) is None
    assert formuler_dose(None) is None


# --- API : un arrosage terminé remonte la réserve ---------------------------------------

def aujourd_hui():
    return datetime.now(settings.fuseau).date()


def espace_critique(client, db, meteo, headers, **champs) -> dict:
    """Square sur limon (TAW 46,5 mm) dont la réserve est épuisée à 40 mm la veille : Critique aujourd'hui."""
    espace = creer_espace(client, headers, type_espace="Square", type_sol="Limoneux", surface_m2=SURFACE, **champs)
    db.add(BilanHydriqueJournalier(
        espace_id=espace["id"], date=aujourd_hui() - timedelta(days=1), reserve_utile_fin_journee=TAW - 40,
        indice_stress=40 / TAW, statut_hydrique="Critique", epuisement_debut_mm=38, epuisement_fin_mm=40,
        et0_mm=5, etc_mm=2, pluie_mm=0, pluie_efficace_mm=0, arrosage_mm=0, drainage_mm=0, taw_mm=TAW, raw_mm=RAW,
        version_modele=VERSION_MODELE,
    ))
    db.commit()
    executer_mise_a_jour(db, meteo_service=meteo)
    return espace


def epuisement_du_jour(arrosage_mm: float, debut: float = 40.0) -> float:
    """Dr de fin de journée attendu avec ET0 5 mm et KL 0,8 (Ks évalué sur Dr de début)."""
    ks = 1.0 if debut <= RAW else (TAW - debut) / (TAW - RAW)
    return min(TAW, max(0.0, debut - arrosage_mm + 5 * 0.8 * ks))


def lecture(client, headers, espace_id: int) -> dict:
    capteurs = client.get(f"{API}/capteurs/dashboard", headers=headers).json()["capteurs"]
    return next(c for c in capteurs if c["espace_id"] == espace_id)


def bilan_du_jour(db, espace_id: int) -> BilanHydriqueJournalier:
    db.expire_all()
    return db.query(BilanHydriqueJournalier).filter_by(espace_id=espace_id, date=aujourd_hui()).one()


def actions(db, espace_id: int | None = None) -> list[ActionIrrigation]:
    db.expire_all()
    requete = db.query(ActionIrrigation)
    if espace_id is not None:
        requete = requete.filter_by(espace_id=espace_id)
    return requete.all()


def arroser(client, headers, espace_id: int, volume: float | None, **champs):
    return client.post(f"{API}/interventions/", headers=headers, json={
        "espace_id": espace_id, "type": "arrosage", "volume_eau_l": volume, **champs})


def test_arrosage_termine_remonte_la_reserve_immediatement(client, db, meteo):
    headers = creer_compte(client)
    espace = espace_critique(client, db, meteo, headers)
    avant = lecture(client, headers, espace["id"])
    assert avant["statut"] == "Critique"
    assert avant["reserve_eau_mm"] == round(TAW - epuisement_du_jour(0), 1)

    r = arroser(client, headers, espace["id"], 3000, statut="terminee")     # 3 000 L sur 100 m² = 30 mm
    assert r.status_code == 201, r.text
    assert r.json()["arrosage_compte_mm"] == 30.0 and r.json()["realisee_le"] is not None

    apres = lecture(client, headers, espace["id"])
    assert apres["statut"] == "Optimal"
    assert apres["reserve_eau_mm"] == round(TAW - epuisement_du_jour(30), 1)
    bilan = bilan_du_jour(db, espace["id"])
    assert bilan.arrosage_mm == 30.0 and bilan.epuisement_debut_mm == pytest.approx(40)
    [action] = actions(db, espace["id"])
    assert (action.intervention_id, action.quantite_mm) == (r.json()["id"], 30.0)

    # Le passage horaire suivant ne compte pas l'arrosage une seconde fois
    executer_mise_a_jour(db, meteo_service=meteo)
    assert bilan_du_jour(db, espace["id"]).arrosage_mm == 30.0


def test_terminer_avec_le_volume_reel_puis_sans_double_comptage(client, db, meteo):
    headers = creer_compte(client)
    espace = espace_critique(client, db, meteo, headers)
    planifiee = arroser(client, headers, espace["id"], 1500).json()
    assert planifiee["statut"] == "planifiee" and planifiee["arrosage_compte_mm"] is None
    assert actions(db) == [] and bilan_du_jour(db, espace["id"]).arrosage_mm == 0

    url = f"{API}/interventions/{planifiee['id']}"
    r = client.put(url, json={"statut": "terminee", "volume_eau_l": 2000}, headers=headers)
    assert r.status_code == 200 and r.json()["arrosage_compte_mm"] == 20.0
    for _ in range(2):                                                         # retermine : rien de plus
        assert client.put(url, json={"statut": "terminee"}, headers=headers).status_code == 200
    assert len(actions(db)) == 1 and bilan_du_jour(db, espace["id"]).arrosage_mm == 20.0

    # Volume corrigé après coup : l'apport est remplacé, pas ajouté
    assert client.put(url, json={"volume_eau_l": 2500}, headers=headers).json()["arrosage_compte_mm"] == 25.0
    assert [a.quantite_mm for a in actions(db)] == [25.0]
    assert bilan_du_jour(db, espace["id"]).arrosage_mm == 25.0
    # Volume remis à zéro : plus rien de compté
    assert client.put(url, json={"volume_eau_l": 0}, headers=headers).json()["arrosage_compte_mm"] is None
    assert actions(db) == [] and bilan_du_jour(db, espace["id"]).arrosage_mm == 0


def test_annuler_un_arrosage_termine_retire_l_apport(client, db, meteo):
    headers = creer_compte(client)
    espace = espace_critique(client, db, meteo, headers)
    intervention = arroser(client, headers, espace["id"], 3000, statut="terminee").json()
    url = f"{API}/interventions/{intervention['id']}"

    r = client.put(url, json={"statut": "planifiee"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["realisee_le"] is None and r.json()["arrosage_compte_mm"] is None
    assert actions(db) == []
    assert lecture(client, headers, espace["id"])["statut"] == "Critique"

    # Un arrosage devenu « taille » n'apporte pas d'eau non plus
    client.put(url, json={"statut": "terminee"}, headers=headers)
    assert len(actions(db)) == 1
    client.put(url, json={"type": "taille"}, headers=headers)
    assert actions(db) == [] and bilan_du_jour(db, espace["id"]).arrosage_mm == 0


def test_supprimer_l_intervention_retire_l_apport_et_recalcule(client, db, meteo):
    headers = creer_compte(client)
    espace = espace_critique(client, db, meteo, headers)
    intervention = arroser(client, headers, espace["id"], 3000, statut="terminee").json()
    assert lecture(client, headers, espace["id"])["statut"] == "Optimal"

    assert client.delete(f"{API}/interventions/{intervention['id']}", headers=headers).status_code == 204
    assert actions(db) == []
    assert bilan_du_jour(db, espace["id"]).arrosage_mm == 0
    assert lecture(client, headers, espace["id"])["statut"] == "Critique"


def test_arrosage_d_un_jour_passe_corrige_la_chaine(client, db, meteo):
    headers = creer_compte(client)
    espace = creer_espace(client, headers, type_espace="Square", type_sol="Limoneux", surface_m2=SURFACE)
    maintenant = datetime.now(UTC)
    for jours in (2, 1, 0):
        executer_mise_a_jour(db, meteo_service=meteo, maintenant=maintenant - timedelta(days=jours))
    hier = aujourd_hui() - timedelta(days=1)
    midi_hier = datetime.combine(hier, time(12), tzinfo=settings.fuseau)

    r = arroser(client, headers, espace["id"], 500, statut="terminee", realisee_le=midi_hier.isoformat())
    assert r.status_code == 201 and r.json()["arrosage_compte_mm"] == 5.0

    db.expire_all()
    chaine = db.query(BilanHydriqueJournalier).filter_by(espace_id=espace["id"]).order_by(
        BilanHydriqueJournalier.date).all()
    assert [b.date for b in chaine] == [hier - timedelta(days=1), hier, aujourd_hui()]
    assert [b.arrosage_mm for b in chaine] == [0, 5.0, 0]
    assert chaine[1].source_meteo == "test-serie"
    for veille, jour in zip(chaine, chaine[1:], strict=False):
        assert jour.epuisement_debut_mm == pytest.approx(veille.epuisement_fin_mm)
    # 4 mm consommés par jour (ET0 5 × KL 0,8) ; 5 mm apportés hier : 4 − 5 + 4 = 3, puis 3 + 4 = 7
    assert chaine[1].epuisement_fin_mm == pytest.approx(3) and chaine[2].epuisement_fin_mm == pytest.approx(7)


def test_surface_inconnue_refusee_avec_un_message_clair(client, db, meteo):
    headers = creer_compte(client)
    espace = creer_espace(client, headers, surface_m2=None)
    r = arroser(client, headers, espace["id"], 300, statut="terminee")
    assert r.status_code == 422
    assert "Surface de l'espace inconnue" in r.json()["detail"]
    assert client.get(f"{API}/interventions/", headers=headers).json() == []      # rien d'enregistré

    planifiee = arroser(client, headers, espace["id"], 300).json()                  # planifier reste possible
    url = f"{API}/interventions/{planifiee['id']}"
    assert client.put(url, json={"statut": "terminee"}, headers=headers).status_code == 422
    assert client.get(url, headers=headers).json()["statut"] == "planifiee"         # transaction annulée
    # Sans volume, l'arrosage se termine sans rien compter
    assert client.put(url, json={"statut": "terminee", "volume_eau_l": None}, headers=headers).status_code == 200
    assert actions(db) == []

    # Surface renseignée : le même arrosage est compté
    client.put(f"{API}/espaces-verts/{espace['id']}", json={"surface_m2": 30}, headers=headers)
    assert client.put(url, json={"volume_eau_l": 300}, headers=headers).json()["arrosage_compte_mm"] == 10.0


def test_date_de_realisation_future_refusee(client, db, meteo):
    headers = creer_compte(client)
    espace = creer_espace(client, headers)
    demain = (datetime.now(UTC) + timedelta(days=1)).isoformat()
    r = arroser(client, headers, espace["id"], 300, statut="terminee", realisee_le=demain)
    assert r.status_code == 422 and "futur" in r.json()["detail"]
    assert actions(db) == []


def test_volume_borne(client, meteo):
    headers = creer_compte(client)
    espace = creer_espace(client, headers)
    assert arroser(client, headers, espace["id"], -1).status_code == 422
    assert arroser(client, headers, espace["id"], 10_000_001).status_code == 422


def test_meteo_indisponible_n_empeche_pas_de_terminer(client, db, meteo):
    headers = creer_compte(client)
    espace = espace_critique(client, db, meteo, headers)
    meteo.disponible = False
    r = arroser(client, headers, espace["id"], 3000, statut="terminee")
    assert r.status_code == 201 and r.json()["arrosage_compte_mm"] == 30.0
    assert bilan_du_jour(db, espace["id"]).arrosage_mm == 0                         # bilan non recalculé
    meteo.disponible = True
    executer_mise_a_jour(db, meteo_service=meteo)                                   # le worker rattrape
    assert bilan_du_jour(db, espace["id"]).arrosage_mm == 30.0


# --- Dose recommandée : lecture capteurs et diagnostic ----------------------------------

def test_dose_dans_la_lecture_et_le_diagnostic(client, db, meteo):
    headers = creer_compte(client)
    espace = espace_critique(client, db, meteo, headers)
    epuisement = epuisement_du_jour(0)
    dose = lecture(client, headers, espace["id"])["dose_recommandee"]
    assert dose == {"mm": round(epuisement, 1), "litres": round(epuisement * SURFACE / 0.75), "minutes": None}

    url = f"{API}/espaces-verts/{espace['id']}"
    assert client.put(url, json={"debit_arrosage_l_min": 0}, headers=headers).status_code == 422
    maj = client.put(url, json={"type_irrigation": "Goutte-à-goutte", "debit_arrosage_l_min": 25}, headers=headers)
    assert maj.status_code == 200 and maj.json()["debit_arrosage_l_min"] == 25
    litres = epuisement * SURFACE / 0.9
    attendue = {"mm": round(epuisement, 1), "litres": round(litres), "minutes": float(-(-litres // 25))}
    assert lecture(client, headers, espace["id"])["dose_recommandee"] == attendue

    diagnostic = client.post(f"{API}/health/diagnostic", json={"espace_id": espace["id"]}, headers=headers).json()
    assert diagnostic["dose_recommandee"] == attendue == diagnostic["mesures"]["dose_recommandee"]
    assert diagnostic["conseil_arrosage"] == formuler_dose(DoseRecommandee(**attendue))
    assert diagnostic["conseil_arrosage"].endswith("min au débit de l'arrosage).")


def test_pas_de_dose_sans_bilan_fao56(client, db, meteo):
    headers = creer_compte(client)
    espace = creer_espace(client, headers)
    assert lecture(client, headers, espace["id"])["dose_recommandee"] is None
    db.add(BilanHydriqueJournalier(espace_id=espace["id"], date=aujourd_hui(), reserve_utile_fin_journee=60,
                                   indice_stress=0.4, statut_hydrique="A surveiller", version_modele="historique-v1"))
    db.commit()
    assert lecture(client, headers, espace["id"])["dose_recommandee"] is None
    diagnostic = client.post(f"{API}/health/diagnostic", json={"espace_id": espace["id"]}, headers=headers).json()
    assert diagnostic["dose_recommandee"] is None and diagnostic["conseil_arrosage"] is None


# --- Droits et isolation -----------------------------------------------------------------

def test_isolation_et_droits_de_la_boucle(client, db, meteo):
    alice = creer_compte(client, "alice@example.com")
    espace = espace_critique(client, db, meteo, alice)
    intervention = arroser(client, alice, espace["id"], 3000).json()
    url = f"{API}/interventions/{intervention['id']}"

    bob = creer_compte(client, "bob@example.com")
    assert arroser(client, bob, espace["id"], 3000, statut="terminee").status_code == 404
    assert client.put(url, json={"statut": "terminee"}, headers=bob).status_code == 404
    assert client.delete(url, headers=bob).status_code == 404
    lecteur = ajouter_membre(client, db, alice, "elu@example.com", "lecteur")
    assert client.put(url, json={"statut": "terminee"}, headers=lecteur).status_code == 403
    assert actions(db) == [] and lecture(client, alice, espace["id"])["statut"] == "Critique"
    assert client.get(f"{API}/capteurs/dashboard", headers=bob).json()["capteurs"] == []

    technicien = ajouter_membre(client, db, alice, "tech@example.com", "technicien")
    r = client.put(url, json={"statut": "terminee"}, headers=technicien)
    assert r.status_code == 200 and r.json()["arrosage_compte_mm"] == 30.0
    assert client.delete(url, headers=technicien).status_code == 403              # suppression : gestionnaire
    assert len(actions(db)) == 1
    assert lecture(client, alice, espace["id"])["statut"] == "Optimal"

    # Le même volume chez Bob ne touche pas l'espace d'Alice
    espace_bob = creer_espace(client, bob, surface_m2=SURFACE)
    arroser(client, bob, espace_bob["id"], 1000, statut="terminee")
    assert [a.quantite_mm for a in actions(db, espace["id"])] == [30.0]
    assert [a.quantite_mm for a in actions(db, espace_bob["id"])] == [10.0]
