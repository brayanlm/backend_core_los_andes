from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.cfg_auth import get_current_cliente
from app.schemas.sch_cliente import (
    LoginClienteIn, TokenClienteOut, ClienteOut, CuentaAhorroOut, CreditoOut,
    CuotaOut, MovimientoOut, TarjetaOut, NotificacionOut, OperacionIn, OperacionOut,
    RegisterClienteIn, SolicitudClienteIn,
    DestinatarioOut, TransferirIn, YapeIn, PagoCuotaIn, RecargaIn,
    ServicioPagoIn, ComprobanteOut,
)
from app.schemas.sch_creditos import SolicitudCreate, SolicitudOut
from app.controllers import ctl_auth_cliente
from app.repositories import rep_cliente
from app.models.mdl_all import Cliente
from app.services import svc_solicitudes

router = APIRouter()


@router.post("/login", response_model=TokenClienteOut)
def login(data: LoginClienteIn, db: Session = Depends(get_db)):
    result = ctl_auth_cliente.login(db, data.numero_documento, data.password)
    if result and result.get("_bloqueado"):
        raise HTTPException(status_code=423, detail="Usuario bloqueado por intentos fallidos")
    if not result:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")
    return result


@router.post("/register", response_model=TokenClienteOut)
def register(data: RegisterClienteIn, db: Session = Depends(get_db)):
    result = ctl_auth_cliente.register(db, data)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/perfil", response_model=ClienteOut)
def perfil(db: Session = Depends(get_db), cli: dict = Depends(get_current_cliente)):
    cliente = rep_cliente.get_cliente(db, cli["cliente_id"])
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.get("/cuentas", response_model=list[CuentaAhorroOut])
def cuentas(db: Session = Depends(get_db), cli: dict = Depends(get_current_cliente)):
    return rep_cliente.cuentas_ahorro(db, cli["cliente_id"])


@router.get("/creditos", response_model=list[CreditoOut])
def creditos(db: Session = Depends(get_db), cli: dict = Depends(get_current_cliente)):
    return rep_cliente.creditos(db, cli["cliente_id"])


@router.get("/creditos/{credito_id}/cronograma", response_model=list[CuotaOut])
def cronograma(
    credito_id: str,
    db: Session = Depends(get_db),
    cli: dict = Depends(get_current_cliente),
):
    return rep_cliente.cronograma(db, credito_id)


@router.get("/movimientos", response_model=list[MovimientoOut])
def movimientos(
    limit: int = 20,
    db: Session = Depends(get_db),
    cli: dict = Depends(get_current_cliente),
):
    return rep_cliente.movimientos(db, cli["cliente_id"], limit)


@router.get("/tarjetas", response_model=list[TarjetaOut])
def tarjetas(db: Session = Depends(get_db), cli: dict = Depends(get_current_cliente)):
    return rep_cliente.tarjetas(db, cli["cliente_id"])


@router.get("/notificaciones", response_model=list[NotificacionOut])
def notificaciones(db: Session = Depends(get_db), cli: dict = Depends(get_current_cliente)):
    return rep_cliente.notificaciones(db, cli["cliente_id"])


@router.put("/notificaciones/{notificacion_id}/leer")
def marcar_notificacion_leida(
    notificacion_id: str,
    db: Session = Depends(get_db),
    cli: dict = Depends(get_current_cliente),
):
    from app.models.mdl_all import Notificacion
    n = db.query(Notificacion).filter(
        Notificacion.id == notificacion_id,
        Notificacion.cliente_id == cli["cliente_id"],
    ).first()
    if n:
        n.leida = 1
        db.commit()
    return {"status": "ok"}


