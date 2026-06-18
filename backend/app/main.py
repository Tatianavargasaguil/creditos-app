from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.config import settings
from app.database import Base, SessionLocal, engine
from app.routers import auth, catalogs, credits, notifications, users, chat
from app.seed import seed_initial_data
from app.security_middleware import setup_security_middleware


def ensure_development_columns() -> None:
    statements = [
        "ALTER TABLE credit_documents ADD COLUMN IF NOT EXISTS mime_type VARCHAR(120)",
        "ALTER TABLE credit_documents ADD COLUMN IF NOT EXISTS file_size INTEGER",
        "ALTER TABLE credit_documents ADD COLUMN IF NOT EXISTS file_data BYTEA",
        "ALTER TABLE credit_alerts ADD COLUMN IF NOT EXISTS email_to VARCHAR(240)",
        "ALTER TABLE credit_alerts ADD COLUMN IF NOT EXISTS email_sent BOOLEAN DEFAULT FALSE",
        "ALTER TABLE credit_alerts ADD COLUMN IF NOT EXISTS email_sent_at TIMESTAMP",
        "ALTER TABLE credit_alerts ADD COLUMN IF NOT EXISTS email_error TEXT",
    ]
    with engine.begin() as connection:
        for statement in statements:
            connection.execute(text(statement))


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)
    
    # Agregar middlewares de seguridad
    setup_security_middleware(app)
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    def on_startup() -> None:
        Base.metadata.create_all(bind=engine)
        ensure_development_columns()
        db = SessionLocal()
        try:
            seed_initial_data(db)
        finally:
            db.close()

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "app": settings.app_name}

    app.include_router(catalogs.router, prefix="/api")
    app.include_router(credits.router, prefix="/api")
    app.include_router(auth.router, prefix="/api")
    app.include_router(users.router, prefix="/api")
    app.include_router(notifications.router, prefix="/api")
    app.include_router(chat.router, prefix="/api")
    return app


app = create_app()
