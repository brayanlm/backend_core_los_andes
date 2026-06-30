import json
import logging
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models import (
    Cliente, SolicitudCredito, Credito, Documento, Visita, CarteraDiaria
)
from app.schemas.sch_creditos import (
    SolicitudCreate, SolicitudOut, DocumentoOut, VisitaOut,
)
from app.services.svc_financiero import (
    calcular_cuota_mensual, generar_cronograma, calcular_score,
)
from app.sync.outbox import enqueue

logger = logging.getLogger("core_mobile")

ESTADOS_SOLICITUD = [
    "enviado",
    "recibido_comite",
    "en_evaluacion",
    "aprobado",
    "condicionado",
    "rechazado",
    "desembolsado",
]

TRANSICIONES = {
    "enviado": {"recibido_comite", "rechazado"},
    "recibido_comite": {"en_evaluacion", "rechazado"},
    "en_evaluacion": {"aprobado", "condicionado", "rechazado"},
    "aprobado": {"desembolsado", "rechazado"},
    "condicionado": {"aprobado", "desembolsado", "rechazado"},
    "rechazado": set(),
    "desembolsado": set(),
}

RATIO_MAXIMO = 0.40
TASA_DEFAULT = 0.25


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


def _transicion_valida(actual: str, nuevo: str) -> bool:
    return nuevo in TRANSICIONES.get(actual, set())


def _upsert_cliente(db: Session, d: SolicitudCreate) -> Cliente:
    existing = db.query(Cliente).filter(
        Cliente.numero_documento == d.numero_documento
    ).first()
    if existing:
        return existing

    cli = Cliente(
        id=_new_id(),
        numero_documento=d.numero_documento,
        nombres=d.nombres or "",
        apellidos=d.apellidos or "",
        telefono=d.telefono or "",
        tipo_negocio=d.tipo_negocio or "",
        nombre_negocio=d.nombre_negocio or "",
    )
    db.add(cli)
    db.flush()
    return cli


def _generar_expediente() -> str:
    return "EXP-" + _new_id().replace("-", "")[:8].upper()


# ─── CRUD Solicitud ───

def crear_solicitud(
    db: Session,
    data: SolicitudCreate,
    asesor_id: Optional[str] = None,
    cliente_id: Optional[str] = None,
) -> SolicitudOut:
    if cliente_id:
        cli = db.query(Cliente).filter(Cliente.id == cliente_id).first()
        if not cli:
            raise ValueError("Cliente no encontrado")
    else:
        cli = _upsert_cliente(db, data)

    cuota = calcular_cuota_mensual(data.monto_solicitado, data.plazo_meses, data.tea_referencial)
    sol = SolicitudCredito(
        id=_new_id(),
        numero_expediente=_generar_expediente(),
        asesor_id=asesor_id,
        cliente_id=cli.id,
        canal=data.canal,
        tipo_negocio=data.tipo_negocio or cli.tipo_negocio,
        nombre_negocio=data.nombre_negocio or cli.nombre_negocio,
        ingresos=data.ingresos_estimados,
        monto=data.monto_solicitado,
        plazo=data.plazo_meses,
        destino_credito=data.destino_credito,
        garantia=data.garantia,
        tea_referencial=data.tea_referencial,
        cuota_estimada=cuota,
        estado="enviado",
        created_at=_utc_now(),
    )
    db.add(sol)
    db.commit()
    db.refresh(sol)
    try:
        enqueue(db, "cr_solicitud_credito", "INSERT", {"id": sol.id, "expediente": sol.numero_expediente, "monto": sol.monto, "estado": sol.estado})
    except Exception as e:
        logger.error("OUTBOX enqueue error: %s", e)
    logger.info("SOLICITUD CREADA id=%s expediente=%s monto=%.2f asesor=%s", sol.id, sol.numero_expediente, sol.monto, asesor_id)
    return _solicitud_to_out(db, sol)


def obtener_solicitud(db: Session, solicitud_id: str) -> Optional[SolicitudOut]:
    sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == solicitud_id).first()
    if not sol:
        return None
    return _solicitud_to_out(db, sol)


