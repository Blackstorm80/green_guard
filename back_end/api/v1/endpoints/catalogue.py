# back_end/api/v1/endpoints/catalogue.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from infrastructure.database import get_db
from domain.models import Plante, Auxiliaire
from typing import List

router = APIRouter()

@router.get("/plantes")
def get_plantes(db: Session = Depends(get_db)):
    return db.query(Plante).all()

@router.get("/auxiliaires")
def get_auxiliaires(db: Session = Depends(get_db)):
    return db.query(Auxiliaire).all()