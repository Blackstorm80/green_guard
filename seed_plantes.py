# Fichier: scripts/seed_plantes.py

# Données initiales pour peupler le catalogue de plantes.
PLANTES_SEED = [
    {
        "nom_scientifique": "Lavandula angustifolia",
        "nom_commun": "Lavande Vraie",
        "type_plante": "Arbuste",
        "besoin_eau": "Faible",
        "eau_min_mm_semaine": 5.0,
        "eau_max_mm_semaine": 15.0,
        "temp_min_confort": 15.0,
        "temp_max_confort": 30.0,
        "temp_min_survie": -15.0,
        "temp_max_survie": 40.0,
        "exposition": "Soleil",
        "type_sol_prefere": "Sableux",
        "ph_min": 6.5,
        "ph_max": 8.0,
        "icone": "🌿",
        "description_courte": "Arbuste aromatique résistant à la sécheresse, apprécié pour ses fleurs violettes.",
    },
    {
        "nom_scientifique": "Hosta 'Francee'",
        "nom_commun": "Hosta 'Francee'",
        "type_plante": "Vivace",
        "besoin_eau": "Élevé",
        "eau_min_mm_semaine": 30.0,
        "eau_max_mm_semaine": 50.0,
        "temp_min_confort": 10.0,
        "temp_max_confort": 22.0,
        "temp_min_survie": -20.0,
        "temp_max_survie": 30.0,
        "exposition": "Ombre",
        "type_sol_prefere": "Limoneux",
        "ph_min": 5.5,
        "ph_max": 7.5,
        "icone": "🍃",
        "description_courte": "Vivace d'ombre au feuillage panaché de vert et de blanc, idéale pour les sous-bois.",
    },
    {
        "nom_scientifique": "Rudbeckia fulgida",
        "nom_commun": "Rudbeckia 'Goldsturm'",
        "type_plante": "Vivace",
        "besoin_eau": "Moyen",
        "eau_min_mm_semaine": 15.0,
        "eau_max_mm_semaine": 25.0,
        "temp_min_confort": 18.0,
        "temp_max_confort": 28.0,
        "temp_min_survie": -30.0,
        "temp_max_survie": 35.0,
        "exposition": "Mi-ombre",
        "type_sol_prefere": "Argileux",
        "ph_min": 6.0,
        "ph_max": 7.5,
        "icone": "🌻",
        "description_courte": "Vivace robuste offrant une floraison estivale jaune d'or spectaculaire.",
    },
]

def seed_plantes(db):
    """
    Peuple la table 'plantes' avec les données initiales.
    'db' est attendu comme une session ou connexion de base de données
    compatible avec la DB-API (ex: session SQLAlchemy).
    """
    # Optionnel : vider la table avant de la repeupler.
    # Attention, cette opération est destructive.
    # from sqlalchemy import text
    # db.execute(text("DELETE FROM plantes"))

    # L'utilisation de `text` de SQLAlchemy est recommandée pour les requêtes SQL brutes.
    from sqlalchemy import text

    insert_sql = text("""
    INSERT INTO plantes (
        nom_scientifique, nom_commun, type_plante, besoin_eau,
        eau_min_mm_semaine, eau_max_mm_semaine, temp_min_confort,
        temp_max_confort, temp_min_survie, temp_max_survie,
        exposition, type_sol_prefere, ph_min, ph_max, icone,
        description_courte
    ) VALUES (
        :nom_scientifique, :nom_commun, :type_plante, :besoin_eau,
        :eau_min_mm_semaine, :eau_max_mm_semaine, :temp_min_confort,
        :temp_max_confort, :temp_min_survie, :temp_max_survie,
        :exposition, :type_sol_prefere, :ph_min, :ph_max, :icone,
        :description_courte
    )
    """)

    for plante in PLANTES_SEED:
        db.execute(insert_sql, plante)

    db.commit()
    print("🌱 Table 'plantes' peuplée avec succès !")

# Pour exécuter ce script manuellement :
# from infrastructure.database import SessionLocal
# db = SessionLocal()
# seed_plantes(db)
# db.close()