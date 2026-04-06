# back_end/sanity_check.py
from infrastructure.database import SessionLocal, DATABASE_PATH
from domain.models import Plante, Auxiliaire

print(f"--- VERIFICATION DU COEUR ---")
print(f"Fichier utilisé : {DATABASE_PATH}")

db = SessionLocal()
try:
    nb_plantes = db.query(Plante).count()
    nb_insectes = db.query(Auxiliaire).count()
    
    print(f"Nombre de plantes en base : {nb_plantes}")
    print(f"Nombre d'insectes en base : {nb_insectes}")
    
    if nb_plantes > 0:
        p = db.query(Plante).first()
        print(f"Première plante trouvée : {p.nom_commun} ({p.nom_scientifique})")
    else:
        print("ALERTE : La table des plantes est vide !")
        
finally:
    db.close()
    