"""
 Initialisation complète de la base Green Guard
- Crée TOUTES les tables
- Ajoute des données de démo por commencer a tester
"""

from datetime import date
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from domain.entities.espece_vegetale import EspeceVegetaleEntity
# Le `README.md` et les cas d'usage indiquent que les entités sont
# dans `domain/entities.py`. Les imports sont donc ajustés en conséquence.
from domain.entities import UserEntity
    

from infrastructure.database import Base
from domain.entities.espace_vert import EspaceVertEntity
from domain.entities.bilan_hydrique import BilanHydriqueJournalierEntity

# Connexion DB
# Le chemin est relatif au dossier `back_end/` où le script sera lancé.
engine = create_engine("sqlite:///./data/green_guard.db")
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db = SessionLocal()

print("  Création des tables...")

# CRÉE TOUTES LES TABLES
# `Base.metadata` contient les méta-informations de toutes les classes
# qui héritent de `Base` (nos entités SQLAlchemy).
Base.metadata.create_all(bind=engine)

print(" Tables créées !")

# DONNÉES DE DÉMO
print("🌱 Insertion données de démo...")

# 1. USERS
user1 = UserEntity(
    name="Admin Vert",
    email="admin@green-guard.fr",
    role="admin"
)
db.add(user1)
db.flush()  # On flush pour que la base assigne un ID à `user1`

# 2. ESPACES VERTS (Paris + banlieue)
espaces = [
    EspaceVertEntity(
        nom="Parc des Buttes-Chaumont",
        ville="Paris 19e",
        latitude=48.8839, longitude=2.3844,
        surface_m2=25000, sante_percent=85
    ),
    EspaceVertEntity(
        nom="Jardin Luxembourg",
        ville="Paris 6e",
        latitude=48.8468, longitude=2.3375,
        surface_m2=23000, sante_percent=92
    ),
    EspaceVertEntity(
        nom="Parc Montsouris",
        ville="Paris 14e",
        latitude=48.8195, longitude=2.3414,
        surface_m2=18000, sante_percent=67
    ),
    EspaceVertEntity(
        nom="Bois de Vincennes",
        ville="Paris 12e",
        latitude=48.8353, longitude=2.4079,
        surface_m2=995000, sante_percent=78
    ),
    EspaceVertEntity(
        nom="Parc de Sceaux",
        ville="Sceaux",
        latitude=48.7805, longitude=2.2389,
        surface_m2=60000, sante_percent=45
    ),
]

for espace in espaces:
    espace.user_id = user1.id
    db.add(espace)

db.flush() # On flush pour que la base assigne les IDs aux espaces

# 3. BILANS HYDRIQUES
for i, espace in enumerate(espaces):
    db.add(BilanHydriqueJournalierEntity(
        espace_id=espace.id,
        date_bilan=date.today(), # Utilisation de la date du jour
        precipitations_mm=2.5 + i*0.5,
        evapotranspiration_mm=3.2,
        bilan_mm=-0.7,
        arrosage_recommande_mm=1.5
    ))

# 4. CAPTEURS
capteurs_demo = [
    CapteurEntity(espace_id=espaces[0].id, type="humidité", valeur=65),
    CapteurEntity(espace_id=espaces[1].id, type="humidité", valeur=78),
    CapteurEntity(espace_id=espaces[2].id, type="humidité", valeur=42),
]

for capteur in capteurs_demo:
    db.add(capteur)

db.commit()
db.close()



# Espèces de référence (données réalistes)
# 1. D'ABORD créer les users
user1 = UserEntity(username="admin", email="admin@green.guard", role="admin")
db.add(user1)
db.commit()

# 2. ENSUITE créer les espaces verts
espace1 = EspaceVertEntity(
    nom="Parc des Buttes Chaumont",
    ville="Paris",
    latitude=48.88,
    longitude=2.38,
    surface_m2=1000,
    sante_percent=85.0,
    user_id=user1.id
)
db.add(espace1)
db.flush()  # Récupère l'ID

espace2 = EspaceVertEntity(
    nom="Square du Colonel Fabien", 
    ville="Paris",
    latitude=48.89,
    longitude=2.39,
    surface_m2=250,
    sante_percent=72.0,
    user_id=user1.id
)
db.add(espace2)
db.flush()

# 3. ENSUITE créer les espèces
especes_demo = [
    EspeceVegetaleEntity(
        nom_commun="Gazon festuca",
        nom_scientifique="Festuca arundinacea",
        humidite_sol_min=25, humidite_sol_max=45,
        vpd_min=0.8, vpd_max=1.8,
        coeff_cultural=1.1
    )
]
for espece in especes_demo:
    db.add(espece)
db.flush()

# 4. ENSUITE lier (maintenant TOUT existe)
db.add_all(especes_demo)
db.commit()

espace1.especes_vegetales.append(especes_demo[0])
espace2.especes_vegetales.append(especes_demo[0])
db.commit()


