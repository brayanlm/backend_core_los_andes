from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.cfg_auth import get_current_asesor, requiere_rol
from app.schemas.sch_creditos import (
    SolicitudCreate, SolicitudOut, SolicitudPendienteOut,
    DocumentoIn, DocumentoOut, VisitaIn, VisitaOut,
    AsignarIn, AsignarGenerarIn, ComiteIn, EvaluarIn, AprobarIn,
    CondicionarIn, RechazarIn,
    PreevaluacionOut, BuroConsultaOut,
)
from datetime import date
from app.services import svc_solicitudes
from app.models import SolicitudCredito, Cliente, Asesor, Preevaluacion, BuroConsulta

router = APIRouter()


@router.post("", response_model=SolicitudOut, status_code=201)
def crear_solicitud(
    data: SolicitudCreate,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    try:
        return svc_solicitudes.crear_solicitud(
            db, data, asesor_id=asesor["asesor_id"]
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=list[SolicitudOut])
def listar_solicitudes(
    estado: str = None,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    return svc_solicitudes.listar_solicitudes(db, estado=estado)


@router.get("/pendientes", response_model=list[SolicitudPendienteOut])
def listar_pendientes(
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    from app.models.mdl_all import SolicitudCredito, Cliente
    q = db.query(SolicitudCredito).filter(
        SolicitudCredito.estado.in_(["enviado", "recibido_comite", "en_evaluacion"])
    ).order_by(SolicitudCredito.created_at.asc())
    result = []
    for s in q.all():
        cli = db.query(Cliente).filter(Cliente.id == s.cliente_id).first()
        nombre = f"{cli.nombres} {cli.apellidos}" if cli else ""
        ratio = round((s.cuota_estimada or 0) / max(s.ingresos or 1, 1), 4)
        result.append(SolicitudPendienteOut(
            id=s.id, cliente_id=s.cliente_id, cliente_nombre=nombre,
            monto=s.monto, plazo=s.plazo, ingresos=s.ingresos,
            destino=s.destino_credito, cuota_estimada=s.cuota_estimada,
            estado=s.estado, created_at=s.created_at,
            score_usado=s.score_usado, ratio=ratio,
        ))
    return result


@router.get("/{solicitud_id}", response_model=SolicitudOut)
def obtener_solicitud(
    solicitud_id: str,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    sol = svc_solicitudes.obtener_solicitud(db, solicitud_id)
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    return sol


@router.put("/{solicitud_id}/asignar", response_model=SolicitudOut)
def asignar_solicitud(
    solicitud_id: str,
    data: AsignarIn,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    try:
        return svc_solicitudes.asignar_asesor(db, solicitud_id, data.asesor_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{solicitud_id}/asignar-generar", response_model=SolicitudOut)
def asignar_y_generar_cartera(
    solicitud_id: str,
    data: AsignarGenerarIn,
    db: Session = Depends(get_db),
    asesor: dict = Depends(requiere_rol("ADMIN")),
):
    try:
        asesor_db = db.query(Asesor).filter(
            Asesor.codigo_empleado == data.codigo_empleado
        ).first()
        if not asesor_db:
            raise HTTPException(
                status_code=404,
                detail=f"No se encontró asesor con código '{data.codigo_empleado}'"
            )
        sol = svc_solicitudes.asignar_asesor(db, solicitud_id, asesor_db.id)
        fecha = date.today().isoformat()
        svc_solicitudes.generar_cartera(db, asesor_db.id, fecha)
        return sol
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{solicitud_id}/documentos", response_model=DocumentoOut, status_code=201)
def subir_documento(
    solicitud_id: str,
    data: DocumentoIn,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    try:
        return svc_solicitudes.agregar_documento(
            db, solicitud_id, data.tipo, data.nombre_archivo, data.contenido_base64
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{solicitud_id}/documentos", response_model=list[DocumentoOut])
def listar_documentos(
    solicitud_id: str,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    return svc_solicitudes.listar_documentos(db, solicitud_id)


@router.post("/{solicitud_id}/firma", response_model=SolicitudOut, status_code=201)
def subir_firma(
    solicitud_id: str,
    data: dict,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    firma = data.get("firma_base64", "")
    if not firma:
        raise HTTPException(status_code=400, detail="firma_base64 es requerido")
    try:
        return svc_solicitudes.agregar_firma(db, solicitud_id, firma)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{solicitud_id}/visita", response_model=VisitaOut, status_code=201)
def registrar_visita(
    solicitud_id: str,
    data: VisitaIn,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == solicitud_id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    try:
        return svc_solicitudes.registrar_visita(
            db, solicitud_id, asesor["asesor_id"], sol.cliente_id,
            data.lat, data.lng, data.observacion, data.resultado,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{solicitud_id}/comite", response_model=SolicitudOut)
def enviar_comite(
    solicitud_id: str,
    data: ComiteIn = None,
    db: Session = Depends(get_db),
    asesor: dict = Depends(requiere_rol("ADMIN")),
):
    try:
        return svc_solicitudes.enviar_comite(db, solicitud_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{solicitud_id}/evaluar", response_model=SolicitudOut)
def evaluar_solicitud(
    solicitud_id: str,
    data: EvaluarIn = None,
    db: Session = Depends(get_db),
    asesor: dict = Depends(requiere_rol("ADMIN")),
):
    try:
        return svc_solicitudes.evaluar(db, solicitud_id, data.score if data else None)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{solicitud_id}/aprobar", response_model=dict)
def aprovar_solicitud(
    solicitud_id: str,
    data: AprobarIn = None,
    db: Session = Depends(get_db),
    asesor: dict = Depends(requiere_rol("ADMIN")),
):
    try:
        return svc_solicitudes.aprovar_solicitud(
            db, solicitud_id,
            asesor_id=asesor["asesor_id"],
            asesor_nombre=asesor.get("nombre", ""),
            monto_aprobado=data.monto_aprobado if data else None,
            tasa_final=data.tasa_final if data else None,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{solicitud_id}/condicionar", response_model=SolicitudOut)
def condicionar_solicitud(
    solicitud_id: str,
    data: CondicionarIn,
    db: Session = Depends(get_db),
    asesor: dict = Depends(requiere_rol("ADMIN")),
):
    try:
        return svc_solicitudes.condicionar_solicitud(
            db, solicitud_id, data.condiciones,
            monto_aprobado=data.monto_aprobado,
            tasa_final=data.tasa_final,
            asesor_id=asesor["asesor_id"],
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/{solicitud_id}/rechazar", response_model=SolicitudOut)
def rechazar_solicitud(
    solicitud_id: str,
    data: RechazarIn,
    db: Session = Depends(get_db),
    asesor: dict = Depends(requiere_rol("ADMIN")),
):
    try:
        return svc_solicitudes.rechazar_solicitud(
            db, solicitud_id, data.motivo,
            asesor_id=asesor["asesor_id"],
            asesor_nombre=asesor.get("nombre", ""),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{solicitud_id}/estado-flujo")
def estado_flujo_solicitud(
    solicitud_id: str,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    """Retorna el estado de los gates del flujo de crédito."""
    sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == solicitud_id).first()
    if not sol:
        raise HTTPException(status_code=404, detail="Solicitud no encontrada")
    cli = db.query(Cliente).filter(Cliente.id == sol.cliente_id).first()
    docs_count = db.query(Documento).filter(Documento.solicitud_id == solicitud_id).count()
    return {
        "solicitud_id": solicitud_id,
        "estado": sol.estado,
        "visita_registrada": bool(sol.visita_registrada),
        "preevaluacion_realizada": bool(sol.preevaluacion_realizada),
        "buro_consultado": bool(sol.buro_consultado),
        "documentos_completos": bool(sol.documentos_completos),
        "firma_capturada": bool(sol.firma_capturada),
        "total_documentos_subidos": docs_count,
        "cliente_nombre": f"{cli.nombres} {cli.apellidos}" if cli else "",
        "cliente_documento": cli.numero_documento if cli else "",
        "monto": sol.monto,
        "plazo": sol.plazo,
    }


@router.get("/{solicitud_id}/evaluacion", response_model=PreevaluacionOut)
def obtener_preevaluacion(
    solicitud_id: str,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    """Retorna la pre-evaluación asociada a una solicitud."""
    pre = db.query(Preevaluacion).filter(
        Preevaluacion.solicitud_id == solicitud_id
    ).order_by(Preevaluacion.created_at.desc()).first()
    if not pre:
        raise HTTPException(status_code=404, detail="No existe pre-evaluación para esta solicitud")
    return pre


@router.get("/{solicitud_id}/buro", response_model=BuroConsultaOut)
def obtener_buro(
    solicitud_id: str,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    """Retorna la consulta de buró asociada a una solicitud."""
    buro = db.query(BuroConsulta).filter(
        BuroConsulta.solicitud_id == solicitud_id
    ).order_by(BuroConsulta.created_at.desc()).first()
    if not buro:
        raise HTTPException(status_code=404, detail="No existe consulta de buró para esta solicitud")
    return buro