@router.post("/solicitudes", response_model=SolicitudOut)
def crear_solicitud_cliente(
    data: SolicitudClienteIn,
    db: Session = Depends(get_db),
    cli: dict = Depends(get_current_cliente),
):
    existing = db.query(Cliente).filter(Cliente.id == cli["cliente_id"]).first()
    if not existing:
        raise HTTPException(status_code=404, detail="Cliente no encontrado en BD")
    if data.nombre_negocio and not existing.nombre_negocio:
        existing.nombre_negocio = data.nombre_negocio
    if data.rubro_negocio and not existing.tipo_negocio:
        existing.tipo_negocio = data.rubro_negocio
    if data.antiguedad_negocio_meses is not None and not existing.antiguedad_negocio_meses:
        existing.antiguedad_negocio_meses = data.antiguedad_negocio_meses
    db.flush()
    create_data = SolicitudCreate(
        cliente_id=cli["cliente_id"],
        numero_documento=existing.numero_documento or "",
        nombres=existing.nombres or "",
        apellidos=existing.apellidos or "",
        telefono=existing.telefono or "",
        tipo_negocio=existing.tipo_negocio or data.rubro_negocio or "",
        nombre_negocio=existing.nombre_negocio or data.nombre_negocio or "",
        monto_solicitado=data.monto_solicitado,
        plazo_meses=data.plazo,
        destino_credito=data.destino or "",
        ingresos_estimados=data.ingresos_declarados or 0,
        tea_referencial=data.tea or 0.25,
        garantia=data.garantia or "sin_garantia",
        canal="cliente",
    )
    return svc_solicitudes.crear_solicitud(
        db, create_data, asesor_id=None, cliente_id=cli["cliente_id"]
    )


@router.get("/solicitudes", response_model=list[SolicitudOut])
def listar_solicitudes_cliente(
    db: Session = Depends(get_db),
    cli: dict = Depends(get_current_cliente),
):
    return svc_solicitudes.listar_solicitudes_cliente(db, cli["cliente_id"])


@router.post("/operaciones", response_model=OperacionOut)
def crear_operacion(
    data: OperacionIn,
    db: Session = Depends(get_db),
    cli: dict = Depends(get_current_cliente),
):
    result = rep_cliente.crear_operacion(db, cli["cliente_id"], data.model_dump())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ═══════════════════════════════════════════════════
#  NUEVOS ENDPOINTS
# ═══════════════════════════════════════════════════

@router.get("/buscar-destinatario", response_model=list[DestinatarioOut])
def buscar_destinatario(
    q: str = Query(..., min_length=1),
    db: Session = Depends(get_db),
    cli: dict = Depends(get_current_cliente),
):
    """Busca clientes por DNI, nombre, cuenta, CCI o teléfono para transferencias."""
    return rep_cliente.buscar_destinatario(db, q)


@router.post("/transferir")
def transferir(
    data: TransferirIn,
    db: Session = Depends(get_db),
    cli: dict = Depends(get_current_cliente),
):
    result = rep_cliente.transferir(db, cli["cliente_id"], data.model_dump())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/yape")
def yape(
    data: YapeIn,
    db: Session = Depends(get_db),
    cli: dict = Depends(get_current_cliente),
):
    """Transferencia tipo Yape por número de celular."""
    result = rep_cliente.transferir_yape(db, cli["cliente_id"], data.model_dump())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/pagar-cuota")
def pagar_cuota(
    data: PagoCuotaIn,
    db: Session = Depends(get_db),
    cli: dict = Depends(get_current_cliente),
):
    result = rep_cliente.pagar_cuota(db, cli["cliente_id"], data.model_dump())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/recargar")
def recargar(
    data: RecargaIn,
    db: Session = Depends(get_db),
    cli: dict = Depends(get_current_cliente),
):
    result = rep_cliente.recargar_celular(db, cli["cliente_id"], data.model_dump())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.post("/pagar-servicio")
def pagar_servicio(
    data: ServicioPagoIn,
    db: Session = Depends(get_db),
    cli: dict = Depends(get_current_cliente),
):
    result = rep_cliente.pagar_servicio(db, cli["cliente_id"], data.model_dump())
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/comprobantes", response_model=list[ComprobanteOut])
def listar_comprobantes(
    limit: int = 20,
    db: Session = Depends(get_db),
    cli: dict = Depends(get_current_cliente),
):
    ops = rep_cliente.listar_operaciones_recientes(db, cli["cliente_id"], limit)
    result = []
    for op in ops:
        comp = rep_cliente.obtener_comprobante(db, cli["cliente_id"], op["id"])
        if comp:
            result.append(comp)
    return result


@router.get("/comprobantes/{operacion_id}", response_model=ComprobanteOut)
def obtener_comprobante(
    operacion_id: str,
    db: Session = Depends(get_db),
    cli: dict = Depends(get_current_cliente),
):
    comp = rep_cliente.obtener_comprobante(db, cli["cliente_id"], operacion_id)
    if not comp:
        raise HTTPException(status_code=404, detail="Comprobante no encontrado")
    return comp
