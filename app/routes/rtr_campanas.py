from datetime import date
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from app.database.session import get_db
from app.core.cfg_auth import get_current_asesor
from app.models.mdl_all import CampanaActiva, Cliente

router = APIRouter()


class CampanaOut(BaseModel):
    id: str
    cliente_id: str
    cliente_nombre: str
    tipo: Optional[str] = None
    monto_ofertado: float
    fecha_vencimiento: Optional[str] = None
    dias_restantes: int


@router.get("", response_model=list[CampanaOut])
def listar(db=Depends(get_db), asesor: dict = Depends(get_current_asesor)):
    hoy = date.today()
    rows = (
        db.query(CampanaActiva, Cliente)
        .join(Cliente, CampanaActiva.cliente_id == Cliente.id)
        .filter(
            CampanaActiva.asesor_id == asesor["asesor_id"],
            CampanaActiva.activa == 1,
        )
        .order_by(CampanaActiva.created_at.desc())
        .all()
    )
    result = []
    for ca, cli in rows:
        fv = ca.fecha_vencimiento
        if fv and fv < hoy.isoformat():
            continue
        dias_rest = 0
        if fv:
            try:
                fv_date = date.fromisoformat(fv)
                dias_rest = (fv_date - hoy).days
            except (ValueError, TypeError):
                pass
        result.append(CampanaOut(
            id=ca.id,
            cliente_id=ca.cliente_id,
            cliente_nombre=f"{cli.nombres} {cli.apellidos}",
            tipo=ca.tipo,
            monto_ofertado=float(ca.monto_ofertado or 0),
            fecha_vencimiento=fv,
            dias_restantes=dias_rest,
        ))
    result.sort(key=lambda x: x.dias_restantes if x.fecha_vencimiento else 999)
    return result
