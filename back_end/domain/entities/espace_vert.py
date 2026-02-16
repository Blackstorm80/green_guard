from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from infrastructure.database import Base

class EspaceVertEntity(Base):
    __tablename__ = "espaces_verts"

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String, index=True)
    ville = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    surface_m2 = Column(Float)
    sante_percent = Column(Float)

    # Clé étrangère vers l'utilisateur, requise par le script init_db.py
    user_id = Column(Integer, ForeignKey("users.id"))

    # Relation inverse (à la fin de EspaceVertEntity)
    bilans = relationship("BilanHydriqueJournalierEntity", back_populates="espace")