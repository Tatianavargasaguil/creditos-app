from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.database import get_db
from app.security import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


def _notification_query(db: Session):
    return db.query(models.Notification).options(
        joinedload(models.Notification.sender),
        joinedload(models.Notification.recipient),
    )


@router.get("/recipients", response_model=list[schemas.UserRead])
def recipients(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.User)
        .filter(models.User.active.is_(True), models.User.id != current_user.id)
        .order_by(models.User.full_name)
        .all()
    )


@router.get("", response_model=list[schemas.NotificationRead])
def list_notifications(
    box: str = "inbox",
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    query = _notification_query(db)
    if box == "sent":
        query = query.filter(models.Notification.sender_id == current_user.id)
    elif box == "all":
        query = query.filter(
            or_(
                models.Notification.sender_id == current_user.id,
                models.Notification.recipient_id == current_user.id,
            )
        )
    else:
        query = query.filter(models.Notification.recipient_id == current_user.id)
    return query.order_by(models.Notification.created_at.desc()).all()


@router.post("", response_model=schemas.NotificationRead, status_code=status.HTTP_201_CREATED)
def create_notification(
    payload: schemas.NotificationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    recipient = db.get(models.User, payload.recipient_id)
    if not recipient or not recipient.active:
        raise HTTPException(status_code=404, detail="Destinatario no encontrado")
    if payload.credit_id and not db.get(models.CreditRequest, payload.credit_id):
        raise HTTPException(status_code=404, detail="Credito no encontrado")

    notification = models.Notification(
        sender_id=current_user.id,
        recipient_id=payload.recipient_id,
        credit_id=payload.credit_id,
        subject=payload.subject,
        message=payload.message,
    )
    db.add(notification)
    db.commit()
    return _notification_query(db).filter(models.Notification.id == notification.id).one()


@router.post("/{notification_id}/read", response_model=schemas.NotificationRead)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    notification = db.get(models.Notification, notification_id)
    if not notification or notification.recipient_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notificacion no encontrada")
    if not notification.read_at:
        notification.read_at = datetime.utcnow()
        db.commit()
    return _notification_query(db).filter(models.Notification.id == notification.id).one()
