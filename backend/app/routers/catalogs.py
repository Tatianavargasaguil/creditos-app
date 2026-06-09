from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import get_current_user

router = APIRouter(prefix="/catalogs", tags=["catalogs"])


@router.get("/stages", response_model=list[schemas.StageRead])
def list_stages(db: Session = Depends(get_db), _current_user: models.User = Depends(get_current_user)):
    return db.query(models.Stage).order_by(models.Stage.sequence).all()


@router.get("/banks", response_model=list[schemas.BankRead])
def list_banks(db: Session = Depends(get_db), _current_user: models.User = Depends(get_current_user)):
    return db.query(models.Bank).filter(models.Bank.active.is_(True)).order_by(models.Bank.sequence).all()
