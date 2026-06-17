from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from ..database import get_db
from ..security import get_current_user
from ..models import User, Message
from ..schemas import MessageCreate
from datetime import datetime

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/messages")
async def send_message(
    msg_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Enviar mensaje a otro usuario"""
    
    # Validar que el destinatario existe y está activo
    recipient = db.query(User).filter(User.id == msg_data.recipient_id, User.active == True).first()
    if not recipient:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o inactivo")
    
    # Solo admin puede enviar a cualquiera, usuarios solo a admin
    if current_user.role != "admin":
        admin_users = db.query(User).filter(User.role == "admin", User.active == True).all()
        admin_ids = [admin.id for admin in admin_users]
        if msg_data.recipient_id not in admin_ids:
            raise HTTPException(status_code=403, detail="Solo puedes enviar mensajes a administrador")
    
    message = Message(
        sender_id=current_user.id,
        recipient_id=msg_data.recipient_id,
        content=msg_data.content
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    return {
        "id": message.id,
        "sender_id": message.sender_id,
        "recipient_id": message.recipient_id,
        "content": message.content,
        "read": message.read,
        "created_at": message.created_at.isoformat()
    }


@router.get("/messages")
async def get_messages(
    user_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener conversación con un usuario específico"""
    
    # Validar que el otro usuario existe y está activo
    other_user = db.query(User).filter(User.id == user_id, User.active == True).first()
    if not other_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado o inactivo")
    
    # Obtener mensajes en ambas direcciones
    messages = db.query(Message).filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.recipient_id == user_id),
            and_(Message.sender_id == user_id, Message.recipient_id == current_user.id)
        )
    ).order_by(Message.created_at.asc()).all()
    
    # Marcar como leídos los mensajes recibidos
    for msg in messages:
        if msg.recipient_id == current_user.id and not msg.read:
            msg.read = True
    db.commit()
    
    return [
        {
            "id": msg.id,
            "sender_id": msg.sender_id,
            "recipient_id": msg.recipient_id,
            "content": msg.content,
            "read": msg.read,
            "created_at": msg.created_at.isoformat(),
            "sender_name": msg.sender.full_name or msg.sender.username
        }
        for msg in messages
    ]


@router.get("/conversations")
async def get_conversations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener lista de usuarios con conversaciones"""
    
    user_ids = set()
    messages = db.query(Message).filter(
        or_(Message.sender_id == current_user.id, Message.recipient_id == current_user.id)
    ).all()
    
    for msg in messages:
        if msg.sender_id == current_user.id:
            user_ids.add(msg.recipient_id)
        else:
            user_ids.add(msg.sender_id)
    
    conversations = []
    for user_id in user_ids:
        user = db.query(User).filter(User.id == user_id, User.active == True).first()
        if user:
            unread = db.query(Message).filter(
                Message.sender_id == user_id,
                Message.recipient_id == current_user.id,
                Message.read == False
            ).count()
            
            conversations.append({
                "id": user.id,
                "name": user.full_name or user.username,
                "email": user.username,
                "role": user.role,
                "unread_count": unread
            })
    
    return conversations


@router.get("/users")
async def get_available_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener usuarios disponibles para chat"""
    
    if current_user.role == "admin":
        # Admin puede chatear con todos excepto con él mismo, solo los activos
        users = db.query(User).filter(User.id != current_user.id, User.active == True).all()
    else:
        # Usuarios normales solo pueden chatear con admin activos
        users = db.query(User).filter(User.role == "admin", User.active == True).all()
    
    return [
        {
            "id": user.id,
            "name": user.full_name or user.username,
            "email": user.username,
            "role": user.role,
            "unread_count": 0
        }
        for user in users
    ]


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar un mensaje (solo el que lo envió)"""
    
    message = db.query(Message).filter(Message.id == message_id).first()
    if not message:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    
    # Solo el remitente puede eliminar su propio mensaje
    if message.sender_id != current_user.id:
        raise HTTPException(status_code=403, detail="Solo puedes eliminar tus propios mensajes")
    
    db.delete(message)
    db.commit()
    
    return {"message": "Mensaje eliminado correctamente"}