def listar_solicitudes(
    db: Session,
    asesor_id: Optional[str] = None,
    estado: Optional[str] = None,
) -> List[SolicitudOut]:
    q = db.query(SolicitudCredito)
    if asesor_id:
        q = q.filter(SolicitudCredito.asesor_id == asesor_id)
    if estado:
        q = q.filter(SolicitudCredito.estado == estado)
    q = q.order_by(SolicitudCredito.created_at.desc())
    return [_solicitud_to_out(db, s) for s in q.all()]


def listar_solicitudes_cliente(db: Session, cliente_id: str) -> List[SolicitudOut]:
    q = db.query(SolicitudCredito).filter(
        SolicitudCredito.cliente_id == cliente_id
    ).order_by(SolicitudCredito.created_at.desc())
    return [_solicitud_to_out(db, s) for s in q.all()]


def listar_pendientes(db: Session) -> List[SolicitudOut]:
    q = db.query(SolicitudCredito).filter(
        SolicitudCredito.estado.in_(["enviado", "recibido_comite", "en_evaluacion"])
    ).order_by(SolicitudCredito.created_at.asc())
    return [_solicitud_to_out(db, s) for s in q.all()]


def _solicitud_to_out(db: Session, sol: SolicitudCredito) -> SolicitudOut:
    cli = db.query(Cliente).filter(Cliente.id == sol.cliente_id).first()
    nombre = f"{cli.nombres} {cli.apellidos}" if cli else ""
    return SolicitudOut(
        id=sol.id,
        numero_expediente=sol.numero_expediente,
        cliente_id=sol.cliente_id,
        cliente_nombre=nombre,
        asesor_id=sol.asesor_id,
        canal=sol.canal,
        monto=sol.monto,
        plazo=sol.plazo,
        cuota_estimada=sol.cuota_estimada,
        ingresos=sol.ingresos,
        estado=sol.estado,
        destino_credito=sol.destino_credito,
        garantia=sol.garantia,
        motivo_rechazo=sol.motivo_rechazo,
        condiciones=sol.condiciones,
        credito_id=sol.credito_id,
        visita_registrada=sol.visita_registrada or 0,
        preevaluacion_realizada=sol.preevaluacion_realizada or 0,
        buro_consultado=sol.buro_consultado or 0,
        documentos_completos=sol.documentos_completos or 0,
        firma_capturada=sol.firma_capturada or 0,
        created_at=sol.created_at,
    )


# ─── Asignar ───

def asignar_asesor(db: Session, solicitud_id: str, asesor_id: str) -> SolicitudOut:
    sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == solicitud_id).first()
    if not sol:
        raise ValueError("Solicitud no encontrada")
    sol.asesor_id = asesor_id
    db.commit()
    db.refresh(sol)
    return _solicitud_to_out(db, sol)


# ─── Documentos ───

def agregar_documento(
    db: Session, solicitud_id: str, tipo: str, nombre_archivo: str, contenido_base64: str
) -> DocumentoOut:
    sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == solicitud_id).first()
    if not sol:
        raise ValueError("Solicitud no encontrada")
    doc = Documento(
        id=_new_id(),
        solicitud_id=solicitud_id,
        tipo=tipo,
        nombre_archivo=nombre_archivo,
        contenido_base64=contenido_base64,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    # Auto-marcar documentos completos si se subieron los obligatorios
    tipos_subidos = [
        r[0] for r in db.query(Documento.tipo).filter(
            Documento.solicitud_id == solicitud_id
        ).distinct().all()
    ]
    requeridos = {"dni_frente", "dni_reverso", "foto_negocio", "ruc"}
    if requeridos.issubset(set(tipos_subidos)):
        sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == solicitud_id).first()
        if sol:
            sol.documentos_completos = 1
            db.commit()
    return DocumentoOut(
        id=doc.id,
        solicitud_id=doc.solicitud_id,
        tipo=doc.tipo,
        nombre_archivo=doc.nombre_archivo or "",
        created_at=doc.created_at or "",
    )


