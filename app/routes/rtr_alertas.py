from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.database.session import get_db
from app.core.cfg_auth import get_current_asesor
from app.models.mdl_all import AlertaCartera, Cliente

router = APIRouter()


class AlertaOut(BaseModel):
    id: str
    cliente_id: str
    cliente_nombre: str
    tipo_alerta: str
    mensaje: Optional[str] = None
    leida: bool


@router.get("", response_model=list[AlertaOut])
def listar(db=Depends(get_db), asesor: dict = Depends(get_current_asesor)):
    rows = (
        db.query(AlertaCartera, Cliente)
        .join(Cliente, AlertaCartera.cliente_id == Cliente.id)
        .filter(AlertaCartera.asesor_id == asesor["asesor_id"])
        .order_by(AlertaCartera.leida.asc(), AlertaCartera.created_at.desc())
        .all()
    )
    result = []
    for a, cli in rows:
        result.append(AlertaOut(
            id=a.id,
            cliente_id=a.cliente_id,
            cliente_nombre=f"{cli.nombres} {cli.apellidos}",
            tipo_alerta=a.tipo_alerta,
            mensaje=a.mensaje,
            leida=bool(a.leida),
        ))
    return result


@router.get("/no-leidas")
def no_leidas(db=Depends(get_db), asesor: dict = Depends(get_current_asesor)):
    n = (
        db.query(AlertaCartera)
        .filter(
            AlertaCartera.asesor_id == asesor["asesor_id"],
            AlertaCartera.leida == 0,
        )
        .count()
    )
    return {"no_leidas": n}


@router.post("/{alerta_id}/leer")
def marcar_leida(alerta_id: str, db=Depends(get_db), asesor: dict = Depends(get_current_asesor)):
    alerta = (
        db.query(AlertaCartera)
        .filter(
            AlertaCartera.id == alerta_id,
            AlertaCartera.asesor_id == asesor["asesor_id"],
        )
        .first()
    )
    if alerta:
        alerta.leida = 1
        db.commit()
    return {"status": "ok"}
