from fastapi import APIRouter, Depends, HTTPException
from app.database.session import get_db
from app.core.cfg_auth import get_current_asesor
from app.schemas.sch_ficha import FichaOut, UbicacionIn
from app.repositories import rep_ficha

router = APIRouter()


@router.get("")
def listar_clientes(db=Depends(get_db), asesor: dict = Depends(get_current_asesor)):
    """Lista todos los clientes desde PostgreSQL."""
    return rep_ficha.listar_todos(db)


@router.get("/{cliente_id}")
def obtener_cliente_por_id(
    cliente_id: str,
    db=Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    """Obtiene un cliente por su ID."""
    cliente = rep_ficha.obtener_por_id(db, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return cliente


@router.post("")
def crear_cliente(
    data: dict,
    db=Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    """Crea un nuevo cliente en PostgreSQL."""
    from app.models.mdl_all import Cliente
    import uuid
    cliente = Cliente(
        id=str(uuid.uuid4()),
        numero_documento=data.get("numero_documento", ""),
        nombres=data.get("nombres", ""),
        apellidos=data.get("apellidos", ""),
        telefono=data.get("telefono"),
        direccion=data.get("direccion"),
        tipo_negocio=data.get("tipo_negocio"),
        nombre_negocio=data.get("nombre_negocio"),
    )
    db.add(cliente)
    db.commit()
    return {"id": cliente.id, **data}


@router.get("/{cliente_id}/ficha", response_model=FichaOut)
def ficha_cliente(
    cliente_id: str,
    db=Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    """Ficha completa del cliente desde PostgreSQL."""
    ficha = rep_ficha.obtener_ficha(db, cliente_id)
    if ficha is None:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return ficha


@router.post("/{cliente_id}/ubicacion")
def actualizar_ubicacion(
    cliente_id: str,
    body: UbicacionIn,
    db=Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    """Actualiza las coordenadas del negocio del cliente en PostgreSQL."""
    ok = rep_ficha.actualizar_ubicacion(db, cliente_id, body.lat, body.lng, body.direccion)
    if not ok:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    return {"ok": True, "lat": body.lat, "lng": body.lng}