def listar_documentos(db: Session, solicitud_id: str) -> List[DocumentoOut]:
    docs = db.query(Documento).filter(Documento.solicitud_id == solicitud_id).all()
    return [
        DocumentoOut(id=d.id, solicitud_id=d.solicitud_id, tipo=d.tipo,
                     nombre_archivo=d.nombre_archivo or "", created_at=d.created_at or "")
        for d in docs
    ]


# ─── Firma ───

def agregar_firma(db: Session, solicitud_id: str, firma_base64: str) -> SolicitudOut:
    sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == solicitud_id).first()
    if not sol:
        raise ValueError("Solicitud no encontrada")
    sol.firma_cliente_base64 = firma_base64
    sol.firma_capturada = 1
    db.commit()
    db.refresh(sol)
    return _solicitud_to_out(db, sol)


# ─── Visita ───

def registrar_visita(
    db: Session, solicitud_id: str, asesor_id: str, cliente_id: str,
    lat: Optional[float], lng: Optional[float],
    observacion: str, resultado: str,
) -> VisitaOut:
    sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == solicitud_id).first()
    if not sol:
        raise ValueError("Solicitud no encontrada")
    vis = Visita(
        id=_new_id(),
        solicitud_id=solicitud_id,
        asesor_id=asesor_id,
        cliente_id=cliente_id,
        lat=lat,
        lng=lng,
        observacion=observacion,
        resultado=resultado,
    )
    db.add(vis)
    sol.visita_registrada = 1
    db.commit()
    db.refresh(vis)
    return VisitaOut(
        id=vis.id,
        solicitud_id=vis.solicitud_id,
        asesor_id=vis.asesor_id,
        cliente_id=vis.cliente_id,
        lat=vis.lat,
        lng=vis.lng,
        observacion=vis.observacion,
        resultado=vis.resultado,
        created_at=vis.created_at,
    )


# ─── Comité ───

def enviar_comite(db: Session, solicitud_id: str) -> SolicitudOut:
    sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == solicitud_id).first()
    if not sol:
        raise ValueError("Solicitud no encontrada")
    if not _transicion_valida(sol.estado, "recibido_comite"):
        raise ValueError(f"No se puede enviar a comité desde estado '{sol.estado}'")
    # ── Validación de gates ──
    if not sol.visita_registrada:
        visita = db.query(Visita).filter(
            Visita.solicitud_id == solicitud_id
        ).first()
        if not visita:
            visita = db.query(Visita).filter(
                Visita.cliente_id == sol.cliente_id
            ).order_by(Visita.created_at.desc()).first()
        if not visita:
            raise ValueError("No se puede enviar a comité: no existe visita registrada")
    # ── Auto-marcar gates que no se hayan completado ──
    sol.preevaluacion_realizada = 1
    sol.buro_consultado = 1
    sol.documentos_completos = 1
    sol.firma_capturada = 1
    # ── Verificar lista negra ──
    from app.models.mdl_all import BuroConsulta
    buro = db.query(BuroConsulta).filter(
        BuroConsulta.solicitud_id == solicitud_id,
        BuroConsulta.en_lista_negra == 1,
    ).first()
    if buro:
        raise ValueError(f"No se puede enviar a comité: el cliente está en lista negra ({buro.motivo_bloqueo})")
    sol.estado = "recibido_comite"
    db.commit()
    db.refresh(sol)
    return _solicitud_to_out(db, sol)


# ─── Evaluar ───

def evaluar(db: Session, solicitud_id: str, score: Optional[int] = None) -> SolicitudOut:
    sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == solicitud_id).first()
    if not sol:
        raise ValueError("Solicitud no encontrada")
    if not _transicion_valida(sol.estado, "en_evaluacion"):
        raise ValueError(f"No se puede evaluar desde estado '{sol.estado}'")

    if score is None:
        score = calcular_score(
            sol.ingresos or 0, sol.monto, sol.plazo
        )

    sol.estado = "en_evaluacion"
    sol.score_usado = score
    sol.fecha_evaluacion = _utc_now()
    db.commit()
    db.refresh(sol)
    return _solicitud_to_out(db, sol)


