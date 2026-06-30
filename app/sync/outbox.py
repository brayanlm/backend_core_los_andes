import json
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.models.mdl_all import SyncOutbox, SyncLog


def enqueue(db: Session, entidad: str, operacion: str, datos: dict):
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


def dequeue(db: Session, limit: int = 50) -> list[dict]:
    items = (
        db.query(SyncOutbox)
        .filter(SyncOutbox.estado == "pendiente")
        .order_by(SyncOutbox.created_at.asc())
        .limit(limit)
        .all()
    )
    return [
        {
            c.name: getattr(item, c.name)
            for c in item.__table__.columns
        }
        for item in items
    ]


def mark_processed(db: Session, outbox_id: str, error: Optional[str] = None):
    item = db.query(SyncOutbox).filter(SyncOutbox.id == outbox_id).first()
    if not item:
        return
    now = datetime.now(timezone.utc).isoformat()
    if error:
        item.estado = "error"
        item.error_msg = error
        item.intentos = (item.intentos or 0) + 1
    else:
        item.estado = "procesado"
    item.procesado_at = now
    db.commit()


def log_sync(db: Session, tipo: str, entidad: str, registros: int, resultado: str = "ok", detalle: str = ""):
    entry = SyncLog(
        id=str(uuid.uuid4()),
        tipo=tipo,
        entidad=entidad,
        registros=registros,
        resultado=resultado,
        detalle=detalle,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    db.add(entry)
    db.commit()
