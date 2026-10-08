# LicitaIA v2 — App + Servidor ChileCompra
### People on Technology | LED VIP | Lizeth Cruz Barrera

El servidor (Render, plan gratis; también funciona en Railway) ahora entrega **la app completa** (abre tu URL de Railway en el navegador)
y hace de intermediario con la API oficial de Mercado Público.

## Qué trae la app
- **Buscar**: licitaciones activas/publicadas/cerradas/adjudicadas por palabras clave, con puntaje de oportunidad (0–100), semáforo de cierre, filtros por región, puntaje y orden, y exportación a CSV (abre directo en Excel).
- **Desiertas**: licitaciones sin oferentes, que suelen volver a publicarse o pasar a trato directo.
- **Detalle**: organismo, montos, fechas, contacto, ítems, desglose del puntaje.
- **Calculadora de margen**: costos por ítem + flete + otros + garantía + margen → precio neto, IVA, total, y comparación con el monto estimado.
- **Propuesta con IA** (si configuras la clave de Anthropic) o **"Copiar prompt para Claude"**; descarga en .doc.
- **Guardadas**: marca con ★, seguimiento por estado (Evaluando → Oferta enviada → Ganada…) y notas.
- **Órdenes de compra**: qué compran los organismos, a quién y a qué precio; búsqueda de proveedor por RUT.
- **Perfiles** (LED VIP y People on Technology ya creados) y **alertas** de licitaciones nuevas.

## Hosting en Render (gratis)
Render lee `render.yaml`: New → Blueprint → elegir este repositorio → pegar `MP_TICKET` cuando lo pida.
En el plan gratis la app se duerme tras 15 min sin uso y tarda ~50 s en despertar.

## Cómo actualizar en Railway (alternativa pagada)

### 1. Variables en Railway (ANTES de subir los archivos)
Railway → tu proyecto → servicio *licitaia-server* → **Variables** → New Variable:
| Variable | Valor | ¿Obligatoria? |
|---|---|---|
| `MP_TICKET` | tu ticket de la API de Mercado Público | Sí |
| `ANTHROPIC_API_KEY` | clave de console.anthropic.com | Opcional (para redactar propuestas con IA) |

### 2. Subir los archivos a GitHub
En github.com/tecnathaliacruz-dotcom/licitaia-server → **Add file → Upload files** y arrastra:
- `server.py`, `requirements.txt`, `Procfile`, `nixpacks.toml`, `README.md`
- `index.html` (la app)

→ **Commit changes**. Railway redespliega solo en 2–3 minutos.

### 3. Abrir la app
Entra a tu URL de Railway (Settings → Domains), por ejemplo
`https://licitaia-server-production.up.railway.app`. Arriba a la derecha debe decir **Conectado**.

## Rutas del servidor
| Ruta | Descripción |
|---|---|
| `GET /` | La app |
| `GET /api/status` | Estado, ticket e IA configurados |
| `GET /api/buscar?q=coffee,led&estado=activas&fecha=ddmmaaaa&detalle=25` | Búsqueda con filtro y detalle |
| `GET /api/detalle/<codigo>` | Detalle de una licitación |
| `GET /api/ordenes?fecha=&organismo=&proveedor=&codigo=` | Órdenes de compra |
| `GET /api/empresa?rut=76.123.456-7` | Código de proveedor por RUT |
| `POST /api/propuesta` | Propuesta con IA |
| `GET /licitaciones/fecha · /codigo · /estado · /organismo · /proveedor` | Rutas originales (siguen funcionando) |

Estados: 5 Publicada · 6 Cerrada · 7 Desierta · 8 Adjudicada · 18 Revocada · 19 Suspendida
(acepta el número o el texto: `estado=7` o `estado=desierta`).

## Notas
- El ticket ya **no** va en el código: el repositorio es público y cualquiera podía usarlo.
- El servidor guarda en caché las respuestas (15 min listas, 6 h detalles) y hace las llamadas de a una, porque la API rechaza peticiones simultáneas.
- Perfiles, guardadas y cálculos se guardan en tu navegador (si cambias de computador, no se traspasan).
