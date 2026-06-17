# 🚀 Guía de Deployment en Hostinger VPS

## Información de tu servidor

- **IP:** 2.24.194.52
- **Puerto SSH:** 24
- **Usuario:** root
- **Sistema:** Ubuntu 24.04 LTS
- **Recursos:** 2 CPU, 8GB RAM, 100GB SSD

---

## Paso 1: Conectarse por SSH

### En Windows (PowerShell):
```powershell
ssh -p 24 root@2.24.194.52
```

### En Mac/Linux:
```bash
ssh -p 24 root@2.24.194.52
```

Ingresa la contraseña que configuraste en Hostinger cuando se te pida.

---

## Paso 2: Clonar el repositorio

Una vez dentro del servidor:

```bash
# Ir a la carpeta home
cd /root

# Clonar tu repositorio (cambia la URL por la tuya)
git clone https://github.com/tu-usuario/creditos.git
cd creditos
```

---

## Paso 3: Configurar variables de entorno

```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar variables
nano .env
```

**Edita estos valores:**
```
DB_USER=postgres
DB_PASSWORD=pon_una_password_fuerte_aqui
DB_NAME=creditos
JWT_SECRET=pon_un_string_largo_y_aleatorio_aqui
```

Para salvar en nano:
- Presiona `Ctrl + X`
- Presiona `Y` (yes)
- Presiona `Enter`

---

## Paso 4: Dar permisos y ejecutar deploy

```bash
# Dar permisos ejecutables
chmod +x deploy.sh

# Ejecutar script de deployment (instala Docker automáticamente)
bash deploy.sh
```

El script hará todo automáticamente:
- ✅ Actualiza el sistema
- ✅ Instala Docker y Docker Compose
- ✅ Descarga el código
- ✅ Configura variables
- ✅ Inicia los contenedores

---

## Paso 5: Verificar que todo funciona

```bash
# Ver estado de contenedores
docker-compose -f docker-compose.prod.yml ps

# Ver logs del backend
docker-compose -f docker-compose.prod.yml logs -f creditos_backend

# Ver logs del frontend
docker-compose -f docker-compose.prod.yml logs -f creditos_frontend
```

---

## Acceder a la aplicación

Una vez que todo esté corriendo:

- **Frontend:** http://2.24.194.52:4210
- **Backend:** http://2.24.194.52:8010
- **API Docs:** http://2.24.194.52:8010/docs

---

## Comandos útiles

```bash
# Detener todos los contenedores
docker-compose -f docker-compose.prod.yml down

# Reiniciar
docker-compose -f docker-compose.prod.yml restart

# Ver logs en tiempo real
docker-compose -f docker-compose.prod.yml logs -f

# Actualizar código y redeploy
cd /root/creditos
git pull origin main
docker-compose -f docker-compose.prod.yml up -d --build
```

---

## Configurar Dominio y SSL (Opcional)

Si tienes un dominio:

1. **Apunta tu dominio a la IP:**
   - En tu proveedor de dominio, crea un registro A que apunte a `2.24.194.52`

2. **Espera propagación del DNS** (5-30 minutos)

3. **Instalar Let's Encrypt SSL:**
```bash
apt-get install certbot python3-certbot-nginx -y

# Generar certificado
certbot certonly --standalone -d tu-dominio.com

# El certificado estará en: /etc/letsencrypt/live/tu-dominio.com/
```

4. **Actualizar nginx/default.conf** con la ruta del certificado

---

## Troubleshooting

### Los contenedores no inician
```bash
# Ver logs detallados
docker-compose -f docker-compose.prod.yml logs --tail=50

# Verificar que el puerto SSH no sea el problema
telnet 2.24.194.52 8010
```

### Base de datos no conecta
```bash
# Verificar que DB esté sana
docker-compose -f docker-compose.prod.yml ps creditos_db

# Ver logs de la BD
docker-compose -f docker-compose.prod.yml logs creditos_db
```

### Frontend no carga
```bash
# Verificar que nginx esté corriendo
docker-compose -f docker-compose.prod.yml ps creditos_nginx

# Ver logs
docker-compose -f docker-compose.prod.yml logs creditos_nginx
```

---

## Soporte

Si tienes problemas, verifica:
1. SSH está accesible
2. Docker está instalado: `docker --version`
3. Las variables de .env son correctas
4. Hay suficiente espacio en disco: `df -h`
5. Los logs no tienen errores: `docker-compose logs -f`

¡Listo! Tu aplicación está en producción 🎉
