"""Script para probar el flujo completo: crear solicitud -> aprobar -> promover"""
import uuid, json, sys, os
from datetime import datetime, timezone

# Asegurar que podemos importar los módulos del backend
sys.path.insert(0, os.path.dirname(__file__))

from app.core.firebase_service import get_firestore, init_firebase
from app.database.connection import get_sqlite_conn

# 1. Crear solicitud en Firestore (simula App Cliente)
print("1. Creando solicitud en Firestore...")
init_firebase()
db = get_firestore()
sid = str(uuid.uuid4())
db.collection('solicitudes_credito').document(sid).set({
    'cliente_id': 'Mq6es7Ll1vUaKx0lCvHkcPudQNA2',
    'monto': 5000.0,
    'plazo': 12,
    'tasa_sugerida': 0.25,
    'ingresos': 2500.0,
    'destino': 'Capital de trabajo',
    'cuota_estimada': 0.0,
    'ratio': 0.0,
    'estado': 'PENDIENTE',
    'canal': 'cliente',
    'created_at': datetime.now(timezone.utc).isoformat()
})
print(f"   Solicitud creada: {sid}")
print()

# 2. Ver solicitudes pendientes
print("2. Solicitudes pendientes en SQLite:")
conn = get_sqlite_conn()
pendientes = conn.execute("SELECT id, monto, destino_credito, estado FROM cr_solicitud_credito").fetchall()
for r in pendientes:
    print(f"   - {r['id'][:8]}... | S/{r['monto']:.0f} | {r['destino_credito']} | {r['estado']}")
print()

# 3. Ver resumen de BD
print("3. Resumen de la base de datos:")
tablas = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()
for (name,) in tablas:
    cnt = conn.execute(f'SELECT COUNT(*) as c FROM "{name}"').fetchone()['c']
    if cnt > 0:
        print(f"   {name}: {cnt} registros")
conn.close()
print()
print("=== FLOW COMPLETO ===")
print(f"Solicitud ID: {sid}")
print("Ahora en otra terminal (o desde el Portal), aprobar con:")
print(f"  POST /solicitudes/{sid}/aprobar")
print("Luego promover con:")
print(f"  POST /sync-db/promover body: {{\"solicitud_id\":\"{sid}\"}}")
