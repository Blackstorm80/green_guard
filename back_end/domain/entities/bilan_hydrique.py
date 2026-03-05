from sqlalchemy import Column, Integer, Float, Date, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.database import Base
from datetime import date

class BilanHydriqueJournalierEntity(Base):
    __tablename__ = "bilans_hydriques"
    
    id = Column(Integer, primary_key=True, index=True)
    espace_id = Column(Integer, ForeignKey("espaces_verts.id"))
    date_bilan = Column(Date)
    precipitations_mm = Column(Float)
    evapotranspiration_mm = Column(Float)
    bilan_mm = Column(Float)
    arrosage_recommande_mm = Column(Float)
    
    # Relation bidirectionnelle
    espace = relationship("EspaceVertEntity", back_populates="bilans")