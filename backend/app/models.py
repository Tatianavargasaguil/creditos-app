from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, LargeBinary, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class StageCode(str, Enum):
    viabilidad = "viabilidad"
    gestion_documental = "gestion_documental"
    estudio = "estudio"
    respuesta_estudio = "respuesta_estudio"
    aprobado = "aprobado"
    firmado = "firmado"
    desembolsado = "desembolsado"
    legalizacion = "legalizacion"
    desasignado = "desasignado"


class BankLineType(str, Enum):
    viabilidad = "viabilidad"
    estudio = "estudio"
    aprobacion = "aprobacion"
    rechazo = "rechazo"
    desembolso = "desembolso"


class BankLineStatus(str, Enum):
    pendiente = "pendiente"
    radicado = "radicado"
    aprobado = "aprobado"
    negado = "negado"
    desembolsado = "desembolsado"


class AlertStatus(str, Enum):
    pendiente = "pendiente"
    enviado = "enviado"
    fallido = "fallido"


class UserRole(str, Enum):
    admin = "admin"
    user = "user"
    advisor = "advisor"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    full_name: Mapped[str] = mapped_column(String(140))
    password_hash: Mapped[str] = mapped_column(String(260))
    role: Mapped[UserRole] = mapped_column(String(20), default=UserRole.user)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Stage(Base):
    __tablename__ = "credit_stages"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80), unique=True)
    code: Mapped[StageCode] = mapped_column(String(40), unique=True)
    sequence: Mapped[int] = mapped_column(Integer, default=10)
    max_hours: Mapped[int | None] = mapped_column(Integer, nullable=True)
    folded: Mapped[bool] = mapped_column(Boolean, default=False)


class Bank(Base):
    __tablename__ = "banks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    sequence: Mapped[int] = mapped_column(Integer, default=10)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_movilize: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_ctl: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_vehicle_history: Mapped[bool] = mapped_column(Boolean, default=False)
    requires_owner_history: Mapped[bool] = mapped_column(Boolean, default=False)


class CreditRequest(Base):
    __tablename__ = "credit_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference: Mapped[str] = mapped_column(String(30), unique=True, index=True)
    odoo_order_ref: Mapped[str | None] = mapped_column(String(80), index=True)
    stage_id: Mapped[int] = mapped_column(ForeignKey("credit_stages.id"))
    stage_started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    advisor_name: Mapped[str | None] = mapped_column(String(120))
    showroom: Mapped[str | None] = mapped_column(String(120))
    business_type: Mapped[str | None] = mapped_column(String(120))

    document_type: Mapped[str | None] = mapped_column(String(30))
    document_number: Mapped[str | None] = mapped_column(String(50), index=True)
    customer_name: Mapped[str] = mapped_column(String(160), index=True)
    phone: Mapped[str | None] = mapped_column(String(50))

    plate: Mapped[str | None] = mapped_column(String(20), index=True)
    vin: Mapped[str | None] = mapped_column(String(80), index=True)
    brand: Mapped[str | None] = mapped_column(String(80))
    line: Mapped[str | None] = mapped_column(String(120))
    model: Mapped[str | None] = mapped_column(String(30))

    sale_price: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    down_payment: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    proforma_invoice_ref: Mapped[str | None] = mapped_column(String(120))
    final_invoice_ref: Mapped[str | None] = mapped_column(String(120))

    viability_bank_id: Mapped[int | None] = mapped_column(ForeignKey("banks.id"), nullable=True)
    selected_bank_id: Mapped[int | None] = mapped_column(ForeignKey("banks.id"), nullable=True)
    disbursement_bank_id: Mapped[int | None] = mapped_column(ForeignKey("banks.id"), nullable=True)

    approval_conditions: Mapped[str | None] = mapped_column(Text)
    observations: Mapped[str | None] = mapped_column(Text)
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    ok_runt: Mapped[bool] = mapped_column(Boolean, default=False)
    ok_runt_at: Mapped[datetime | None] = mapped_column(DateTime)
    runt_observation: Mapped[str | None] = mapped_column(Text)
    insured_ok: Mapped[bool] = mapped_column(Boolean, default=False)
    policy_issued: Mapped[bool] = mapped_column(Boolean, default=False)
    insurance_company: Mapped[str | None] = mapped_column(String(120))
    policy_observation: Mapped[str | None] = mapped_column(Text)

    disbursed_value: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    ownership_card_issued: Mapped[bool] = mapped_column(Boolean, default=False)
    ownership_card_delivery_date: Mapped[datetime | None] = mapped_column(Date)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stage: Mapped[Stage] = relationship()
    viability_bank: Mapped[Bank | None] = relationship(foreign_keys=[viability_bank_id])
    selected_bank: Mapped[Bank | None] = relationship(foreign_keys=[selected_bank_id])
    disbursement_bank: Mapped[Bank | None] = relationship(foreign_keys=[disbursement_bank_id])
    bank_lines: Mapped[list["CreditBankLine"]] = relationship(back_populates="credit", cascade="all, delete-orphan")
    documents: Mapped[list["CreditDocument"]] = relationship(back_populates="credit", cascade="all, delete-orphan")
    alerts: Mapped[list["CreditAlert"]] = relationship(back_populates="credit", cascade="all, delete-orphan")
    history: Mapped[list["CreditHistory"]] = relationship(back_populates="credit", cascade="all, delete-orphan")

    @property
    def financed_value(self) -> float:
        return float(self.sale_price or 0) - float(self.down_payment or 0)


