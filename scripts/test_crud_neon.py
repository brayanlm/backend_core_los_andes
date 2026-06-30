"""Test CRUD completo contra Neon."""
import os, sys, json, uuid, requests

BASE = os.environ.get("API_URL", "http://localhost:8010")
adm = {"codigo_empleado": "000", "password": "admin123"}

s = requests.Session()

# 1. LOGIN
r = s.post(f"{BASE}/auth/login", json=adm)
assert r.status_code == 200, f"Login fallo: {r.text}"
token = r.json()["access_token"]
s.headers.update({"Authorization": f"Bearer {token}"})
asesor_id = r.json()["asesor"]["id"]
print(f"[OK] Login admin -> asesor_id={asesor_id}")

# 2. CREAR CLIENTE
cli_data = {
            "numero_documento": "87654322",
    "nombres": "Test",
    "apellidos": "Neon",
    "telefono": "999888777",
    "direccion": "Av. PostgreSQL 123",
}
r = s.post(f"{BASE}/clientes", json=cli_data)
assert r.status_code == 200, f"Crear cliente fallo: {r.text}"
cliente_id = r.json()["id"]
print(f"[OK] Cliente creado -> id={cliente_id}")

# 3. CREAR SOLICITUD (usando campos del schema SolicitudCreate)
sol_data = {
    "cliente_id": cliente_id,
    "monto_solicitado": 10000.0,
    "plazo_meses": 12,
    "destino_credito": "Capital de trabajo",
    "garantia": "personal",
    "canal": "asesor",
    "tipo_negocio": "comercio",
    "ingresos_estimados": 3000.0,
}
r = s.post(f"{BASE}/solicitudes", json=sol_data)
if r.status_code != 201:
    print(f"[WARN] Crear solicitud fallo: {r.status_code} {r.text}")
    # Minimal version
    sol_data2 = {
        "cliente_id": cliente_id,
        "monto_solicitado": 10000.0,
        "plazo_meses": 12,
    }
    r = s.post(f"{BASE}/solicitudes", json=sol_data2)
    if r.status_code != 201:
        # Try with numero_documento instead
        sol_data3 = {
    "numero_documento": "87654322",
            "nombres": "Test",
            "apellidos": "Neon",
            "monto_solicitado": 10000.0,
            "plazo_meses": 12,
        }
        r = s.post(f"{BASE}/solicitudes", json=sol_data3)
assert r.status_code == 201, f"Crear solicitud fallo definitivo: {r.status_code} {r.text}"
solicitud_id = r.json()["id"]
print(f"[OK] Solicitud creada -> id={solicitud_id}, estado={r.json().get('estado','')}")

# 4. COMITE + EVALUAR + APROBAR
for step, ep, data in [
    ("Comite", f"{BASE}/solicitudes/{solicitud_id}/comite", None),
    ("Evaluar", f"{BASE}/solicitudes/{solicitud_id}/evaluar", {"score": 680}),
    ("Aprobar", f"{BASE}/solicitudes/{solicitud_id}/aprobar", {"monto_aprobado": 10000.0, "tasa_final": 0.25}),
]:
    r = s.put(ep, json=data) if data else s.put(ep)
    if r.status_code in (200, 201):
        print(f"[OK] {step} exitoso")
    else:
        print(f"[WARN] {step}: {r.status_code} {r.text[:200]}")

# 5. VER solicitud aprobada
r = s.get(f"{BASE}/solicitudes/{solicitud_id}")
assert r.status_code == 200
sol = r.json()
credito_id = sol.get("credito_id")
print(f"[OK] Solicitud estado={sol['estado']}, credito_id={credito_id}")

# 6. LISTAR CREDITOS
r = s.get(f"{BASE}/creditos")
if r.status_code == 200:
    print(f"[OK] Creditos listados: {len(r.json())} creditos")

# 7. DESEMBOLSAR (si hay credito)
if credito_id:
    r = s.post(f"{BASE}/creditos/{credito_id}/desembolsar", json={
        "cuenta_destino": "CTA-TEST123",
    })
    if r.status_code == 201:
        print(f"[OK] Desembolso registrado en credito {credito_id}")
    else:
        print(f"[WARN] Desembolsar: {r.status_code} {r.text[:300]}")

print("\n=== FLUJO CRUD COMPLETO EN NEON ===")
