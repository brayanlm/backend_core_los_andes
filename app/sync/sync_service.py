"""
Sync service — PostgreSQL only. Firestore removed.
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.mdl_all import SyncOutbox, Cliente, SolicitudCredito, Credito


def push_outbox(db: Session, limit: int = 50) -> dict:
    """Push ya no opera contra Firestore. Solo marca los pendientes como procesados."""
    from app.sync.outbox import dequeue, mark_processed, log_sync
    items = dequeue(db, limit)
    for item in items:
        mark_processed(db, item["id"], "sync_disabled")
    log_sync(db, "push", f"{len(items)} skipped (Firestore disabled)", len(items), "ok")
    return {"ok": len(items), "error": 0, "detail": "Firestore disabled — outbox drained"}


def pull_all(db: Session) -> dict:
    """Pull ya no opera contra Firestore."""
    from app.sync.outbox import log_sync
    log_sync(db, "pull", "Firestore disabled", 0, "ok")
    return {"detail": "Firestore disabled — no data pulled", "tablas": {}}


def promover_solicitud(db: Session, solicitud_id: str) -> dict:
    sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == solicitud_id).first()
    if not sol:
        return {"error": "Solicitud no encontrada en PostgreSQL"}

    estado = sol.estado
    if estado not in ("APROBADO", "desembolsado"):
        return {"error": f"Estado invalido: {estado}"}

    cliente = db.query(Cliente).filter(Cliente.id == sol.cliente_id).first()
    if not cliente:
        return {"error": "Cliente no encontrado en PostgreSQL"}

    cliente_data = {
        "id": cliente.id,
        "numero_documento": cliente.numero_documento,
        "nombres": cliente.nombres,
        "apellidos": cliente.apellidos,
        "direccion": cliente.direccion,
        "telefono": cliente.telefono,
        "calificacion_sbs": cliente.calificacion_sbs or "NORMAL",
    }

    # Upsert dcliente
    db.execute(
        text("""INSERT INTO dcliente (id, cod_cliente, numero_documento, nombres, apellidos, calificacion_sbs, estado, created_at)
                VALUES (:id, :cod, :doc, :nom, :ape, :sbs, 'activo', :now)
                ON CONFLICT (id) DO UPDATE SET
                  numero_documento=EXCLUDED.numero_documento,
                  nombres=EXCLUDED.nombres,
                  apellidos=EXCLUDED.apellidos,
                  calificacion_sbs=EXCLUDED.calificacion_sbs,
                  estado='activo'"""),
        {"id": str(uuid.uuid4()), "cod": cliente_data["id"], "doc": cliente_data.get("numero_documento", ""),
         "nom": cliente_data.get("nombres", ""), "ape": cliente_data.get("apellidos", ""),
         "sbs": cliente_data.get("calificacion_sbs", "NORMAL"),
         "now": datetime.now(timezone.utc).isoformat()},
    )

    cred = db.query(Credito).filter(Credito.solicitud_id == solicitud_id).first()
    cod_credito = cred.id if cred else None

    db.execute(
        text("""INSERT INTO dsolicitud (id, cod_solicitud, cod_cliente, monto, plazo_meses, estado, created_at)
                VALUES (:id, :sol_id, :cli_id, :monto, :plazo, :est, :now)
                ON CONFLICT (id) DO NOTHING"""),
        {"id": str(uuid.uuid4()), "sol_id": sol.id, "cli_id": cliente_data["id"],
         "monto": sol.monto, "plazo": sol.plazo, "est": estado,
         "now": datetime.now(timezone.utc).isoformat()},
    )

    db.commit()
    return {
        "solicitud_id": solicitud_id,
        "cod_cliente": cliente_data["id"],
        "cod_credito": cod_credito,
        "estado": "promovido",
    }
