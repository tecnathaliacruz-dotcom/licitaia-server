# LicitaIA — Servidor ChileCompra
### People on Technology | LED VIP | Lizeth Cruz Barrera

---

## ¿Qué hace este servidor?
Actúa como intermediario entre tu app (navegador) y la API oficial de ChileCompra.
El navegador no puede llamar directamente a ChileCompra por restricciones de seguridad (CORS),
pero este servidor sí puede hacerlo y te devuelve los datos.

---

## PASO A PASO — Subir a Railway (GRATIS)

### 1. Crear cuenta en GitHub
- Ve a https://github.com y crea una cuenta gratuita

### 2. Crear repositorio
- Clic en "New repository"
- Nombre: `licitaia-server`
- Público o privado (cualquiera sirve)
- Clic en "Create repository"

### 3. Subir los archivos
Sube estos 4 archivos al repositorio:
- server.py
- requirements.txt
- Procfile
- nixpacks.toml

Para subir: clic en "Add file" → "Upload files" → arrastrá los 4 archivos → "Commit changes"

### 4. Crear cuenta en Railway
- Ve a https://railway.app
- Clic en "Start a New Project"
- Iniciá sesión con tu cuenta de GitHub

### 5. Desplegar el servidor
- Clic en "Deploy from GitHub repo"
- Seleccioná "licitaia-server"
- Railway detecta automáticamente que es Python y lo instala
- En 2-3 minutos tenés tu servidor funcionando

### 6. Obtener tu URL
- En Railway, ve a tu proyecto → Settings → Domains
- Clic en "Generate Domain"
- Te da una URL tipo: https://licitaia-server-production.up.railway.app

### 7. Actualizar la app
- Copiá esa URL
- Dásela a Claude y él actualiza la app para que use tu servidor real

---

## Rutas disponibles del servidor

| Ruta | Descripción | Ejemplo |
|------|-------------|---------|
| GET / | Estado del servidor | / |
| GET /licitaciones/fecha | Por fecha publicación | /licitaciones/fecha?fecha=13052026 |
| GET /licitaciones/codigo | Por código exacto | /licitaciones/codigo?codigo=1509-5-L114 |
| GET /licitaciones/estado | Por estado | /licitaciones/estado?estado=7 |
| GET /licitaciones/organismo | Por organismo | /licitaciones/organismo?codigo=694 |

---

## Estados de licitaciones
- 5 = Publicada
- 6 = Cerrada  
- 7 = Desierta (sin oferentes) ⚡ — TU MAYOR OPORTUNIDAD
- 8 = Adjudicada

---

## Ticket API
El ticket ya está incluido en el servidor: 33588502-90E2-4B19-9FCA-0960F65D93CC

---

## Costo
Railway tiene plan gratuito con $5 USD de crédito mensual.
Este servidor consume muy poco, debería ser gratuito indefinidamente.
