"""Caso 12 - Flujo completo desde App Clientes hasta cronograma."""
import os, sys, json, uuid, requests
from datetime import datetime, timezone

BASE = os.environ.get("API_URL", "http://localhost:8010")

s = requests.Session()
errors = []

def ok(label, detail=""):
    print(f"  [OK] {label}{' - '+detail if detail else ''}")

def fail(label, detail):
    print(f"  [FAIL] {label}: {detail}")
    errors.append(f"{label}: {detail}")

def check(label, cond, detail=""):
    if cond:
        ok(label, detail)
    else:
        fail(label, detail)

# ============================================================
# 1. REGISTRAR CLIENTE (Ariadna Quispe)
# ============================================================
print("\n=== 1. Registrar Cliente (App Clientes) ===")
reg_data = {
    "numero_documento": "41226021",
    "password": "ariadna123",
    "nombres": "Ariadna",
    "apellidos": "Quispe",
    "telefono": "964110212",
    "direccion": "El Tambo",
}
r = s.post(f"{BASE}/cliente/register", json=reg_data)
if r.status_code == 200:
    cliente_token = r.json()["access_token"]
    cliente_id = r.json()["cliente"]["id"]
    ok("Cliente registrado", f"id={cliente_id}")
elif "ya existe" in r.text:
    # Ya registrado antes - login directo
    r2 = s.post(f"{BASE}/cliente/login", json={"numero_documento":"41226021","password":"ariadna123"})
    assert r2.status_code == 200, f"Login cliente fallo: {r2.text}"
    cliente_token = r2.json()["access_token"]
    cliente_id = r2.json()["cliente"]["id"]
    ok("Cliente ya existia, login ok", f"id={cliente_id}")
else:
    fail("Registrar cliente", f"{r.status_code} {r.text[:200]}")
    sys.exit(1)

# ============================================================
# 2. CREAR SOLICITUD DESDE APP CLIENTES
# ============================================================
print("\n=== 2. Solicitud desde App Clientes ===")
s.headers.update({"Authorization": f"Bearer {cliente_token}"})
sol_data = {
    "monto_solicitado": 4000.0,
    "plazo": 18,
    "tea": 0.4392,
    "destino": "Mobiliario y equipos de salon",
    "ingresos_declarados": 3300.0,
    "nombre_negocio": "Estilos Ariadna",
    "rubro_negocio": "Peluqueria",
    "antiguedad_negocio_meses": 40,
    "tipo_negocio": "microempresa",
    "garantia": "sin_garantia",
    "gastos_mensuales": 1300.0,
    "tipo_cuota": "mensual",
}
r = s.post(f"{BASE}/cliente/solicitudes", json=sol_data)
check(r.status_code in (200, 201), f"Crear solicitud status={r.status_code}",
      f"{r.text[:200]}" if r.status_code != 201 else "")
if r.status_code not in (200, 201):
    sys.exit(1)
sol = r.json()
solicitud_id = sol["id"]
check(sol["estado"] == "enviado", f"Solicitud creada id={solicitud_id}",
      f"estado={sol['estado']}, cuota_estimada={sol.get('cuota_estimada')}")
cuota_ref = sol.get("cuota_estimada", 0)
check(abs(cuota_ref - 292.82) < 5, f"Cuota de referencia ~292.82",
      f"obtenida={cuota_ref:.2f}")

# ============================================================
# 3. LOGIN ADMIN
# ============================================================
print("\n=== 3. Login Admin ===")
r = s.post(f"{BASE}/auth/login", json={"codigo_empleado":"000","password":"admin123"})
assert r.status_code == 200
token_admin = r.json()["access_token"]
s.headers.update({"Authorization": f"Bearer {token_admin}"})
ok("Admin logged in")

# ============================================================
# 4. PRE-EVALUAR
# ============================================================
print("\n=== 4. Pre-evaluar ===")
r = s.post(f"{BASE}/pre-evaluar", json={
    "numero_documento": "41226021",
    "nombres": "Ariadna Quispe",
    "tipo_negocio": "Peluqueria",
    "ingresos_estimados": 3300.0,
    "monto_solicitado": 4000.0,
    "destino_credito": "Mobiliario y equipos de salon",
})
check(r.status_code == 200, f"Pre-evaluar status={r.status_code}",
      f"{r.text[:200]}" if r.status_code != 200 else "")
if r.status_code == 200:
    pe = r.json()
    check(pe["calificacion"] == "APTO", f"Pre-eval={pe['calificacion']}",
          f"puntaje={pe.get('puntaje','?')}, motivo={pe.get('motivo','')}")

# ============================================================
# 5. BURÓ
# ============================================================
print("\n=== 5. Buró de Créditos ===")
r = s.post(f"{BASE}/buro/consulta", json={
    "dni": "41226021",
    "cliente_id": cliente_id,
})
check(r.status_code == 200, f"Buro status={r.status_code}")
if r.status_code == 200:
    bu = r.json()
    check(bu["calificacion_sbs"] == "NORMAL", f"SBS={bu['calificacion_sbs']}",
          f"entidades={bu['entidades_con_deuda']}, deuda_total={bu['deuda_total']}, mora={bu.get('dias_mayor_mora',0)}")

# ============================================================
# 6. ASIGNAR ASESOR
# ============================================================
print("\n=== 6. Asignar Asesor ===")
# Asignar a asesor 001 (codigo_empleado)
r = s.put(f"{BASE}/solicitudes/{solicitud_id}/asignar-generar", json={
    "codigo_empleado": "001",
})
check(r.status_code in (200, 201), f"Asignar status={r.status_code}",
      f"{r.text[:200]}" if r.status_code not in (200, 201) else "")

