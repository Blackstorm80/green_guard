from datetime import datetime
import random
from sqlalchemy.orm import Session
from sqlalchemy import desc, func

from domain.models import EspaceVert, Mesure, BilanHydriqueJournalier, ActionIrrigation
from domain.logic.bilan_hydrique import calculer_bilan_hydrique_pour_jour
from infrastructure.services.meteo_open_meteo import OpenMeteoService

class CapteurHybridService:
    def __init__(self, db_session: Session):
        self.db = db_session
        self.meteo_service = OpenMeteoService()

    def lecture_actuelle(self, espace_id: int):
        """
        Récupère la télémétrie réelle ou simulée.
        REMARQUE : Les clés correspondent exactement à LectureCapteurDTO.
        """
        # 1. Recherche de la dernière mesure en base de données
        derniere_mesure = self.db.query(Mesure)\
            .filter(Mesure.espace_id == espace_id)\
            .order_by(desc(Mesure.timestamp))\
            .first()

        if derniere_mesure:
            return {
                "espace_id": espace_id,
                "temperature_c": float(derniere_mesure.temperature),
                "humidite_percent": float(derniere_mesure.humidite_sol),
                "luminosite_lux": int(getattr(derniere_mesure, 'luminosite', 2500)),
                "co2_ppm": int(getattr(derniere_mesure, 'co2', 450)),
                "o2_percent": 20.9,
                "reserve_eau_mm": float(getattr(derniere_mesure, 'reserve_eau', 12.5)),
                "timestamp": derniere_mesure.timestamp.isoformat() if hasattr(derniere_mesure.timestamp, 'isoformat') else str(derniere_mesure.timestamp)
            }

        # 2. Fallback de simulation si aucune donnée n'est présente
        return {
            "espace_id": espace_id,
            "temperature_c": round(random.uniform(19.0, 24.5), 1),
            "humidite_percent": float(random.randint(40, 65)),
            "luminosite_lux": random.randint(1500, 4000),
            "co2_ppm": random.randint(420, 580),
            "o2_percent": 20.9,
            "reserve_eau_mm": round(random.uniform(8.0, 15.0), 1),
            "timestamp": datetime.utcnow().isoformat()
        }

    def mise_a_jour_complete(self):
        """
        Logique métier : Calcule le bilan hydrique et génère de nouvelles mesures.
        """
        espaces = self.db.query(EspaceVert).all()
        now = datetime.utcnow()

        for espace in espaces:
            # Récupération météo
            meteo = self.meteo_service.recuperer_conditions_actuelles(
                latitude=espace.latitude, longitude=espace.longitude, maintenant=now
            )
            
            if not meteo or getattr(meteo, 'pluie', None) is None or getattr(meteo, 'et0', None) is None:
                import logging
                logging.warning(f"Données météo manquantes pour l'espace {espace.id} (et0 ou pluie absente). Calcul ignoré.")
                continue

            # Récupération bilan précédent
            bilan_precedent = self.db.query(BilanHydriqueJournalier) \
                .filter(BilanHydriqueJournalier.espace_id == espace.id) \
                .order_by(desc(BilanHydriqueJournalier.date)) \
                .first()

            # Cumul irrigation
            arrosage_mm = self.db.query(func.sum(ActionIrrigation.quantite_mm)) \
                .filter(ActionIrrigation.espace_id == espace.id) \
                .filter(func.date(ActionIrrigation.timestamp) == now.date()) \
                .scalar() or 0.0

            # Calcul via le coeur algorithmique
            resultat_metier = calculer_bilan_hydrique_pour_jour(
                espace_vert=espace,
                bilan_precedent=bilan_precedent,
                pluie_jour_mm=meteo.pluie,
                et0_jour_mm=meteo.et0,
                arrosage_jour_mm=arrosage_mm,
                date_du_jour=now.date(),
                stress_sanitaire_jour=None
            )

            # Sauvegarde Bilan
            nouveau_bilan_db = BilanHydriqueJournalier(
                espace_id=espace.id,
                date=now.date(),
                reserve_utile_fin_journee=resultat_metier.reserve_eau,
                indice_stress=resultat_metier.indice_stress,
                statut_hydrique=resultat_metier.statut_hydrique,
                stress_sanitaire=resultat_metier.stress_sanitaire
            )
            self.db.add(nouveau_bilan_db)
            
            # Sauvegarde Mesure (Dashboard)
            res_max = espace.reserve_utile_max if espace.reserve_utile_max > 0 else 1
            humidite_percent = (resultat_metier.reserve_eau / res_max) * 100
            
            nouvelle_mesure = Mesure(
                espace_id=espace.id,
                temperature=meteo.temperature_c,
                humidite_sol=round(max(0, min(100, humidite_percent)), 1),
                humidite_air=meteo.humidite,
                timestamp=now
            )
            self.db.add(nouvelle_mesure)

        self.db.commit()

# --- Script de mise à jour ---
def run_update():
    from infrastructure.database import SessionLocal
    db = SessionLocal()
    try:
        service = CapteurHybridService(db)
        service.mise_a_jour_complete()
        print("--- MISE A JOUR DES CAPTEURS REUSSIE ---")
    except Exception as e:
        print(f"--- ERREUR SIMULATION : {e} ---")
    finally:
        db.close()

if __name__ == "__main__":
    run_update()