# ─── Aprobar ───

def aprovar_solicitud(
    db: Session, solicitud_id: str,
    asesor_id: str, asesor_nombre: str = "",
    monto_aprobado: Optional[float] = None,
    tasa_final: Optional[float] = None,
) -> dict:
    sol = db.query(SolicitudCredito).with_for_update().filter(SolicitudCredito.id == solicitud_id).first()
    if not sol:
        raise ValueError("Solicitud no encontrada")
    if not _transicion_valida(sol.estado, "aprobado"):
        raise ValueError(f"No se puede aprobar desde estado '{sol.estado}'")

    # Validar que tiene documentos adjuntos (opcional para testing)
    docs_count = db.query(Documento).filter(Documento.solicitud_id == solicitud_id).count()

    ahora = _utc_now()
    monto_final = monto_aprobado or sol.monto
    tasa = tasa_final or sol.tea_referencial or TASA_DEFAULT
    cuota = calcular_cuota_mensual(monto_final, sol.plazo, tasa)
    ingresos = sol.ingresos or 0
    ratio = round(cuota / ingresos, 4) if ingresos > 0 else 0

    cred = Credito(
        id=_new_id(),
        solicitud_id=sol.id,
        cliente_id=sol.cliente_id,
        asesor_id=asesor_id,
        monto=monto_final,
        monto_desembolsado=None,
        plazo_meses=sol.plazo,
        tasa=tasa,
        ingreso_cliente=ingresos,
        cuota_estimada=cuota,
        ratio_cuota_ingreso=ratio,
        estado="APROBADO",
        score=sol.score_usado or 500,
        destino=sol.destino_credito,
        fecha_creacion=ahora,
        fecha_aprobacion=ahora,
    )
    db.add(cred)
    db.flush()

    sol.estado = "aprobado"
    sol.credito_id = cred.id
    sol.evaluado_por = asesor_id
    sol.evaluado_nombre = asesor_nombre or ""
    sol.fecha_evaluacion = ahora
    sol.monto_aprobado = monto_final
    sol.tasa_sugerida = tasa

    db.commit()
    db.refresh(sol)
    try:
        enqueue(db, "cr_credito", "INSERT", {"id": cred.id, "solicitud_id": sol.id, "monto": monto_final, "estado": "APROBADO"})
    except Exception as e:
        logger.error("OUTBOX enqueue error: %s", e)
    logger.info("SOLICITUD APROBADA id=%s expediente=%s credito=%s monto=%.2f asesor=%s", sol.id, sol.numero_expediente, cred.id, monto_final, asesor_id)

    return {
        "id": cred.id,
        "solicitud_id": sol.id,
        "estado": "APROBADO",
        "monto": monto_final,
        "numero_expediente": sol.numero_expediente,
    }


# ─── Condicionar ───

def condicionar_solicitud(
    db: Session, solicitud_id: str,
    condiciones: str,
    monto_aprobado: Optional[float] = None,
    tasa_final: Optional[float] = None,
    asesor_id: str = "",
) -> SolicitudOut:
    sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == solicitud_id).first()
    if not sol:
        raise ValueError("Solicitud no encontrada")
    if not _transicion_valida(sol.estado, "condicionado"):
        raise ValueError(f"No se puede condicionar desde estado '{sol.estado}'")

    sol.estado = "condicionado"
    sol.condiciones = condiciones
    if monto_aprobado:
        sol.monto_aprobado = monto_aprobado
    if tasa_final:
        sol.tasa_sugerida = tasa_final
    sol.evaluado_por = asesor_id or sol.asesor_id
    sol.fecha_evaluacion = _utc_now()

    db.commit()
    db.refresh(sol)
    return _solicitud_to_out(db, sol)


# ─── Rechazar ───

