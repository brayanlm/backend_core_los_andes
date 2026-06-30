import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.mdl_all import SyncOutbox, SyncLog


ENTITY_MAP = {
    "clientes": "cr_cliente",
    "creditos": "cr_credito",
    "solicitudes_credito": "cr_solicitud_credito",
    "cronograma_pagos": "cr_cronograma_pago",
    "cuentas_ahorro": "cr_cuenta_ahorro",
    "movimientos": "cr_movimiento",
    "tarjetas": "cr_tarjeta",
    "notificaciones": "cr_notificacion",
    "operaciones_cliente": "cr_operacion",
    "acciones_cobranza": "cr_accion_cobranza",
    "creditos_preaprobados": "cr_credito_preaprobado",
    "historial_creditos": "cr_historial_credito",
    "solicitudes_notas_internas": "cr_nota_interna",
    "cartera_diaria": "cr_cartera_diaria",
    "asesores": "cr_asesor",
}


def _get_columns(db: Session, tabla: str) -> set:
    rows = db.execute(text(f"SELECT column_name FROM information_schema.columns WHERE table_schema='public' AND table_name=:t"), {"t": tabla}).all()
    return {r[0] for r in rows}


def mirror_write(db: Session, coleccion: str, doc_id: str, data: dict):
    tabla = ENTITY_MAP.get(coleccion)
    if not tabla:
        return
    cols = _get_columns(db, tabla)
    filtered = {"id": doc_id}
    for k, v in data.items():
        if k in cols and not callable(v) and not isinstance(v, (bytes,)):
            filtered[k] = v if not hasattr(v, "isoformat") else v.isoformat()
    _upsert(db, tabla, filtered)


def mirror_delete(db: Session, coleccion: str, doc_id: str):
    tabla = ENTITY_MAP.get(coleccion)
    if not tabla:
        return
    db.execute(text(f"DELETE FROM {tabla} WHERE id = :id"), {"id": doc_id})
    db.commit()


def enqueue_sync(db: Session, coleccion: str, operacion: str, datos: dict):
    entidad = ENTITY_MAP.get(coleccion, coleccion)
    entry = SyncOutbox(
        id=str(uuid.uuid4()),
        entidad=entidad,
        operacion=operacion,
        datos=json.dumps(datos, default=str),
        estado="pendiente",
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    db.add(entry)
    db.commit()


def mirror_and_enqueue(db: Session, coleccion: str, doc_id: str, data: dict, operacion: str = "INSERT"):
    mirror_write(db, coleccion, doc_id, data)
    enqueue_sync(db, coleccion, operacion, {"id": doc_id, **data})


def _upsert(db: Session, tabla: str, data: dict):
    existing = db.execute(
        text(f"SELECT id FROM {tabla} WHERE id = :id"), {"id": data.get("id", "")}
    ).first()
    if existing:
        set_clause = ", ".join(f"{k} = :{k}" for k in data)
        db.execute(text(f"UPDATE {tabla} SET {set_clause} WHERE id = :id"), data)
    else:
        cols = ", ".join(data.keys())
        placeholders = ", ".join(f":{k}" for k in data)
        db.execute(text(f"INSERT INTO {tabla} ({cols}) VALUES ({placeholders})"), data)
    db.commit()
