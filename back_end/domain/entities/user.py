from sqlalchemy import Column, Integer, String
from infrastructure.database import Base
from sqlalchemy.orm import relationship

class UserEntity(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(String, default="user")  # admin, manager, user
    configs_clustering = relationship("ClusteringConfigEntity", back_populates="user")
    zones_intelligentes = relationship("ZoneIntelligenteEntity", back_populates="user")