class CreditBankLine(Base):
    __tablename__ = "credit_bank_lines"

    id: Mapped[int] = mapped_column(primary_key=True)
    credit_id: Mapped[int] = mapped_column(ForeignKey("credit_requests.id"))
    bank_id: Mapped[int] = mapped_column(ForeignKey("banks.id"))
    type: Mapped[BankLineType] = mapped_column(String(30), default=BankLineType.estudio)
    status: Mapped[BankLineStatus] = mapped_column(String(30), default=BankLineStatus.pendiente)
    filed_at: Mapped[datetime | None] = mapped_column(DateTime)
    answered_at: Mapped[datetime | None] = mapped_column(DateTime)
    approved_amount: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    disbursed_value: Mapped[float] = mapped_column(Numeric(14, 2), default=0)
    term: Mapped[str | None] = mapped_column(String(80))
    rate: Mapped[str | None] = mapped_column(String(80))
    conditions: Mapped[str | None] = mapped_column(Text)
    rejection_reason: Mapped[str | None] = mapped_column(Text)

    credit: Mapped[CreditRequest] = relationship(back_populates="bank_lines")
    bank: Mapped[Bank] = relationship()


class CreditDocument(Base):
    __tablename__ = "credit_documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    credit_id: Mapped[int] = mapped_column(ForeignKey("credit_requests.id"))
    name: Mapped[str] = mapped_column(String(160))
    type: Mapped[str] = mapped_column(String(60), default="otro")
    file_name: Mapped[str | None] = mapped_column(String(220))
    file_url: Mapped[str | None] = mapped_column(String(500))
    mime_type: Mapped[str | None] = mapped_column(String(120))
    file_size: Mapped[int | None] = mapped_column(Integer)
    file_data: Mapped[bytes | None] = mapped_column(LargeBinary)
    observation: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    credit: Mapped[CreditRequest] = relationship(back_populates="documents")


class CreditAlert(Base):
    __tablename__ = "credit_alerts"

    id: Mapped[int] = mapped_column(primary_key=True)
    credit_id: Mapped[int] = mapped_column(ForeignKey("credit_requests.id"))
    type: Mapped[str] = mapped_column(String(60), default="otro")
    message: Mapped[str] = mapped_column(Text)
    recipients: Mapped[str] = mapped_column(String(80), default="equipo_creditos")
    email_to: Mapped[str | None] = mapped_column(String(240))
    status: Mapped[AlertStatus] = mapped_column(String(30), default=AlertStatus.pendiente)
    scheduled_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime)
    email_sent: Mapped[bool] = mapped_column(Boolean, default=False)
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime)
    email_error: Mapped[str | None] = mapped_column(Text)
    error_message: Mapped[str | None] = mapped_column(Text)

    credit: Mapped[CreditRequest] = relationship(back_populates="alerts")


class CreditHistory(Base):
    __tablename__ = "credit_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    credit_id: Mapped[int] = mapped_column(ForeignKey("credit_requests.id"))
    actor: Mapped[str] = mapped_column(String(120), default="Sistema")
    action: Mapped[str] = mapped_column(String(120))
    detail: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    credit: Mapped[CreditRequest] = relationship(back_populates="history")


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    credit_id: Mapped[int | None] = mapped_column(ForeignKey("credit_requests.id"), nullable=True)
    subject: Mapped[str] = mapped_column(String(160))
    message: Mapped[str] = mapped_column(Text)
    read_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    sender: Mapped[User] = relationship(foreign_keys=[sender_id])
    recipient: Mapped[User] = relationship(foreign_keys=[recipient_id])
    credit: Mapped[CreditRequest | None] = relationship()


class Message(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    recipient_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    content: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    sender: Mapped[User] = relationship(foreign_keys=[sender_id], backref="sent_messages")
    recipient: Mapped[User] = relationship(foreign_keys=[recipient_id], backref="received_messages")
