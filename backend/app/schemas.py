from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field


class StageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    sequence: int
    max_hours: int | None = None
    folded: bool


class BankRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    sequence: int
    active: bool
    is_movilize: bool
    requires_ctl: bool
    requires_vehicle_history: bool
    requires_owner_history: bool


class CreditRequestBase(BaseModel):
    odoo_order_ref: str | None = Field(None, max_length=100)
    advisor_name: str | None = Field(None, max_length=255)
    showroom: str | None = Field(None, max_length=255)
    business_type: str | None = Field(None, max_length=100)
    document_type: str | None = Field(None, max_length=50)
    document_number: str | None = Field(None, max_length=50)
    customer_name: str = Field(min_length=2, max_length=255)
    phone: str | None = Field(None, max_length=20)
    plate: str | None = Field(None, max_length=20)
    vin: str | None = Field(None, max_length=17)
    brand: str | None = Field(None, max_length=100)
    line: str | None = Field(None, max_length=100)
    model: str | None = Field(None, max_length=100)
    sale_price: float = 0
    down_payment: float = 0
    proforma_invoice_ref: str | None = Field(None, max_length=100)
    final_invoice_ref: str | None = Field(None, max_length=100)
    viability_bank_id: int | None = None
    selected_bank_id: int | None = None
    disbursement_bank_id: int | None = None
    approval_conditions: str | None = None
    observations: str | None = None
    rejection_reason: str | None = None
    ok_runt: bool = False
    ok_runt_at: datetime | None = None
    runt_observation: str | None = None
    insured_ok: bool = False
    policy_issued: bool = False
    insurance_company: str | None = None
    policy_observation: str | None = None
    disbursed_value: float = 0
    ownership_card_issued: bool = False
    ownership_card_delivery_date: date | None = None


class CreditRequestCreate(CreditRequestBase):
    stage_id: int | None = None


class CreditRequestUpdate(CreditRequestBase):
    customer_name: str | None = None
    stage_id: int | None = None


class BankLineCreate(BaseModel):
    bank_id: int
    type: str = "estudio"
    status: str = "pendiente"
    filed_at: datetime | None = None
    answered_at: datetime | None = None
    approved_amount: float = 0
    disbursed_value: float = 0
    term: str | None = None
    rate: str | None = None
    conditions: str | None = None
    rejection_reason: str | None = None


class BankLineRead(BankLineCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bank: BankRead


class DocumentCreate(BaseModel):
    name: str
    type: str = "otro"
    file_name: str | None = None
    file_url: str | None = None
    observation: str | None = None


class DocumentRead(DocumentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    mime_type: str | None = None
    file_size: int | None = None


class AlertCreate(BaseModel):
    type: str = "otro"
    message: str
    recipients: str = "equipo_creditos"
    email_to: str | None = None
    scheduled_at: datetime | None = None


class AlertRead(AlertCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    sent_at: datetime | None = None
    email_sent: bool = False
    email_sent_at: datetime | None = None
    email_error: str | None = None
    error_message: str | None = None


class HistoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    actor: str
    action: str
    detail: str | None = None
    created_at: datetime


class CreditRequestRead(CreditRequestBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    reference: str
    stage_id: int
    stage_started_at: datetime
    created_at: datetime
    updated_at: datetime
    stage: StageRead
    viability_bank: BankRead | None = None
    selected_bank: BankRead | None = None
    disbursement_bank: BankRead | None = None
    bank_lines: list[BankLineRead] = []
    documents: list[DocumentRead] = []
    alerts: list[AlertRead] = []
    history: list[HistoryRead] = []

    @computed_field
    @property
    def financed_value(self) -> float:
        return float(self.sale_price or 0) - float(self.down_payment or 0)


class DashboardSummary(BaseModel):
    total_requests: int
    active_requests: int
    approved_requests: int
    disbursed_value: float
    by_stage: dict[str, int]
    by_selected_bank: dict[str, int]


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
    full_name: str
    role: str
    active: bool


class LoginRequest(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=6, max_length=255)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserRead


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    full_name: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=255)
    role: str = "user"


class UserPasswordUpdate(BaseModel):
    password: str = Field(min_length=6)


class NotificationCreate(BaseModel):
    recipient_id: int
    subject: str = Field(min_length=3)
    message: str = Field(min_length=3)
    credit_id: int | None = None


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    subject: str
    message: str
    credit_id: int | None = None
    read_at: datetime | None = None
    created_at: datetime
    sender: UserRead
    recipient: UserRead


class MessageCreate(BaseModel):
    recipient_id: int
    content: str = Field(min_length=1)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sender_id: int
    recipient_id: int
    content: str
    read: bool
    created_at: datetime
    sender_name: str | None = None

