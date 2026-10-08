"""
LicitaIA — Servidor ChileCompra (Mercado Público)
People on Technology | LED VIP | Lizeth Cruz Barrera

Sirve la app (static/index.html) y hace de intermediario con la API oficial
de Mercado Público. Variables de entorno (Railway → Variables):
  MP_TICKET          (obligatoria) ticket de la API de Mercado Público
  ANTHROPIC_API_KEY  (opcional) para redactar propuestas con IA
  ANTHROPIC_MODEL    (opcional) modelo a usar; por defecto claude-sonnet-4-5
"""
import os
import re
import time
import threading
import unicodedata
from datetime import datetime, timedelta

import requests
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__, static_folder=None)
CORS(app, origins="*", allow_headers="*", methods=["GET", "POST", "OPTIONS"])

TICKET = os.environ.get("MP_TICKET", "").strip()
BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico"
ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "").strip()
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5").strip()

# La API rechaza peticiones simultáneas con el mismo ticket → las serializamos.
_api_lock = threading.Lock()
_cache = {}
_cache_lock = threading.Lock()

# Estados: la app vieja enviaba números; la API espera texto.
ESTADOS = {
    "5": "publicada", "6": "cerrada", "7": "desierta", "8": "adjudicada",
    "18": "revocada", "19": "suspendida",
}
ESTADOS_TEXTO = {"activas", "publicada", "cerrada", "desierta", "adjudicada",
                 "revocada", "suspendida", "todos"}


def norm_estado(valor, defecto="activas"):
    v = (valor or "").strip().lower()
    if not v:
        return defecto
    if v in ESTADOS:
        return ESTADOS[v]
    return v if v in ESTADOS_TEXTO else defecto


def norm_fecha(valor):
    """Acepta ddmmaaaa, dd-mm-aaaa o aaaa-mm-dd y devuelve ddmmaaaa."""
    v = (valor or "").strip()
    if not v:
        return ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
        a, m, d = v.split("-")
        return f"{d}{m}{a}"
    return re.sub(r"\D", "", v)


def sin_tildes(texto):
    t = unicodedata.normalize("NFD", (texto or "").lower())
    return "".join(c for c in t if unicodedata.category(c) != "Mn")


def cache_get(key):
    with _cache_lock:
        item = _cache.get(key)
        if item and item[0] > time.time():
            return item[1]
        _cache.pop(key, None)
        return None


def cache_set(key, value, ttl):
    with _cache_lock:
        if len(_cache) > 3000:  # limpieza simple
            ahora = time.time()
            for k in [k for k, v in _cache.items() if v[0] <= ahora]:
                _cache.pop(k, None)
        _cache[key] = (time.time() + ttl, value)


def call_api(endpoint, params=None, ttl=600):
    """Llama a Mercado Público con caché y reintento ante 'peticiones simultáneas'."""
    if not TICKET:
        return {"error": "Falta la variable MP_TICKET en Railway", "Codigo": 500}
    params = {k: v for k, v in dict(params or {}).items() if v not in (None, "")}
    key = endpoint + "?" + "&".join(f"{k}={params[k]}" for k in sorted(params))
    hit = cache_get(key)
    if hit is not None:
        return hit
    params["ticket"] = TICKET
    data = None
    for intento in range(3):
        try:
            with _api_lock:
                r = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=25)
            data = r.json()
        except Exception as e:  # red, JSON inválido, etc.
            data = {"error": str(e), "Codigo": 500}
        # 10500 = peticiones simultáneas; esperar y reintentar
        if isinstance(data, dict) and str(data.get("Codigo")) == "10500":
            time.sleep(1.5 * (intento + 1))
            continue
        break
    if isinstance(data, dict) and "error" not in data and data.get("Codigo") is None:
        cache_set(key, data, ttl)
    return data


def detalle(codigo):
    data = call_api("licitaciones.json", {"codigo": codigo}, ttl=6 * 3600)
    lst = (data or {}).get("Listado") or []
    return lst[0] if lst else None


