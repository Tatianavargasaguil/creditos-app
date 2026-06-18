from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.security import create_token, get_current_user, verify_password
from app.audit_logger import log_login_attempt

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=schemas.LoginResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db), request: Request = None):
    client_ip = request.client.host if request and request.client else "unknown"
    
    user = db.query(models.User).filter(models.User.username == payload.username).first()
    is_valid = user and user.active and verify_password(payload.password, user.password_hash)
    
    # Registrar intento de login
    log_login_attempt(payload.username, is_valid, client_ip)
    
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña invalida")
    
    return schemas.LoginResponse(access_token=create_token(user), user=user)


@router.get("/me", response_model=schemas.UserRead)
def me(current_user: models.User = Depends(get_current_user)):
    return current_user