# ============================================================
# 7. VISITA
# ============================================================
print("\n=== 7. Registrar Visita ===")
r = s.post(f"{BASE}/solicitudes/{solicitud_id}/visita", json={
    "resultado": "visitado",
    "lat": -12.0573,
    "lng": -75.2161,
    "comentario": "Visita de evaluacion - Caso 12",
})
check(r.status_code in (200, 201), f"Visita status={r.status_code}",
      f"{r.text[:200]}" if r.status_code != 201 else "")

# ============================================================
# 8. COMITÉ
# ============================================================
print("\n=== 8. Enviar a Comité ===")
r = s.put(f"{BASE}/solicitudes/{solicitud_id}/comite", json={
    "comentario": "Solicitud evaluada, enviar a comite",
})
check(r.status_code in (200, 201), f"Comite status={r.status_code}",
      f"{r.text[:200]}" if r.status_code not in (200, 201) else "")

# ============================================================
# 9. EVALUAR
# ============================================================
print("\n=== 9. Evaluar ===")
r = s.put(f"{BASE}/solicitudes/{solicitud_id}/evaluar", json={
    "score": 85,
})
check(r.status_code in (200, 201), f"Evaluar status={r.status_code}",
      f"{r.text[:200]}" if r.status_code not in (200, 201) else "")

# ============================================================
# 10. APROBAR
# ============================================================
print("\n=== 10. Aprobar ===")
r = s.put(f"{BASE}/solicitudes/{solicitud_id}/aprobar", json={
    "monto_aprobado": 4000.0,
    "tasa_final": 0.4392,
    "comentario": "Aprobado segun evaluacion - Caso 12",
})
check(r.status_code in (200, 201), f"Aprobar status={r.status_code}",
      f"{r.text[:300]}" if r.status_code not in (200, 201) else "")
if r.status_code in (200, 201):
    aprob = r.json()
    credito_id = aprob.get("credito_id") or aprob.get("id")
    check(credito_id is not None, "Credito generado", f"credito_id={credito_id}")
else:
    credito_id = None

# ============================================================
# 11. VER SOLICITUD
# ============================================================
print("\n=== 11. Ver Solicitud Aprobada ===")
r = s.get(f"{BASE}/solicitudes/{solicitud_id}")
if r.status_code == 200:
    sol_ver = r.json()
    check(sol_ver["estado"] == "aprobado", f"Estado={sol_ver['estado']}",
          f"credito_id={sol_ver.get('credito_id')}")
    if not credito_id:
        credito_id = sol_ver.get("credito_id")

# ============================================================
# 12. DESEMBOLSAR
# ============================================================
print("\n=== 12. Desembolsar ===")
if credito_id:
    r = s.post(f"{BASE}/creditos/{credito_id}/desembolsar", json={
        "cuenta_destino": "CTA-ARIADNA-001",
    })
    check(r.status_code in (200, 201), f"Desembolso status={r.status_code}",
          f"{r.text[:300]}" if r.status_code != 201 else "")
    if r.status_code == 201:
        des = r.json()
        check(des["estado"] == "desembolsado" or des.get("total_cuotas") == 18,
              f"Desembolso OK", f"total_cuotas={des.get('total_cuotas')}, mensaje={des.get('mensaje','')}")
else:
    fail("Desembolsar", "No hay credito_id")

# ============================================================
# 13. CRONOGRAMA
# ============================================================
print("\n=== 13. Cronograma de Pagos ===")
if credito_id:
    r = s.get(f"{BASE}/creditos/{credito_id}/cronograma")
    check(r.status_code == 200, f"Cronograma status={r.status_code}")
    if r.status_code == 200:
        cuotas = r.json()
        check(len(cuotas) == 18, f"Total cuotas={len(cuotas)}")
        if cuotas:
            print(f"\n  {'N°':>3} {'Fecha Venc':>12} {'Cuota':>8} {'Capital':>8} {'Interes':>8} {'Saldo':>8}")
            print(f"  {'-'*50}")
            primera = cuotas[0]
            check(abs(primera["monto_cuota"] - 292.82) < 1, f"Cuota 1 ~292.82",
                  f"obtenido={primera['monto_cuota']:.2f}")
            check(abs(primera["monto_capital"] - 169.60) < 1, f"Capital cuota 1 ~169.60",
                  f"obtenido={primera['monto_capital']:.2f}")
            check(abs(primera["monto_interes"] - 123.22) < 1, f"Interes cuota 1 ~123.22",
                  f"obtenido={primera['monto_interes']:.2f}")
            for c in cuotas[:5]:
                print(f"  {c['nro_cuota']:>3} {str(c.get('fecha_vencimiento','')):>12} {c['monto_cuota']:>8.2f} {c['monto_capital']:>8.2f} {c['monto_interes']:>8.2f} {c['saldo']:>8.2f}")
            print(f"  ...")
            ultima = cuotas[-1]
            print(f"  {ultima['nro_cuota']:>3} {str(ultima.get('fecha_vencimiento','')):>12} {ultima['monto_cuota']:>8.2f} {ultima['monto_capital']:>8.2f} {ultima['monto_interes']:>8.2f} {ultima['saldo']:>8.2f}")
            check(ultima["saldo"] < 1, f"Saldo final ~0", f"obtenido={ultima['saldo']:.2f}")
else:
    fail("Cronograma", "No hay credito_id")

# ============================================================
# RESUMEN
# ============================================================
print(f"\n{'='*60}")
if errors:
    print(f"RESULTADO: {len(errors)} error(es):")
    for e in errors:
        print(f"  - {e}")
else:
    print("RESULTADO: CASO 12 COMPLETO EXITOSAMENTE")
print(f"{'='*60}")