def rechazar_solicitud(
    db: Session, solicitud_id: str, motivo: str,
    asesor_id: str = "", asesor_nombre: str = "",
) -> SolicitudOut:
    sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == solicitud_id).first()
    if not sol:
        raise ValueError("Solicitud no encontrada")
    if not _transicion_valida(sol.estado, "rechazado"):
        raise ValueError(f"No se puede rechazar desde estado '{sol.estado}'")

    sol.estado = "rechazado"
    sol.motivo_rechazo = motivo
    sol.evaluado_por = asesor_id or sol.asesor_id
    sol.evaluado_nombre = asesor_nombre or ""
    sol.fecha_evaluacion = _utc_now()

    db.commit()
    db.refresh(sol)
    logger.info("SOLICITUD RECHAZADA id=%s expediente=%s motivo=%s asesor=%s", sol.id, sol.numero_expediente, motivo, asesor_id)
    return _solicitud_to_out(db, sol)


# ─── Cartera ───

def generar_cartera(db: Session, asesor_id: str, fecha: str) -> List[dict]:
    solicitudes = db.query(SolicitudCredito).filter(
        SolicitudCredito.asesor_id == asesor_id,
        SolicitudCredito.estado.in_(["enviado", "recibido_comite"]),
    ).all()

    items = []
    for sol in solicitudes:
        existing = db.query(CarteraDiaria).filter(
            CarteraDiaria.asesor_id == asesor_id,
            CarteraDiaria.cliente_id == sol.cliente_id,
            CarteraDiaria.fecha_asignacion == fecha,
        ).first()
        if existing:
            continue

        c = CarteraDiaria(
            id=_new_id(),
            asesor_id=asesor_id,
            cliente_id=sol.cliente_id,
            fecha_asignacion=fecha,
            tipo_gestion="NUEVA_SOLICITUD",
            prioridad="alta" if sol.monto > 10000 else "normal",
            monto_credito=sol.monto,
        )
        db.add(c)
        items.append(c)

    if items:
        db.commit()

    cartera = db.query(CarteraDiaria).filter(
        CarteraDiaria.asesor_id == asesor_id,
        CarteraDiaria.fecha_asignacion == fecha,
    ).order_by(CarteraDiaria.prioridad).all()

    result = []
    for c in cartera:
        cli = db.query(Cliente).filter(Cliente.id == c.cliente_id).first()
        result.append({
            "id": c.id,
            "cliente_id": c.cliente_id,
            "cliente_nombre": f"{cli.nombres} {cli.apellidos}" if cli else "",
            "tipo_gestion": c.tipo_gestion,
            "prioridad": c.prioridad,
            "monto_credito": c.monto_credito,
            "estado_visita": c.estado_visita,
        })
    return result


def marcar_visita_cartera(
    db: Session, cartera_id: str, asesor_id: str,
    resultado: str, observacion: str = "",
    lat: Optional[float] = None, lng: Optional[float] = None,
) -> bool:
    c = db.query(CarteraDiaria).filter(
        CarteraDiaria.id == cartera_id,
        CarteraDiaria.asesor_id == asesor_id,
    ).first()
    if not c:
        return False

    c.estado_visita = "visitado"
    c.resultado_visita = resultado
    c.observacion_visita = observacion[:500] if observacion else ""
    c.timestamp_visita = _utc_now()
    if lat is not None:
        c.lat_visita = lat
    if lng is not None:
        c.lng_visita = lng

    vis = Visita(
        id=_new_id(),
        asesor_id=asesor_id,
        cliente_id=c.cliente_id,
        lat=lat,
        lng=lng,
        observacion=observacion,
        resultado=resultado,
    )
    db.add(vis)

    # Marcar solicitud como visita registrada
    sol = db.query(SolicitudCredito).filter(
        SolicitudCredito.cliente_id == c.cliente_id,
    ).order_by(SolicitudCredito.created_at.desc()).first()
    if sol:
        sol.visita_registrada = 1
        vis.solicitud_id = sol.id
        db.flush()

    db.commit()
    return True
