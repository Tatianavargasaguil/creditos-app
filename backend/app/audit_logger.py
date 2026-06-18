import logging
import json
from datetime import datetime
from typing import Any

# Configurar logging de auditoría
audit_logger = logging.getLogger("audit")
audit_handler = logging.FileHandler("audit.log")
audit_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
audit_handler.setFormatter(audit_formatter)
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)


def log_login_attempt(username: str, success: bool, client_ip: str):
    """Registrar intentos de login"""
    event = {
        "type": "LOGIN_ATTEMPT",
        "username": username,
        "success": success,
        "client_ip": client_ip,
        "timestamp": datetime.utcnow().isoformat()
    }
    audit_logger.info(json.dumps(event))


def log_user_creation(created_by: str, new_username: str, role: str, client_ip: str):
    """Registrar creación de usuarios"""
    event = {
        "type": "USER_CREATED",
        "created_by": created_by,
        "new_username": new_username,
        "role": role,
        "client_ip": client_ip,
        "timestamp": datetime.utcnow().isoformat()
    }
    audit_logger.info(json.dumps(event))


def log_credit_modification(user_id: int, credit_id: int, action: str, changes: dict, client_ip: str):
    """Registrar modificaciones a créditos"""
    event = {
        "type": "CREDIT_MODIFIED",
        "user_id": user_id,
        "credit_id": credit_id,
        "action": action,
        "changes": changes,
        "client_ip": client_ip,
        "timestamp": datetime.utcnow().isoformat()
    }
    audit_logger.info(json.dumps(event))


def log_unauthorized_access(user_id: int, resource: str, client_ip: str):
    """Registrar intentos de acceso no autorizado"""
    event = {
        "type": "UNAUTHORIZED_ACCESS",
        "user_id": user_id,
        "resource": resource,
        "client_ip": client_ip,
        "timestamp": datetime.utcnow().isoformat()
    }
    audit_logger.warning(json.dumps(event))
