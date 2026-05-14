from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)  # Permite llamadas desde cualquier navegador

TICKET = "33588502-90E2-4B19-9FCA-0960F65D93CC"
BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico"

def call_api(endpoint, params={}):
    params["ticket"] = TICKET
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e), "Codigo": 500}

# ─── RUTAS ───────────────────────────────────────────────

@app.route("/")
def index():
    return jsonify({"status": "ok", "app": "LicitaIA", "empresa": "People on Technology"})

@app.route("/licitaciones/fecha")
def por_fecha():
    fecha = request.args.get("fecha", "")   # formato ddmmaaaa
    estado = request.args.get("estado", "")
    params = {"fecha": fecha}
    if estado:
        params["estado"] = estado
    data = call_api("licitaciones.json", params)
    return jsonify(data)

@app.route("/licitaciones/codigo")
def por_codigo():
    codigo = request.args.get("codigo", "")
    data = call_api("licitaciones.json", {"codigo": codigo})
    return jsonify(data)

@app.route("/licitaciones/estado")
def por_estado():
    estado = request.args.get("estado", "7")
    fecha = request.args.get("fecha", "")
    params = {"estado": estado}
    if fecha:
        params["fecha"] = fecha
    data = call_api("licitaciones.json", params)
    return jsonify(data)

@app.route("/licitaciones/organismo")
def por_organismo():
    codigo_org = request.args.get("codigo", "")
    fecha = request.args.get("fecha", "")
    params = {"CodigoOrganismo": codigo_org}
    if fecha:
        params["fecha"] = fecha
    data = call_api("licitaciones.json", params)
    return jsonify(data)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=False)
