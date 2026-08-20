import base64
import json
from urllib import error, parse, request

from app.config import settings
from app.models import CreditAlert, CreditRequest

GRAPH_SCOPE = "https://graph.microsoft.com/.default"
GRAPH_SENDMAIL_URL = "https://graph.microsoft.com/v1.0/users/{mail_from}/sendMail"
MAX_SIMPLE_ATTACHMENT_BYTES = 3 * 1024 * 1024


def _require_graph_config() -> None:
    missing = [
        name
        for name, value in {
            "GRAPH_TENANT_ID": settings.graph_tenant_id,
            "GRAPH_CLIENT_ID": settings.graph_client_id,
            "GRAPH_CLIENT_SECRET": settings.graph_client_secret,
            "GRAPH_MAIL_FROM": settings.graph_mail_from,
        }.items()
        if not value
    ]
    if missing:
        raise RuntimeError(f"Microsoft Graph no configurado: faltan {', '.join(missing)}")


def _post_json(url: str, payload: dict, headers: dict[str, str]) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = request.Request(url, data=data, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=30) as response:
            body = response.read()
            if not body:
                return {}
            return json.loads(body.decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Microsoft Graph respondio {exc.code}: {detail}") from exc


def _post_form(url: str, payload: dict[str, str]) -> dict:
    data = parse.urlencode(payload).encode("utf-8")
    req = request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Microsoft identity respondio {exc.code}: {detail}") from exc


def _get_graph_access_token() -> str:
    _require_graph_config()
    token_url = f"https://login.microsoftonline.com/{settings.graph_tenant_id}/oauth2/v2.0/token"
    response = _post_form(
        token_url,
        {
            "client_id": settings.graph_client_id or "",
            "client_secret": settings.graph_client_secret or "",
            "scope": GRAPH_SCOPE,
            "grant_type": "client_credentials",
        },
    )
    access_token = response.get("access_token")
    if not access_token:
        raise RuntimeError("Microsoft identity no devolvio access_token")
    return access_token


def _email_addresses(value: str) -> list[dict]:
    addresses = [item.strip() for item in value.replace(";", ",").split(",")]
    return [
        {"emailAddress": {"address": address}}
        for address in addresses
        if address
    ]


def _build_message(
    credit: CreditRequest,
    alert: CreditAlert,
    attachments: list[tuple[str, str, bytes]] | None = None,
) -> dict:
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
    message = {
        "subject": f"Alerta de credito - {alert.type}",
        "body": {
            "contentType": "Text",
            "content": body,
        },
        "toRecipients": _email_addresses(alert.email_to or ""),
    }
    graph_attachments = []
    for filename, content_type, data in attachments or []:
        if len(data) >= MAX_SIMPLE_ATTACHMENT_BYTES:
            raise RuntimeError(
                f"El adjunto {filename} supera 3 MB. "
                "Microsoft Graph requiere upload session para adjuntos grandes."
            )
        graph_attachments.append(
            {
                "@odata.type": "#microsoft.graph.fileAttachment",
                "name": filename,
                "contentType": content_type or "application/octet-stream",
                "contentBytes": base64.b64encode(data).decode("ascii"),
            }
        )
    if graph_attachments:
        message["attachments"] = graph_attachments
    return message


def send_alert_email(
    credit: CreditRequest,
    alert: CreditAlert,
    attachments: list[tuple[str, str, bytes]] | None = None,
) -> None:
    if not alert.email_to:
        return
    token = _get_graph_access_token()
    message = _build_message(credit, alert, attachments)
    if not message["toRecipients"]:
        raise RuntimeError("No hay destinatarios validos para el correo")

    mail_from = parse.quote(settings.graph_mail_from, safe="")
    _post_json(
        GRAPH_SENDMAIL_URL.format(mail_from=mail_from),
        {
            "message": message,
            "saveToSentItems": settings.graph_save_to_sent_items,
        },
        {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
