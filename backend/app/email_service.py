import smtplib
from email.message import EmailMessage

from app.config import settings
from app.models import CreditAlert, CreditRequest


def send_alert_email(
    credit: CreditRequest,
    alert: CreditAlert,
    attachments: list[tuple[str, str, bytes]] | None = None,
) -> None:
    if not alert.email_to:
        return
    if not settings.smtp_host:
        raise RuntimeError("SMTP no configurado")

    subject = f"Alerta de credito - {alert.type}"
    body = f"""Alerta de credito

Solicitud: {credit.reference}
Cliente: {credit.customer_name}
Placa: {credit.plate or ""}
VIN: {credit.vin or ""}
Etapa actual: {credit.stage.name if credit.stage else ""}
Tipo de alerta: {alert.type}

Mensaje:
{alert.message}
"""

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.smtp_from
    message["To"] = alert.email_to
    message.set_content(body)

    for filename, content_type, data in attachments or []:
        maintype, _, subtype = (content_type or "application/octet-stream").partition("/")
        message.add_attachment(
            data,
            maintype=maintype or "application",
            subtype=subtype or "octet-stream",
            filename=filename,
        )

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        if settings.smtp_use_tls:
            smtp.starttls()
        if settings.smtp_user and settings.smtp_password:
            smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(message)
