from datetime import date, datetime, time
from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from fastapi.responses import Response, StreamingResponse
from io import BytesIO
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app import models, schemas
from app.database import get_db
from app.email_service import send_alert_email
from app.security import get_current_user, require_admin

router = APIRouter(prefix="/credits", tags=["credits"])


def _next_reference(db: Session) -> str:
    count = db.query(models.CreditRequest).count() + 1
    return f"CRE-{count:05d}"


def _default_stage(db: Session) -> models.Stage:
    stage = db.query(models.Stage).filter(models.Stage.code == "viabilidad").first()
    if not stage:
        raise HTTPException(status_code=500, detail="No existe la etapa Viabilidad")
    return stage


def _credit_query(db: Session):
    return (
        db.query(models.CreditRequest)
        .options(
            joinedload(models.CreditRequest.stage),
            joinedload(models.CreditRequest.viability_bank),
            joinedload(models.CreditRequest.selected_bank),
            joinedload(models.CreditRequest.disbursement_bank),
            joinedload(models.CreditRequest.bank_lines).joinedload(models.CreditBankLine.bank),
            joinedload(models.CreditRequest.documents),
            joinedload(models.CreditRequest.alerts),
            joinedload(models.CreditRequest.history),
        )
    )


def _add_history(db: Session, credit_id: int, action: str, detail: str | None = None, actor: str = "Sistema") -> None:
    db.add(models.CreditHistory(credit_id=credit_id, actor=actor, action=action, detail=detail))


@router.get("", response_model=list[schemas.CreditRequestRead])
def list_credits(
    search: str | None = Query(default=None),
    stage_code: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(get_current_user),
):
    query = _credit_query(db)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                models.CreditRequest.reference.ilike(like),
                models.CreditRequest.customer_name.ilike(like),
                models.CreditRequest.document_number.ilike(like),
                models.CreditRequest.plate.ilike(like),
                models.CreditRequest.vin.ilike(like),
            )
        )
    if stage_code:
        query = query.join(models.Stage).filter(models.Stage.code == stage_code)
    return query.order_by(models.CreditRequest.created_at.desc()).all()


@router.post("", response_model=schemas.CreditRequestRead, status_code=status.HTTP_201_CREATED)
def create_credit(
    payload: schemas.CreditRequestCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    stage_id = payload.stage_id or _default_stage(db).id
    values = payload.model_dump(exclude={"stage_id"})
    credit = models.CreditRequest(reference=_next_reference(db), stage_id=stage_id, **values)
    db.add(credit)
    db.flush()
    _add_history(db, credit.id, "Credito creado", "Registro inicial de solicitud", current_user.full_name)
    db.commit()
    return _credit_query(db).filter(models.CreditRequest.id == credit.id).one()


@router.get("/reports/summary", response_model=schemas.DashboardSummary)
def summary(db: Session = Depends(get_db), _current_user: models.User = Depends(get_current_user)):
    total = db.query(models.CreditRequest).count()
    active = (
        db.query(models.CreditRequest)
        .join(models.Stage)
        .filter(models.Stage.code.notin_(["legalizacion", "desasignado"]))
        .count()
    )
    approved = db.query(models.CreditRequest).join(models.Stage).filter(models.Stage.code == "aprobado").count()
    disbursed_value = db.query(func.coalesce(func.sum(models.CreditRequest.disbursed_value), 0)).scalar() or 0

    by_stage_rows = (
        db.query(models.Stage.name, func.count(models.CreditRequest.id))
        .join(models.CreditRequest, models.CreditRequest.stage_id == models.Stage.id, isouter=True)
        .group_by(models.Stage.name, models.Stage.sequence)
        .order_by(models.Stage.sequence)
        .all()
    )
    by_bank_rows = (
        db.query(models.Bank.name, func.count(models.CreditRequest.id))
        .join(models.CreditRequest, models.CreditRequest.selected_bank_id == models.Bank.id)
        .group_by(models.Bank.name)
        .all()
    )
    return schemas.DashboardSummary(
        total_requests=total,
        active_requests=active,
        approved_requests=approved,
        disbursed_value=float(disbursed_value),
        by_stage={name: count for name, count in by_stage_rows},
        by_selected_bank={name: count for name, count in by_bank_rows},
    )


@router.get("/reports/detail", response_model=list[schemas.CreditRequestRead])
def detail_report(
    search: str | None = Query(default=None),
    stage_id: int | None = Query(default=None),
    bank_id: int | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(get_current_user),
):
    query = _credit_query(db)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                models.CreditRequest.reference.ilike(like),
                models.CreditRequest.customer_name.ilike(like),
                models.CreditRequest.document_number.ilike(like),
                models.CreditRequest.plate.ilike(like),
                models.CreditRequest.vin.ilike(like),
                models.CreditRequest.advisor_name.ilike(like),
                models.CreditRequest.showroom.ilike(like),
            )
        )
    if stage_id:
        query = query.filter(models.CreditRequest.stage_id == stage_id)
    if bank_id:
        query = query.filter(
            or_(
                models.CreditRequest.viability_bank_id == bank_id,
                models.CreditRequest.selected_bank_id == bank_id,
                models.CreditRequest.disbursement_bank_id == bank_id,
                models.CreditRequest.bank_lines.any(models.CreditBankLine.bank_id == bank_id),
            )
        )
    if date_from:
        query = query.filter(models.CreditRequest.created_at >= datetime.combine(date_from, time.min))
    if date_to:
        query = query.filter(models.CreditRequest.created_at <= datetime.combine(date_to, time.max))
    return query.order_by(models.CreditRequest.created_at.desc()).all()


