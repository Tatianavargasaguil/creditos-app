from sqlalchemy.orm import Session

from . import models
from app.security import hash_password


STAGES = [
    ("Viabilidad", "viabilidad", 10, None, False),
    ("Gestion Documental", "gestion_documental", 20, None, False),
    ("Estudio", "estudio", 30, 24, False),
    ("Respuesta de Estudio", "respuesta_estudio", 40, None, False),
    ("Aprobado", "aprobado", 50, None, False),
    ("Firmado", "firmado", 60, 24, False),
    ("Desembolsado", "desembolsado", 70, 96, False),
    ("Legalizacion TPE", "legalizacion", 80, None, False),
    ("Desasignado", "desasignado", 90, None, True),
]

BANKS = [
    ("Confiemza", 10, False, False, False, False),
    ("Apoyautos", 20, False, False, False, False),
    ("Davivienda", 30, False, False, False, False),
    ("Movilize", 40, True, True, True, True),
    ("Finandina", 50, False, False, False, False),
    ("Fineza", 60, False, False, False, False),
    ("Occidente", 70, False, True, False, False),
    ("Bancolombia", 80, False, False, False, False),
    ("Santander", 90, False, False, False, False),
    ("Finanzauto", 100, False, False, False, False),
    ("BBVA", 110, False, False, False, False),
    ("Promotec", 120, False, False, False, False),
]


def seed_initial_data(db: Session) -> None:
    for name, code, sequence, max_hours, folded in STAGES:
        exists = db.query(models.Stage).filter(models.Stage.code == code).first()
        if not exists:
            db.add(models.Stage(name=name, code=code, sequence=sequence, max_hours=max_hours, folded=folded))

    for name, sequence, is_movilize, requires_ctl, requires_vehicle_history, requires_owner_history in BANKS:
        exists = db.query(models.Bank).filter(models.Bank.name == name).first()
        if not exists:
            db.add(
                models.Bank(
                    name=name,
                    sequence=sequence,
                    is_movilize=is_movilize,
                    requires_ctl=requires_ctl,
                    requires_vehicle_history=requires_vehicle_history,
                    requires_owner_history=requires_owner_history,
                )
            )

    default_users = [
        ("admin", "Administrador", "admin123", models.UserRole.admin),
        ("usuario", "Usuario Creditos", "usuario123", models.UserRole.user),
    ]
    for username, full_name, password, role in default_users:
        exists = db.query(models.User).filter(models.User.username == username).first()
        if not exists:
            db.add(
                models.User(
                    username=username,
                    full_name=full_name,
                    password_hash=hash_password(password),
                    role=role,
                    active=True,
                )
            )
    db.commit()
