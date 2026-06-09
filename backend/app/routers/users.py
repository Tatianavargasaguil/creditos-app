from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import hash_password, require_admin

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[schemas.UserRead])
def list_users(
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    return db.query(models.User).filter(models.User.active.is_(True)).order_by(models.User.full_name).all()


@router.post("", response_model=schemas.UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: schemas.UserCreate,
    db: Session = Depends(get_db),
    _admin: models.User = Depends(require_admin),
):
    role = payload.role if payload.role in ("admin", "user") else "user"
    exists = db.query(models.User).filter(models.User.username == payload.username).first()
    if exists:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    user = models.User(
        username=payload.username,
        full_name=payload.full_name,
        password_hash=hash_password(payload.password),
        role=role,
        active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: models.User = Depends(require_admin),
):
    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user.id == admin.id:
        raise HTTPException(status_code=400, detail="No puedes eliminar tu propio usuario")
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="No se puede eliminar el administrador base")

    user.active = False
    db.commit()
    return None