# ---------------------------------------------------------------- App web
@app.route("/")
def home():
    # index.html puede estar en la raíz del repo o en static/
    for carpeta in (BASE_DIR, os.path.join(BASE_DIR, "static")):
        if os.path.exists(os.path.join(carpeta, "index.html")):
            return send_from_directory(carpeta, "index.html")
    return jsonify({"status": "ok", "app": "LicitaIA", "aviso": "Falta index.html"})


@app.route("/api/status")
def status():
    return jsonify({
        "status": "ok", "app": "LicitaIA", "version": "2.0",
        "ticket_configurado": bool(TICKET),
        "ia_configurada": bool(ANTHROPIC_KEY),
    })


# ------------------------------------------------- Rutas originales (compatibles)
@app.route("/licitaciones/fecha")
def por_fecha():
    return jsonify(call_api("licitaciones.json", {
        "fecha": norm_fecha(request.args.get("fecha")),
        "estado": norm_estado(request.args.get("estado"), ""),
    }))


@app.route("/licitaciones/codigo")
def por_codigo():
    return jsonify(call_api("licitaciones.json", {"codigo": request.args.get("codigo", "").strip()}, ttl=6 * 3600))


@app.route("/licitaciones/estado")
def por_estado():
    return jsonify(call_api("licitaciones.json", {
        "estado": norm_estado(request.args.get("estado"), "desierta"),
        "fecha": norm_fecha(request.args.get("fecha")),
    }))


@app.route("/licitaciones/organismo")
def por_organismo():
    return jsonify(call_api("licitaciones.json", {
        "CodigoOrganismo": request.args.get("codigo", "").strip(),
        "fecha": norm_fecha(request.args.get("fecha")),
        "estado": norm_estado(request.args.get("estado"), ""),
    }))


@app.route("/licitaciones/proveedor")
def por_proveedor():
    return jsonify(call_api("licitaciones.json", {
        "CodigoProveedor": request.args.get("codigo", "").strip(),
        "fecha": norm_fecha(request.args.get("fecha")),
    }))


# ----------------------------------------------------------- Nuevas rutas
@app.route("/api/buscar")
def buscar():
    """
    Lista licitaciones (activas por defecto), filtra por palabras clave en el
    nombre y trae el detalle (monto, organismo, región, ítems) de las primeras N.
      ?q=coffee,catering,pantalla led   (separadas por coma)
      &estado=activas|publicada|desierta|...   &fecha=ddmmaaaa
      &detalle=25   (máx 60; cada detalle es una llamada a la API, con caché 6 h)
    """
    estado = norm_estado(request.args.get("estado"), "activas")
    fecha = norm_fecha(request.args.get("fecha"))
    n_det = max(0, min(int(request.args.get("detalle", 25) or 0), 60))
    palabras = [sin_tildes(p.strip()) for p in request.args.get("q", "").split(",") if p.strip()]

    params = {"estado": estado}
    if fecha:
        params["fecha"] = fecha
    data = call_api("licitaciones.json", params, ttl=900)
    if not isinstance(data, dict) or "Listado" not in data:
        return jsonify({"error": (data or {}).get("error") or (data or {}).get("Mensaje") or "Respuesta inesperada de la API", "raw": data}), 502

    resultados = []
    for lic in data.get("Listado") or []:
        nombre_n = sin_tildes(lic.get("Nombre", ""))
        hits = [p for p in palabras if p in nombre_n]
        if palabras and not hits:
            continue
        resultados.append({**lic, "coincidencias": hits})

    resultados.sort(key=lambda x: (-len(x["coincidencias"]), x.get("FechaCierre") or "9999"))
    for item in resultados[:n_det]:
        det = detalle(item.get("CodigoExterno"))
        if det:
            item["detalle"] = det

    return jsonify({
        "total_api": data.get("Cantidad"),
        "total": len(resultados),
        "con_detalle": min(n_det, len(resultados)),
        "estado": estado,
        "Listado": resultados,
    })


@app.route("/api/detalle/<codigo>")
def api_detalle(codigo):
    det = detalle(codigo)
    if not det:
        return jsonify({"error": "No se encontró la licitación"}), 404
    return jsonify(det)


