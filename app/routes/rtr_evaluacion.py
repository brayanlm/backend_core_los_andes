from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.cfg_auth import get_current_asesor
from app.models.mdl_all import Preevaluacion, SolicitudCredito, Cliente
from app.schemas.sch_creditos import PreevaluacionOut
from app.services.svc_financiero import calcular_cuota_mensual, calcular_score
import uuid
from datetime import datetime, timezone

router = APIRouter()


class PreEvalIn(BaseModel):
    solicitud_id: str


@router.post("/pre-evaluar", response_model=PreevaluacionOut)
def pre_evaluar_solicitud(
    data: PreEvalIn,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    """Pre-evaluación crediticia integrada al flujo de solicitud.
    Usa datos reales de la solicitud y persiste el resultado en PostgreSQL.
    """
    sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == data.solicitud_id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")

    cli = db.query(Cliente).filter(Cliente.id == sol.cliente_id).first()

    ingreso = sol.ingresos or 0
    gasto = 0
    monto = sol.monto
    plazo = sol.plazo
    antiguedad = cli.antiguedad_negocio_meses or 0 if cli else 0

    cuota = calcular_cuota_mensual(monto, plazo, sol.tea_referencial)
    ingreso_neto = max(ingreso - gasto, 1)
    ratio = round(cuota / ingreso_neto, 4) if ingreso_neto > 0 else 99
    score = calcular_score(ingreso, monto, plazo) if ingreso > 0 else 0

    observaciones = []
    puntaje = 0

    if ingreso <= 0:
        resultado = "REVISAR"
        puntaje = 50
        observaciones.append("Ingresos no declarados; requiere análisis adicional.")
    elif ratio <= 0.35 and antiguedad >= 12:
        resultado = "APTO"
        puntaje = 85 + min(score // 10, 15)
        observaciones.append("Capacidad de pago suficiente. Negocio con antigüedad adecuada.")
    elif ratio <= 0.35:
        resultado = "APTO"
        puntaje = 75 + min(score // 10, 10)
        observaciones.append("Capacidad de pago suficiente. Verificar antigüedad del negocio.")
    elif ratio <= 0.50 and antiguedad >= 6:
        resultado = "REVISAR"
        puntaje = 60
        observaciones.append(f"Ratio cuota/ingreso de {ratio:.1%}. Antigüedad aceptable.")
    elif ratio <= 0.50:
        resultado = "REVISAR"
        puntaje = 55
        observaciones.append(f"Ratio cuota/ingreso de {ratio:.1%}. Requiere garantía adicional.")
    elif ratio <= 0.70 and antiguedad >= 24:
        resultado = "REVISAR"
        puntaje = 50
        observaciones.append(f"Ratio elevado ({ratio:.1%}) pero negocio consolidado.")
    else:
        resultado = "NO_PROCEDE"
        puntaje = max(25, 40 - int(ratio * 20))
        observaciones.append(f"El monto supera la capacidad de pago (ratio {ratio:.1%}).")

    if antiguedad < 6 and resultado != "NO_PROCEDE":
        observaciones.append("Negocio con menos de 6 meses de antigüedad.")
        puntaje = max(puntaje - 10, 20)

    now = datetime.now(timezone.utc).isoformat()
    pre = Preevaluacion(
        id=str(uuid.uuid4()),
        solicitud_id=data.solicitud_id,
        asesor_id=asesor.get("asesor_id"),
        cliente_id=sol.cliente_id,
        ingreso_mensual=ingreso,
        gasto_mensual=gasto,
        monto_solicitado=monto,
        plazo=plazo,
        cuota_estimada=cuota,
        antiguedad_negocio_meses=antiguedad,
        score=score,
        resultado=resultado,
        puntaje=puntaje,
        ratio_cuota_ingreso=ratio,
        observaciones=" | ".join(observaciones),
        created_at=now,
    )
    db.add(pre)
    sol.preevaluacion_realizada = 1
    db.commit()
    db.refresh(pre)

    return PreevaluacionOut(
        id=pre.id,
        solicitud_id=pre.solicitud_id,
        asesor_id=pre.asesor_id,
        cliente_id=pre.cliente_id,
        ingreso_mensual=pre.ingreso_mensual,
        gasto_mensual=pre.gasto_mensual,
        monto_solicitado=pre.monto_solicitado,
        plazo=pre.plazo,
        cuota_estimada=pre.cuota_estimada,
        antiguedad_negocio_meses=pre.antiguedad_negocio_meses,
        score=pre.score,
        resultado=pre.resultado,
        puntaje=pre.puntaje,
        ratio_cuota_ingreso=pre.ratio_cuota_ingreso,
        observaciones=pre.observaciones,
        created_at=pre.created_at,
    )
