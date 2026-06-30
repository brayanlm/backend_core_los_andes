"""Test rapido del API."""
import urllib.request, json

BASE = "http://127.0.0.1:8003"

# 1. Login
body = json.dumps({"codigo_empleado": "0001", "password": "123456"}).encode()
req = urllib.request.Request(f"{BASE}/auth/login", data=body, headers={"Content-Type": "application/json"})
resp = urllib.request.urlopen(req)
login = json.loads(resp.read())
token = login["access_token"]
print(f"[OK] Login: {login['asesor']['nombres']} {login['asesor']['apellidos']}")

headers = {"Authorization": f"Bearer {token}"}

# 2. Cartera
req = urllib.request.Request(f"{BASE}/cartera/", headers=headers)
resp = urllib.request.urlopen(req)
cartera = json.loads(resp.read())
print(f"[OK] Cartera: {len(cartera)} items")
for c in cartera[:3]:
    print(f"      {c['cliente_nombre']}: {c['tipo_gestion']} [{c['estado_visita']}]")

# 3. Cobranza / mora
req = urllib.request.Request(f"{BASE}/cobranza/mora", headers=headers)
resp = urllib.request.urlopen(req)
mora = json.loads(resp.read())
print(f"[OK] Mora: {len(mora)} clientes en mora")

# 4. Pre-evaluar
body = json.dumps({"numero_documento": "44455667", "ingresos_estimados": 2000, "monto_solicitado": 5000}).encode()
req = urllib.request.Request(f"{BASE}/pre-evaluar", data=body, headers={"Content-Type": "application/json", **headers})
resp = urllib.request.urlopen(req)
preeval = json.loads(resp.read())
print(f"[OK] Pre-evaluacion: {preeval['calificacion']} (score: {preeval['puntaje']})")

# 5. Buro
body = json.dumps({"dni": "44455667"}).encode()
req = urllib.request.Request(f"{BASE}/buro/consulta", data=body, headers={"Content-Type": "application/json", **headers})
resp = urllib.request.urlopen(req)
buro = json.loads(resp.read())
print(f"[OK] Buro: {buro['calificacion_sbs']} - {buro['interpretacion'][:50]}...")

# 6. Ficha cliente
cli_id = cartera[0]["cliente_id"] if cartera else ""
if cli_id:
    req = urllib.request.Request(f"{BASE}/clientes/{cli_id}/ficha", headers=headers)
    resp = urllib.request.urlopen(req)
    ficha = json.loads(resp.read())
    print(f"[OK] Ficha: {ficha['cliente']['nombres']} - deuda: S/{ficha['posicion']['deuda_total']:.0f}")

# 7. Solicitudes
body = json.dumps({
    "numero_documento": "99988877",
    "nombres": "TEST",
    "apellidos": "API",
    "monto_solicitado": 3000,
    "plazo_meses": 6,
}).encode()
req = urllib.request.Request(f"{BASE}/solicitudes", data=body, headers={"Content-Type": "application/json", **headers})
resp = urllib.request.urlopen(req)
sol = json.loads(resp.read())
print(f"[OK] Solicitud creada: {sol['numero_expediente']}")

# 8. Root
req = urllib.request.Request(f"{BASE}/")
resp = urllib.request.urlopen(req)
root = json.loads(resp.read())
print(f"[OK] Root: {root['sistema']} v{root['version']}")

print("\n--- TODOS LOS TEST PASARON ---")
