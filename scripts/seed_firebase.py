"""
Seed de datos demo para Firebase (Auth + Firestore).
Crea: 1 agencia, 1 asesor (login 0001 / clave 123456), 5 clientes y su cartera.

Uso:
    python -m scripts.seed_firebase
"""
import sys, os, uuid
from datetime import datetime, timezone, date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.firebase_service import init_firebase
from app.core.cfg_config import settings

FIREBASE_API_KEY = settings.FIREBASE_WEB_API_KEY


def _create_firebase_user(email, password):
    """Crea un usuario en Firebase Auth via REST API."""
    import urllib.request, json as j
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={FIREBASE_API_KEY}"
    body = j.dumps({"email": email, "password": password, "returnSecureToken": True}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        resp = urllib.request.urlopen(req)
        return j.loads(resp.read())
    except urllib.error.HTTPError as e:
        err = j.loads(e.read())
        if err.get("error", {}).get("message") == "EMAIL_EXISTS":
            return {"alreadyExists": True}
        raise


def run():
    db = init_firebase()
    ahora = datetime.now(timezone.utc).isoformat()
    hoy = date.today().isoformat()

    # Verificar si ya hay datos
    existing = list(db.collection("asesores").limit(1).stream())
    if existing:
        print("Firestore ya contiene datos. Seed omitido.")
        return

    # 1. Crear Firebase Auth user
    print("Creando usuario Firebase Auth para 0001...")
    _create_firebase_user("0001@bancodelosandes.com", "123456")
    print("  Usuario creado.")

    # 2. Agencia
    agencia_id = str(uuid.uuid4())
    db.collection("agencias").document(agencia_id).set({
        "id": agencia_id,
        "cod_agencia": "0001",
        "nombre": "Agencia Central",
        "region": "Lima",
        "activa": True,
        "created_at": ahora,
    })
    print("  Agencia creada.")

    # 3. Asesor
    asesor_id = str(uuid.uuid4())
    db.collection("asesores").document(asesor_id).set({
        "id": asesor_id,
        "cod_asesor": "A001",
        "codigo_empleado": "0001",
        "nombres": "Carlos",
        "apellidos": "Ramirez",
        "agencia_id": agencia_id,
        "perfil": "operador",
        "activo": True,
        "created_at": ahora,
    })
    print("  Asesor creado.")

    # 4. Clientes y Cartera
    demo = [
        ("Maria Quispe Huaman",  "44455667", "RECUPERACION_MORA", "alta",   88, 8500),
        ("Jose Mamani Flores",   "41112233", "RENOVACION",        "alta",   72, 12000),
        ("Rosa Condori Apaza",   "42778899", "AMPLIACION",        "media",  55, 5000),
        ("Pedro Ccahua Ramos",   "43223344", "NUEVA_SOLICITUD",   "normal", 30, 3000),
        ("Lucia Vargas Soto",    "40556677", "SEGUIMIENTO",       "normal", 15, 4500),
    ]
    for i, (nombre, doc, tipo, prio, score, monto) in enumerate(demo):
        nombres, apellidos = nombre.split(" ", 1)
        cli_id = str(uuid.uuid4())
        db.collection("clientes").document(cli_id).set({
            "id": cli_id,
            "numero_documento": doc,
            "nombres": nombres,
            "apellidos": apellidos,
            "telefono": "9" + doc,
            "calificacion_sbs": "NORMAL",
            "created_at": ahora,
        })
        cartera_id = str(uuid.uuid4())
        db.collection("cartera_diaria").document(cartera_id).set({
            "id": cartera_id,
            "asesor_id": asesor_id,
            "cliente_id": cli_id,
            "agencia_id": agencia_id,
            "fecha_asignacion": hoy,
            "tipo_gestion": tipo,
            "prioridad": prio,
            "score_prioridad": score,
            "monto_credito": monto,
            "estado_visita": "pendiente",
            "orden_manual": i,
            "created_at": ahora,
        })
        print(f"  Cliente {nombres} {apellidos} + cartera creados.")

    # 5. Creditos con mora (para cobranza)
    for doc, prod, monto, dmora in [
        ("44455667", "CREDITO_PYME", 8500, 15),
        ("41112233", "CREDITO_PERSONAL", 12000, 0),
        ("42778899", "CREDITO_PYME", 5000, 45),
    ]:
        cli_docs = list(db.collection("clientes").where("numero_documento", "==", doc).limit(1).stream())
        if not cli_docs:
            continue
        cli_id = cli_docs[0].id
        cred_id = str(uuid.uuid4())
        db.collection("creditos").document(cred_id).set({
            "id": cred_id,
            "cod_cuenta_credito": f"CR-{doc}-001",
            "cliente_id": cli_id,
            "producto": prod,
            "monto_desembolsado": monto,
            "saldo_capital": monto * 0.6,
            "saldo_total": monto * 0.65,
            "dias_mora": dmora,
            "estado": "vigente" if dmora == 0 else "mora",
            "fecha_desembolso": "2025-06-01",
            "cuotas_total": 12,
            "cuotas_pagadas": 4,
            "created_at": ahora,
        })

    print("\nSeed completado exitosamente.")
    print("Login: codigo_empleado=0001  password=123456")


if __name__ == "__main__":
    run()