def _apply_report_filters(query, search, stage_id, bank_id, date_from, date_to):
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                models.CreditRequest.reference.ilike(like),
                models.CreditRequest.customer_name.ilike(like),
                models.CreditRequest.document_number.ilike(like),
                models.CreditRequest.plate.ilike(like),
                models.CreditRequest.vin.ilike(like),
                models.CreditRequest.advisor_name.ilike(like),
                models.CreditRequest.showroom.ilike(like),
            )
        )
    if stage_id:
        query = query.filter(models.CreditRequest.stage_id == stage_id)
    if bank_id:
        query = query.filter(
            or_(
                models.CreditRequest.viability_bank_id == bank_id,
                models.CreditRequest.selected_bank_id == bank_id,
                models.CreditRequest.disbursement_bank_id == bank_id,
                models.CreditRequest.bank_lines.any(models.CreditBankLine.bank_id == bank_id),
            )
        )
    if date_from:
        query = query.filter(models.CreditRequest.created_at >= datetime.combine(date_from, time.min))
    if date_to:
        query = query.filter(models.CreditRequest.created_at <= datetime.combine(date_to, time.max))
    return query


def _join_lines(values: list[str]) -> str:
    return "\n".join(value for value in values if value)


@router.get("/reports/excel")
def excel_report(
    search: str | None = Query(default=None),
    stage_id: int | None = Query(default=None),
    bank_id: int | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(get_current_user),
):
    query = _apply_report_filters(_credit_query(db), search, stage_id, bank_id, date_from, date_to)
    credits = query.order_by(models.CreditRequest.created_at.desc()).all()

    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "Solicitudes"
    headers = [
        "Referencia",
        "Cliente",
        "Documento",
        "Celular",
        "Placa",
        "VIN",
        "Vehiculo",
        "Asesor",
        "Vitrina",
        "Tipo negocio",
        "Etapa actual",
        "Fecha creacion",
        "Inicio etapa actual",
        "Valor venta",
        "Cuota inicial",
        "Valor financiado",
        "Valor desembolsado",
        "Banco viabilidad",
        "Banco seleccionado",
        "Banco desembolso",
        "Motivo rechazo",
        "OK RUNT",
        "Observacion RUNT",
        "Asegurado OK",
        "Poliza emitida",
        "Entidad aseguradora",
        "Observacion poliza",
        "Tarjeta propiedad emitida",
        "Fecha entrega tarjeta",
        "Bancos / radicaciones",
        "Documentos",
        "Alertas",
        "Historial / etapas",
        "Observaciones",
    ]
    sheet.append(headers)
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1967D2")

    for credit in credits:
        bank_lines = _join_lines([
            f"{line.bank.name} | {line.type} | {line.status} | radicado: {line.filed_at or '-'} | respuesta: {line.answered_at or '-'} | condiciones: {line.conditions or '-'}"
            for line in credit.bank_lines
        ])
        documents = _join_lines([
            f"{document.name} | {document.type} | {document.file_name or '-'} | {document.file_size or 0} bytes"
            for document in credit.documents
        ])
        alerts = _join_lines([
            f"{alert.type} | {alert.status} | {alert.message} | correo: {alert.email_to or '-'} | enviado: {'si' if alert.email_sent else 'no'}"
            for alert in credit.alerts
        ])
        history = _join_lines([
            f"{item.created_at} | {item.actor} | {item.action} | {item.detail or '-'}"
            for item in credit.history
        ])
        sheet.append([
            credit.reference,
            credit.customer_name,
            f"{credit.document_type or ''} {credit.document_number or ''}".strip(),
            credit.phone,
            credit.plate,
            credit.vin,
            f"{credit.brand or ''} {credit.line or ''} {credit.model or ''}".strip(),
            credit.advisor_name,
            credit.showroom,
            credit.business_type,
            credit.stage.name if credit.stage else "",
            credit.created_at,
            credit.stage_started_at,
            float(credit.sale_price or 0),
            float(credit.down_payment or 0),
            credit.financed_value,
            float(credit.disbursed_value or 0),
            credit.viability_bank.name if credit.viability_bank else "",
            credit.selected_bank.name if credit.selected_bank else "",
            credit.disbursement_bank.name if credit.disbursement_bank else "",
            credit.rejection_reason,
            "Si" if credit.ok_runt else "No",
            credit.runt_observation,
            "Si" if credit.insured_ok else "No",
            "Si" if credit.policy_issued else "No",
            credit.insurance_company,
            credit.policy_observation,
            "Si" if credit.ownership_card_issued else "No",
            credit.ownership_card_delivery_date,
            bank_lines,
            documents,
            alerts,
            history,
            credit.observations,
        ])

    for column_cells in sheet.columns:
        length = max(len(str(cell.value or "")) for cell in column_cells)
        sheet.column_dimensions[column_cells[0].column_letter].width = min(max(length + 2, 12), 60)
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = cell.alignment.copy(wrap_text=True, vertical="top")

    output = BytesIO()
    workbook.save(output)
    output.seek(0)
    filename = f"reporte_creditos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{credit_id}", response_model=schemas.CreditRequestRead)
