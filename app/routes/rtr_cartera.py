import logging
from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.cfg_auth import get_current_asesor, requiere_rol
from app.schemas.sch_cartera import CarteraItemOut, MarcarVisitaIn
from app.services import svc_solicitudes

logger = logging.getLogger("core_mobile")

router = APIRouter()


@router.post("/generar")
def generar_cartera(
    fecha: date = None,
    db: Session = Depends(get_db),
    asesor: dict = Depends(requiere_rol("ADMIN")),
):
    f = (fecha or date.today()).isoformat()
    items = svc_solicitudes.generar_cartera(db, asesor["asesor_id"], f)
    return {"status": "ok", "items": len(items), "fecha": f}


@router.get("", response_model=list[CarteraItemOut])
def listar_cartera(
    fecha: date = None,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    from app.models import CarteraDiaria, Cliente, Asesor
    f = date.today().isoformat()
    aid = asesor["asesor_id"]
    q = db.query(CarteraDiaria).filter(
        CarteraDiaria.asesor_id == aid,
        CarteraDiaria.fecha_asignacion == f,
    )
    logger.info(
        "CARTERA: asesor_id=%s fecha=%s total_en_db=%d",
        aid, f, q.count(),
    )
    cartera = q.order_by(CarteraDiaria.prioridad).all()

    result = []
    for c in cartera:
        cli = db.query(Cliente).filter(Cliente.id == c.cliente_id).first()
        result.append(CarteraItemOut(
            id=c.id,
            cliente_id=c.cliente_id,
            cliente_nombre=f"{cli.nombres} {cli.apellidos}" if cli else "",
            documento=cli.numero_documento if cli else "",
            tipo_gestion=c.tipo_gestion or "",
            prioridad=c.prioridad or "normal",
            score_prioridad=c.score_prioridad or 0,
            monto_credito=c.monto_credito or 0,
            estado_visita=c.estado_visita or "pendiente",
            orden_manual=c.orden_manual,
            lat=c.lat,
            lng=c.lng,
            asesor_id=c.asesor_id,
            fecha_asignacion=c.fecha_asignacion,
        ))
    return result


@router.post("/{cartera_id}/visita")
def marcar_visita(
    cartera_id: str,
    data: MarcarVisitaIn,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    ok = svc_solicitudes.marcar_visita_cartera(
        db, cartera_id, asesor["asesor_id"],
        resultado=data.resultado,
        observacion=data.observacion or "",
        lat=data.lat,
        lng=data.lng,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Item de cartera no encontrado")
    return {"status": "ok", "cartera_id": cartera_id, "estado_visita": data.resultado}
