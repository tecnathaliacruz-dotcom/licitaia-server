from flask import Flask, jsonify, request
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app, origins="*", allow_headers="*", methods=["GET","POST","OPTIONS"])

TICKET = "33588502-90E2-4B19-9FCA-0960F65D93CC"
BASE_URL = "https://api.mercadopublico.cl/servicios/v1/publico"

def call_api(endpoint, params={}):
    params["ticket"] = TICKET
    try:
        r = requests.get(f"{BASE_URL}/{endpoint}", params=params, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        return {"error": str(e), "Codigo": 500}

@app.route("/")
def index():
    return jsonify({"status": "ok", "app": "LicitaIA"})

@app.route("/licitaciones/fecha")
def por_fecha():
    params = {"fecha": request.args.get("fecha","")}
    estado = request.args.get("estado","")
    if estado: params["estado"] = estado
    return jsonify(call_api("licitaciones.json", params))

@app.route("/licitaciones/codigo")
def por_codigo():
    return jsonify(call_api("licitaciones.json", {"codigo": request.args.get("codigo","")}))

@app.route("/licitaciones/estado")
def por_estado():
    params = {"estado": request.args.get("estado","7")}
    fecha = request.args.get("fecha","")
    if fecha: params["fecha"] = fecha
    return jsonify(call_api("licitaciones.json", params))

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
