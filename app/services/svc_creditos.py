import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from app.models import Cliente, Credito, SolicitudCredito, CronogramaPago, Asesor
from app.schemas.sch_creditos import CreditoOut, CronogramaCuotaOut, DesembolsarOut
from app.services.svc_financiero import generar_cronograma
from app.sync.outbox import enqueue

logger = logging.getLogger("core_mobile")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


def listar_creditos(
    db: Session, asesor_id: Optional[str] = None, estado: Optional[str] = None
) -> List[CreditoOut]:
    q = db.query(Credito).options(
        joinedload(Credito.cliente), joinedload(Credito.asesor)
    )
    if asesor_id:
        q = q.filter(Credito.asesor_id == asesor_id)
    if estado:
        q = q.filter(Credito.estado == estado)
    q = q.order_by(Credito.fecha_creacion.desc())

    result = []
    for c in q.all():
        cli = c.cliente
        asesor = c.asesor
        result.append(CreditoOut(
            id=c.id,
            solicitud_id=c.solicitud_id,
            cliente_id=c.cliente_id,
            cliente_nombre=f"{cli.nombres} {cli.apellidos}" if cli else "",
            asesor_id=c.asesor_id,
            asesor_nombre=f"{asesor.nombres} {asesor.apellidos}" if asesor else "",
            monto=c.monto,
            monto_desembolsado=c.monto_desembolsado,
            plazo_meses=c.plazo_meses,
            tasa=c.tasa,
            cuota_estimada=c.cuota_estimada,
            estado=c.estado,
            destino=c.destino,
            fecha_creacion=c.fecha_creacion,
            fecha_aprobacion=c.fecha_aprobacion,
            fecha_desembolso=c.fecha_desembolso,
        ))
    return result


def obtener_credito(db: Session, credito_id: str) -> Optional[CreditoOut]:
    c = db.query(Credito).options(
        joinedload(Credito.cliente), joinedload(Credito.asesor)
    ).filter(Credito.id == credito_id).first()
    if not c:
        return None
    cli = c.cliente
    asesor = c.asesor
    return CreditoOut(
        id=c.id,
        solicitud_id=c.solicitud_id,
        cliente_id=c.cliente_id,
        cliente_nombre=f"{cli.nombres} {cli.apellidos}" if cli else "",
        asesor_id=c.asesor_id,
        asesor_nombre=f"{asesor.nombres} {asesor.apellidos}" if asesor else "",
        monto=c.monto,
        monto_desembolsado=c.monto_desembolsado,
        plazo_meses=c.plazo_meses,
        tasa=c.tasa,
        cuota_estimada=c.cuota_estimada,
        estado=c.estado,
        destino=c.destino,
        fecha_creacion=c.fecha_creacion,
        fecha_aprobacion=c.fecha_aprobacion,
        fecha_desembolso=c.fecha_desembolso,
    )


def desembolsar(
    db: Session, credito_id: str, cuenta_destino: str = ""
) -> DesembolsarOut:
    cred = db.query(Credito).with_for_update().filter(Credito.id == credito_id).first()
    if not cred:
        raise ValueError("Crédito no encontrado")

    if cred.estado not in ("APROBADO", "aprobado"):
        raise ValueError(f"El crédito está en estado '{cred.estado}', no se puede desembolsar")

    # Validar que la solicitud asociada esté aprobada
    if cred.solicitud_id:
        sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == cred.solicitud_id).first()
        if sol and sol.estado not in ("aprobado", "condicionado"):
            raise ValueError(f"La solicitud asociada está en estado '{sol.estado}', no se puede desembolsar")

    ahora = _utc_now()
    monto = cred.monto
    plazo = cred.plazo_meses
    tea = cred.tasa or 0.25

    # Generar cronograma
    cuotas, total_interes, total_pagar = generar_cronograma(monto, plazo, tea, ahora)

    # Crear cuotas
    for c in cuotas:
        cup = CronogramaPago(
            id=_new_id(),
            credito_id=credito_id,
            nro_cuota=c["nro_cuota"],
            fecha_vencimiento=c["fecha_vencimiento"],
            monto_cuota=c["monto_cuota"],
            monto_capital=c["monto_capital"],
            monto_interes=c["monto_interes"],
            saldo=c["saldo"],
            estado_cuota="pendiente",
        )
        db.add(cup)

    # Actualizar crédito
    cred.estado = "DESEMBOLSADO"
    cred.monto_desembolsado = monto
    cred.saldo_capital = monto
    cred.saldo_total = total_pagar
    cred.cuotas_total = plazo
    cred.cuotas_pagadas = 0
    cred.fecha_desembolso = ahora

    # Actualizar solicitud asociada
    if cred.solicitud_id:
        sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == cred.solicitud_id).first()
        if sol:
            sol.estado = "desembolsado"

    db.commit()
    try:
        enqueue(db, "cr_credito", "UPDATE", {"id": cred.id, "estado": "DESEMBOLSADO", "monto": monto, "cuotas": plazo})
    except Exception as e:
        logger.error("OUTBOX enqueue error: %s", e)
    logger.info("CREDITO DESEMBOLSADO id=%s monto=%.2f plazo=%d meses cuenta=%s", cred.id, monto, plazo, cuenta_destino)

    return DesembolsarOut(
        id=cred.id,
        estado="DESEMBOLSADO",
        monto_desembolsado=monto,
        total_cuotas=plazo,
        mensaje=f"Crédito desembolsado por S/ {monto:,.2f} a {plazo} meses",
    )


def obtener_cronograma(db: Session, credito_id: str) -> List[CronogramaCuotaOut]:
    cuotas = db.query(CronogramaPago).filter(
        CronogramaPago.credito_id == credito_id
    ).order_by(CronogramaPago.nro_cuota).all()

    return [
        CronogramaCuotaOut(
            nro_cuota=c.nro_cuota,
            fecha_vencimiento=c.fecha_vencimiento,
            monto_cuota=c.monto_cuota or 0,
            monto_capital=c.monto_capital or 0,
            monto_interes=c.monto_interes or 0,
            saldo=c.saldo or 0,
            estado_cuota=c.estado_cuota or "pendiente",
        )
        for c in cuotas
    ]


def obtener_stats(db: Session) -> dict:
    total = db.query(Credito).count()
    vigentes = db.query(Credito).filter(
        Credito.estado.in_(["APROBADO", "DESEMBOLSADO"])
    ).count()
    mora = db.query(Credito).filter(Credito.dias_mora > 30).count()
    monto_total = db.query(Credito.monto).filter(
        Credito.estado == "DESEMBOLSADO"
    ).all()
    total_monto = sum(r[0] or 0 for r in monto_total)
    return {
        "total": total,
        "vigentes": vigentes,
        "mora": mora,
        "monto_total": round(total_monto, 2),
    }
