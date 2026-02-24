from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship
from infrastructure.database import Base
from datetime import datetime

class EspeceVegetaleEntity(Base):
    __tablename__ = "especes_vegetales"
    
    id = Column(Integer, primary_key=True, index=True)
    nom_commun = Column(String(100), index=True)  # "Gazon festuca", "Rosier gallica"
    nom_scientifique = Column(String(150))
    
    # Seuils hydriques en pourcent
    humidite_sol_min = Column(Float, default=20.0)  # %
    humidite_sol_max = Column(Float, default=60.0)  # %
    humidite_sol_optimale = Column(Float, default=40.0)
    
    #  Déficit de Pression de Vapeur - indicateur stress 
    vpd_min = Column(Float, default=0.5)  # kPa
    vpd_max = Column(Float, default=2.0)  # kPa
    vpd_optimale = Column(Float, default=1.2)
    
    # CO2 et autres
    co2_seuil_stress = Column(Float, default=800.0)  # ppm
    oxygene_min = Column(Float, default=18.0)  # %
    
    #  besoin en eau relatif de la zone vegetal
    coeff_cultural = Column(Float, default=1.0)  # 0.8=peu, 1.2=moyen, 1.8=beaucoup
    
    # Audit
    cree_le = Column(DateTime, default=datetime.utcnow)
    
    # Relations
    espaces_verts = relationship(
        "EspaceVertEntity", 
        secondary="espaces_especes",  # table many-to-many auto-créée
        back_populates="especes_vegetales"
    )


""" ici nous le dossier espace vergetale a ne pas confondre avec espace vert , epace vert a comme paramettre le paramettre 
comme la localisation alors espace vegetale au comme paramettre des xtics des plantes presentes dans l'espace"""