@app.route("/api/ordenes")
def ordenes():
    """Órdenes de compra: ?codigo= | ?fecha=&organismo=&proveedor=&estado="""
    params = {
        "codigo": request.args.get("codigo", "").strip(),
        "fecha": norm_fecha(request.args.get("fecha")),
        "CodigoOrganismo": request.args.get("organismo", "").strip(),
        "CodigoProveedor": request.args.get("proveedor", "").strip(),
        "estado": request.args.get("estado", "").strip().lower(),
    }
    if not any([params["codigo"], params["fecha"]]):
        params["fecha"] = (datetime.utcnow() - timedelta(hours=3)).strftime("%d%m%Y")
    return jsonify(call_api("ordenesdecompra.json", params, ttl=1800))


@app.route("/api/empresa")
def empresa():
    """Busca código de proveedor o comprador por RUT: ?rut=76.123.456-7&tipo=proveedor|comprador"""
    rut = request.args.get("rut", "").strip()
    if (request.args.get("tipo") or "proveedor") == "comprador":
        return jsonify(call_api("Empresas/BuscarComprador", {}, ttl=24 * 3600))
    return jsonify(call_api("Empresas/BuscarProveedor", {"rutempresaproveedor": rut}, ttl=24 * 3600))


@app.route("/api/propuesta", methods=["POST"])
def propuesta():
    """Redacta una propuesta técnica-económica con Claude (si hay ANTHROPIC_API_KEY)."""
    if not ANTHROPIC_KEY:
        return jsonify({"error": "sin_ia", "mensaje": "Configura ANTHROPIC_API_KEY en Railway para redactar con IA"}), 501
    body = request.get_json(silent=True) or {}
    lic = body.get("licitacion") or {}
    empresa_ = body.get("empresa") or {}
    calculo = body.get("calculo") or {}
    instrucciones = body.get("instrucciones") or ""

    items = ((lic.get("Items") or {}).get("Listado") or [])[:40]
    items_txt = "\n".join(
        f"- {i.get('NombreProducto') or ''}: {i.get('Descripcion') or ''} "
        f"({i.get('Cantidad')} {i.get('UnidadMedida') or ''})" for i in items
    )
    prompt = f"""Eres experto en licitaciones públicas de Chile (Mercado Público, Ley 19.886).
Redacta en español de Chile una propuesta técnica y económica lista para adaptar y subir.

LICITACIÓN
Código: {lic.get('CodigoExterno')}
Nombre: {lic.get('Nombre')}
Organismo: {(lic.get('Comprador') or {}).get('NombreOrganismo')}
Región: {(lic.get('Comprador') or {}).get('RegionUnidad')}
Tipo: {lic.get('Tipo')}
Monto estimado: {lic.get('MontoEstimado')} {lic.get('Moneda') or ''}
Cierre: {(lic.get('Fechas') or {}).get('FechaCierre')}
Descripción: {(lic.get('Descripcion') or '')[:3000]}
Ítems:
{items_txt or '(sin detalle de ítems)'}

EMPRESA OFERENTE
{empresa_.get('nombre', '')} — RUT {empresa_.get('rut', '')}
Rubro: {empresa_.get('rubro', '')}
Experiencia y diferenciadores: {empresa_.get('experiencia', '')}
Contacto: {empresa_.get('contacto', '')}

CÁLCULO ECONÓMICO (CLP)
{calculo}

INSTRUCCIONES ADICIONALES
{instrucciones}

Estructura: 1) Carta de presentación, 2) Comprensión del requerimiento,
3) Propuesta técnica (metodología, plazos, equipo, logística),
4) Propuesta económica (tabla en texto con valores neto, IVA, total),
5) Garantías y cumplimiento de bases, 6) Checklist de anexos a revisar en las bases.
No inventes certificaciones ni experiencia que no se indicó; marca con [COMPLETAR] lo que falte."""
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": ANTHROPIC_KEY, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": ANTHROPIC_MODEL, "max_tokens": 4000,
                  "messages": [{"role": "user", "content": prompt}]},
            timeout=110,
        )
        data = r.json()
        if r.status_code != 200:
            return jsonify({"error": "ia", "mensaje": (data.get("error") or {}).get("message", str(data))}), 502
        texto = "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text")
        return jsonify({"texto": texto})
    except Exception as e:
        return jsonify({"error": "ia", "mensaje": str(e)}), 502


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
