# Aplicativo de Creditos

MVP independiente para el area de creditos vehiculares. Esta version no depende de Odoo para operar; permite crear solicitudes manuales minimas y gestionar etapas, bancos, documentos, alertas e historial.

## Puertos

- Frontend Angular: `http://localhost:4210`
- Backend FastAPI: `http://localhost:8010`
- Swagger/OpenAPI: `http://localhost:8010/docs`
- PostgreSQL del aplicativo: `localhost:5440`

Se eligieron estos puertos para no chocar con Odoo local `8069`, otros servicios en `8000/8001` ni PostgreSQL locales `5432/5433/5434`.

## Arranque con Docker

```powershell
docker compose up --build
```

El backend crea las tablas automaticamente en desarrollo y carga datos iniciales:

- etapas del flujo de creditos
- bancos base
- requisitos especiales de Movilize y Occidente

## Estructura

```txt
backend/
  app/
    models.py
    schemas.py
    routers/
    seed.py
frontend/
  src/app/
docker-compose.yml
```

## Flujo inicial

1. Crear una solicitud con cliente, placa/VIN, asesor, vitrina y valores.
2. Moverla por etapas desde el panel derecho.
3. Agregar bancos de viabilidad, estudio, aprobacion, rechazo o desembolso.
4. Cargar documentos. Los archivos quedan guardados en PostgreSQL en la columna `file_data` de `credit_documents`.
5. Registrar alertas y observaciones.
6. Consultar metricas y tablero por etapa.

## Integracion futura con Odoo

La app queda lista para agregar despues una mini integracion de lectura:

- buscar por placa
- buscar por VIN
- buscar por numero de pedido
- precargar cliente, asesor, vitrina, valores y facturas

Mientras no exista esa integracion, el aplicativo opera con creacion manual minima o con un importador futuro desde Excel.

## Correos de alertas

Para enviar alertas por correo, configura Microsoft Graph API con OAuth 2.0 client credentials en un archivo `.env` basado en `.env.example`:

```txt
GRAPH_TENANT_ID=tenant-id-entregado-por-microsoft
GRAPH_CLIENT_ID=client-id-del-app-registration
GRAPH_CLIENT_SECRET=client-secret-del-app-registration
GRAPH_MAIL_FROM=creditos@carmaxcolombia.com.co
GRAPH_SAVE_TO_SENT_ITEMS=true
```

El App Registration debe tener permiso de Microsoft Graph `Mail.Send` de tipo `Application` con admin consent. Idealmente debe estar limitado al buzon `creditos@carmaxcolombia.com.co` desde Microsoft Entra/Exchange.

Los adjuntos enviados directamente por esta integracion deben ser menores a 3 MB. Para adjuntos mayores, Microsoft Graph requiere crear un borrador y usar upload session.

Si Microsoft Graph no esta configurado, la alerta se guarda igual y queda marcada como fallida con el detalle de configuracion faltante.
