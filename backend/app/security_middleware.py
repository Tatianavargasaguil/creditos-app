import secrets
import logging
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Middleware para rate limiting por IP"""
    
    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, List[datetime]] = defaultdict()
    
    async def dispatch(self, request: Request, call_next):
        # Obtener IP del cliente
        client_ip = request.client.host if request.client else "unknown"
        
        # Endpoints sensibles con rate limit más restrictivo
        sensitive_endpoints = ["/api/auth/login", "/api/users"]
        is_sensitive = any(request.url.path.startswith(ep) for ep in sensitive_endpoints)
        
        limit = 5 if is_sensitive and request.method == "POST" else self.requests_per_minute
        
        # Limpiar requests antiguos
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)
        
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > cutoff
        ]
        
        # Verificar límite
        if len(self.requests[client_ip]) >= limit:
            logger.warning(f"Rate limit exceeded for {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiadas solicitudes. Intenta más tarde."
            )
        
        self.requests[client_ip].append(now)
        
        response = await call_next(request)
        return response


class CSRFMiddleware(BaseHTTPMiddleware):
    """Middleware para CSRF protection"""
    
    def __init__(self, app, token_length: int = 32):
        super().__init__(app)
        self.token_length = token_length
    
    async def dispatch(self, request: Request, call_next):
        # Generar token CSRF si no existe
        if "csrf_token" not in request.cookies:
            csrf_token = secrets.token_urlsafe(self.token_length)
            response = await call_next(request)
            response.set_cookie(
                "csrf_token",
                csrf_token,
                httponly=False,  # JavaScript lo debe leer
                secure=True,
                samesite="strict"
            )
            return response
        
        # Validar token CSRF en requests POST/PUT/DELETE/PATCH
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            csrf_token_cookie = request.cookies.get("csrf_token")
            csrf_token_header = request.headers.get("X-CSRF-Token")
            
            if not csrf_token_cookie or not csrf_token_header:
                logger.warning(f"CSRF token missing for {request.url.path}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Token CSRF faltante o inválido"
                )
            
            if not secrets.compare_digest(csrf_token_cookie, csrf_token_header):
                logger.warning(f"CSRF token mismatch for {request.url.path}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Token CSRF inválido"
                )
        
        response = await call_next(request)
        return response


def setup_security_middleware(app):
    """Configurar todos los middlewares de seguridad"""
    app.add_middleware(RateLimitMiddleware, requests_per_minute=100)
    app.add_middleware(CSRFMiddleware)