def get_credit(credit_id: int, db: Session = Depends(get_db), _current_user: models.User = Depends(get_current_user)):
    credit = _credit_query(db).filter(models.CreditRequest.id == credit_id).first()
    if not credit:
        raise HTTPException(status_code=404, detail="Credito no encontrado")
    return credit


@router.patch("/{credit_id}", response_model=schemas.CreditRequestRead)
def update_credit(
    credit_id: int,
    payload: schemas.CreditRequestUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    credit = db.get(models.CreditRequest, credit_id)
    if not credit:
        raise HTTPException(status_code=404, detail="Credito no encontrado")

    values = payload.model_dump(exclude_unset=True)
    old_stage_id = credit.stage_id
    for key, value in values.items():
        setattr(credit, key, value)
    if "stage_id" in values and values["stage_id"] != old_stage_id:
        credit.stage_started_at = datetime.utcnow()
        _add_history(
            db,
            credit.id,
            "Cambio de etapa",
            f"Etapa anterior ID {old_stage_id}, nueva ID {values['stage_id']}",
            current_user.full_name,
        )
    else:
        _add_history(db, credit.id, "Credito actualizado", ", ".join(values.keys()), current_user.full_name)
    db.commit()
    return _credit_query(db).filter(models.CreditRequest.id == credit.id).one()


@router.delete("/{credit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_credit(
    credit_id: int,
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(require_admin),
):
    credit = db.get(models.CreditRequest, credit_id)
    if not credit:
        raise HTTPException(status_code=404, detail="Credito no encontrado")

    db.query(models.Notification).filter(models.Notification.credit_id == credit_id).update(
        {models.Notification.credit_id: None},
        synchronize_session=False,
    )
    db.delete(credit)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{credit_id}/bank-lines", response_model=schemas.BankLineRead, status_code=status.HTTP_201_CREATED)
def add_bank_line(
    credit_id: int,
    payload: schemas.BankLineCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not db.get(models.CreditRequest, credit_id):
        raise HTTPException(status_code=404, detail="Credito no encontrado")
    line = models.CreditBankLine(credit_id=credit_id, **payload.model_dump())
    db.add(line)
    db.flush()
    _add_history(db, credit_id, "Banco agregado", f"Banco ID {payload.bank_id} en estado {payload.status}", current_user.full_name)
    db.commit()
    db.refresh(line)
    return line


@router.post("/{credit_id}/documents", response_model=schemas.DocumentRead, status_code=status.HTTP_201_CREATED)
def add_document(
    credit_id: int,
    payload: schemas.DocumentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not db.get(models.CreditRequest, credit_id):
        raise HTTPException(status_code=404, detail="Credito no encontrado")
    document = models.CreditDocument(credit_id=credit_id, **payload.model_dump())
    db.add(document)
    db.flush()
    _add_history(db, credit_id, "Documento agregado", payload.name, current_user.full_name)
    db.commit()
    db.refresh(document)
    return document


@router.post("/{credit_id}/documents/upload", response_model=schemas.DocumentRead, status_code=status.HTTP_201_CREATED)
def upload_document(
    credit_id: int,
    name: str = Form(...),
    type: str = Form("otro"),
    observation: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not db.get(models.CreditRequest, credit_id):
        raise HTTPException(status_code=404, detail="Credito no encontrado")

    file_data = file.file.read()
    safe_name = file.filename or "documento"

    document = models.CreditDocument(
        credit_id=credit_id,
        name=name,
        type=type,
        file_name=safe_name,
        file_url=f"/api/credits/{credit_id}/documents/download",
        mime_type=file.content_type or "application/octet-stream",
        file_size=len(file_data),
        file_data=file_data,
        observation=observation,
    )
    db.add(document)
    db.flush()
    _add_history(db, credit_id, "Documento cargado", safe_name, current_user.full_name)
    db.commit()
    db.refresh(document)
    return document


@router.get("/{credit_id}/documents/{document_id}/download")
def download_document(
    credit_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    _current_user: models.User = Depends(get_current_user),
):
    document = (
        db.query(models.CreditDocument)
        .filter(models.CreditDocument.credit_id == credit_id, models.CreditDocument.id == document_id)
        .first()
    )
    if not document or not document.file_data:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    filename = document.file_name or document.name
    return Response(
        content=document.file_data,
        media_type=document.mime_type or "application/octet-stream",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


@router.delete("/{credit_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    credit_id: int,
    document_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(require_admin),
):
    document = (
        db.query(models.CreditDocument)
        .filter(models.CreditDocument.credit_id == credit_id, models.CreditDocument.id == document_id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Documento no encontrado")

    detail = document.file_name or document.name
    db.delete(document)
    _add_history(db, credit_id, "Documento eliminado", detail, current_user.full_name)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{credit_id}/alerts", response_model=schemas.AlertRead, status_code=status.HTTP_201_CREATED)
def add_alert(
    credit_id: int,
    type: str = Form("otro"),
    message: str = Form(...),
    recipients: str = Form("equipo_creditos"),
    email_to: str | None = Form(None),
    selected_document_ids: list[int] = Form([]),
    file: UploadFile | None = File(None),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    if not db.get(models.CreditRequest, credit_id):
        raise HTTPException(status_code=404, detail="Credito no encontrado")
    alert = models.CreditAlert(
        credit_id=credit_id,
        type=type,
        message=message,
        recipients=recipients,
        email_to=email_to,
        scheduled_at=datetime.utcnow(),
    )
    db.add(alert)
    db.flush()
    attachments: list[tuple[str, str, bytes]] = []
    attached_names: list[str] = []

    if selected_document_ids:
        documents = (
            db.query(models.CreditDocument)
            .filter(
                models.CreditDocument.credit_id == credit_id,
                models.CreditDocument.id.in_(selected_document_ids),
                models.CreditDocument.file_data.isnot(None),
            )
            .all()
        )
        for document in documents:
            filename = document.file_name or document.name
            attachments.append((filename, document.mime_type or "application/octet-stream", document.file_data or b""))
            attached_names.append(filename)

    if file:
        file_data = file.file.read()
        safe_name = file.filename or "adjunto_alerta"
        attachments.append((safe_name, file.content_type or "application/octet-stream", file_data))
        attached_names.append(safe_name)
        document = models.CreditDocument(
            credit_id=credit_id,
            name=safe_name,
            type="alerta",
            file_name=safe_name,
            file_url=f"/api/credits/{credit_id}/documents/download",
            mime_type=file.content_type or "application/octet-stream",
            file_size=len(file_data),
            file_data=file_data,
            observation=f"Adjunto enviado en alerta {type}",
        )
        db.add(document)
        db.flush()
        _add_history(db, credit_id, "Documento cargado", safe_name, current_user.full_name)

    if alert.email_to:
        credit = _credit_query(db).filter(models.CreditRequest.id == credit_id).one()
        try:
            send_alert_email(credit, alert, attachments)
            alert.status = models.AlertStatus.enviado
            alert.email_sent = True
            alert.email_sent_at = datetime.utcnow()
            alert.sent_at = alert.email_sent_at
            alert.email_error = None
            alert.error_message = None
        except Exception as error:
            alert.status = models.AlertStatus.fallido
            alert.email_sent = False
            alert.email_error = str(error)
            alert.error_message = str(error)
    detail = message
    if attached_names:
        detail = f"{message} | Adjuntos: {', '.join(attached_names)}"
    _add_history(db, credit_id, "Alerta creada", detail, current_user.full_name)
    db.commit()
    db.refresh(alert)
    return alert
