from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.cfg_auth import get_current_asesor
from app.models.mdl_all import BuroConsulta, Cliente, SolicitudCredito
from app.schemas.sch_creditos import BuroConsultaOut
import uuid
from datetime import datetime, timezone

router = APIRouter()


class BuroIn(BaseModel):
    dni: str
    solicitud_id: Optional[str] = None
    cliente_id: Optional[str] = None


# Perfiles determinísticos por último dígito del DNI (simulado académico)
_PERFILES = {
    0: ("NORMAL", 1, 4500, 4500, 0, False, "Sin observaciones. Cliente con buen historial."),
    1: ("NORMAL", 2, 12000, 8000, 0, False, "Historial positivo en 2 entidades."),
    2: ("CPP", 2, 18000, 12000, 15, False, "Mora leve de 15 días. Requiere seguimiento."),
    3: ("NORMAL", 0, 0, 0, 0, False, "Sin historial crediticio. Cliente nuevo en el sistema."),
    4: ("DUDOSO", 3, 25000, 15000, 95, False, "Mora prolongada de 95 días. Riesgo alto."),
    5: ("DEFICIENTE", 2, 16000, 10000, 45, False, "Mora de 45 días. Capacidad de pago reducida."),
    6: ("NORMAL", 1, 6000, 6000, 0, False, "Cliente con crédito vigente sin mora."),
    7: ("PERDIDA", 4, 40000, 22000, 210, True, "Cliente en lista de inhabilitados. No procede."),
    8: ("CPP", 1, 9000, 9000, 20, False, "Mora leve de 20 días. Regularizó parcialmente."),
    9: ("NORMAL", 2, 14000, 9000, 0, False, "Historial positivo. 2 créditos vigentes sin mora."),
}


@router.post("/consulta", response_model=BuroConsultaOut)
def consulta_buro(
    data: BuroIn,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    """Consulta de buró determinística basada en DNI (simulación académica).
    El resultado persiste en PostgreSQL asociado a la solicitud.
    """
    ultimo = int(data.dni[-1]) if data.dni and data.dni[-1].isdigit() else 0
    perfil = _PERFILES[ultimo]

    calif, entidades, deuda, mayor, mora, lista_negra, recom = perfil

    # Resolver cliente_id
    cliente_id = data.cliente_id
    if not cliente_id and data.solicitud_id:
        sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == data.solicitud_id).first()
        if sol:
            cliente_id = sol.cliente_id
    if not cliente_id:
        cli = db.query(Cliente).filter(Cliente.numero_documento == data.dni).first()
        if cli:
            cliente_id = cli.id

    if not cliente_id:
        raise HTTPException(status_code=404, detail="Cliente no encontrado. Proporcione cliente_id o solicitud_id.")

    # Determinar motivo_bloqueo
    motivo = None
    if lista_negra:
        motivo = "Registrado en lista de restricción del sistema financiero."

    # Persistir resultado
    now = datetime.now(timezone.utc).isoformat()
    consulta = BuroConsulta(
        id=str(uuid.uuid4()),
        solicitud_id=data.solicitud_id,
        asesor_id=asesor.get("asesor_id"),
        cliente_id=cliente_id,
        dni=data.dni,
        calificacion=calif,
        entidades_con_deuda=entidades,
        deuda_total=float(deuda),
        mayor_deuda=float(mayor),
        dias_mayor_mora=mora,
        en_lista_negra=1 if lista_negra else 0,
        recomendacion=recom,
        motivo_bloqueo=motivo,
        created_at=now,
    )
    db.add(consulta)

    # Marcar solicitud como buro_consultado
    if data.solicitud_id:
        sol = db.query(SolicitudCredito).filter(SolicitudCredito.id == data.solicitud_id).first()
        if sol:
            sol.buro_consultado = 1

    db.commit()
    db.refresh(consulta)

    return BuroConsultaOut(
        id=consulta.id,
        solicitud_id=consulta.solicitud_id,
        asesor_id=consulta.asesor_id,
        cliente_id=consulta.cliente_id,
        dni=consulta.dni,
        calificacion=consulta.calificacion,
        entidades_con_deuda=consulta.entidades_con_deuda,
        deuda_total=consulta.deuda_total,
        mayor_deuda=consulta.mayor_deuda,
        dias_mayor_mora=consulta.dias_mayor_mora,
        en_lista_negra=bool(consulta.en_lista_negra),
        recomendacion=consulta.recomendacion,
        motivo_bloqueo=consulta.motivo_bloqueo,
        created_at=consulta.created_at,
    )
