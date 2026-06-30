from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.database.session import get_db
from app.core.cfg_auth import get_current_asesor

router = APIRouter()


class PromoverIn(BaseModel):
    solicitud_id: str


@router.post("/outbox/push")
def push_outbox(db=Depends(get_db), asesor: dict = Depends(get_current_asesor)):
    """Procesa la cola sync_outbox: drena pendientes (Firestore deshabilitado)."""
    from app.sync.sync_service import push_outbox
    return push_outbox(db, limit=100)


@router.post("/pull")
def pull_all(db=Depends(get_db), asesor: dict = Depends(get_current_asesor)):
    """Pull desde Firestore deshabilitado — todo en PostgreSQL."""
    from app.sync.sync_service import pull_all
    return pull_all(db)


@router.post("/promover")
def promover(payload: PromoverIn, db=Depends(get_db), asesor: dict = Depends(get_current_asesor)):
    """Promueve una solicitud aprobada al nucleo financiero."""
    from app.sync.sync_service import promover_solicitud
    result = promover_solicitud(db, payload.solicitud_id)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return {"mensaje": "Solicitud promovida al nucleo financiero", **result}


@router.get("/outbox/pendientes")
def listar_pendientes(db=Depends(get_db), asesor: dict = Depends(get_current_asesor)):
    """Lista los registros pendientes en la cola de sincronizacion."""
    from app.sync.outbox import dequeue
    return dequeue(db, limit=50)


@router.get("/log")
def sync_log(db=Depends(get_db), asesor: dict = Depends(get_current_asesor)):
    """Ultimos registros del log de sincronizacion."""
    from app.models.mdl_all import SyncLog
    rows = db.query(SyncLog).order_by(SyncLog.created_at.desc()).limit(20).all()
    return [
        {c.name: getattr(r, c.name) for c in r.__table__.columns}
        for r in rows
    ]


@router.get("/estado")
def estado_sync(db=Depends(get_db), asesor: dict = Depends(get_current_asesor)):
    """Estado de la BD: tablas, pendientes."""
    from sqlalchemy import text
    from app.models.mdl_all import SyncOutbox
    tablas = db.execute(
        text("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
    ).all()
    pendientes = db.query(SyncOutbox).filter(SyncOutbox.estado == "pendiente").count()
    return {
        "motor": "PostgreSQL",
        "tablas": [r[0] for r in tablas],
        "outbox_pendientes": pendientes,
    }
