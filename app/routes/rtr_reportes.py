from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.cfg_auth import get_current_asesor, requiere_rol, ROLES
from app.models import Asesor, SolicitudCredito, Credito, CarteraDiaria

router = APIRouter()

class ProductividadAsesor(BaseModel):
    asesor_nombre: str
    enviadas: int
    aprobadas: int
    desembolsadas: int
    monto_total: float
    tasa_aprobacion: float

class ResumenReportes(BaseModel):
    total_solicitudes: int
    total_aprobadas: int
    total_desembolsadas: int
    monto_colocado: float
    clientes_atendidos: int
    visitas_realizadas: int
    en_cartera: int
    promedio_score: float
    asesores_activos: int

def _calcular_productividad(db: Session, asesor_id: str | None = None) -> list[dict]:
    """Calcula productividad. Si asesor_id es None, devuelve todos."""
    query = db.query(Asesor)
    if asesor_id:
        query = query.filter(Asesor.id == asesor_id)
    asesores = query.all()
    result = []
    for a in asesores:
        solicitudes = db.query(SolicitudCredito).filter(
            SolicitudCredito.asesor_id == a.id
        ).all()
        enviadas = aprobadas = desembolsadas = 0
        monto_total = 0.0
        for s in solicitudes:
            enviadas += 1
            if s.estado in ("aprobado", "desembolsado"):
                aprobadas += 1
            if s.estado == "desembolsado":
                desembolsadas += 1
            monto_total += float(s.monto or 0)
        creditos = db.query(Credito).filter(
            Credito.asesor_id == a.id,
            Credito.solicitud_id == None
        ).all()
        for c in creditos:
            enviadas += 1
            if c.estado in ("APROBADO", "DESEMBOLSADO"):
                aprobadas += 1
            if c.estado == "DESEMBOLSADO":
                desembolsadas += 1
            monto_total += float(c.monto or 0)
        if enviadas > 0:
            result.append({
                "asesor_nombre": f"{a.nombres} {a.apellidos}",
                "enviadas": enviadas,
                "aprobadas": aprobadas,
                "desembolsadas": desembolsadas,
                "monto_total": monto_total,
                "tasa_aprobacion": round((aprobadas / enviadas * 100) if enviadas else 0, 1),
            })
    return result


@router.get("/productividad", response_model=list[ProductividadAsesor])
def productividad(
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    perfil = asesor.get("perfil", "")
    rol = ROLES.get(perfil, "ASESOR")
    if rol == "ADMIN":
        result = _calcular_productividad(db)
    else:
        result = _calcular_productividad(db, asesor_id=asesor.get("asesor_id"))
    result.sort(key=lambda x: x["enviadas"], reverse=True)
    return result


@router.get("/resumen", response_model=ResumenReportes)
def resumen_reportes(
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    perfil = asesor.get("perfil", "")
    rol = ROLES.get(perfil, "ASESOR")
    asesor_id = asesor.get("asesor_id")

    solicitudes_q = db.query(SolicitudCredito)
    creditos_q = db.query(Credito)
    cartera_q = db.query(CarteraDiaria)

    if rol != "ADMIN":
        solicitudes_q = solicitudes_q.filter(SolicitudCredito.asesor_id == asesor_id)
        creditos_q = creditos_q.filter(Credito.asesor_id == asesor_id)
        cartera_q = cartera_q.filter(CarteraDiaria.asesor_id == asesor_id)

    solicitudes = solicitudes_q.all()
    creditos = creditos_q.all()

    total_solicitudes = len(solicitudes) + len(creditos)
    total_aprobadas = sum(1 for s in solicitudes if s.estado in ("aprobado", "desembolsado"))
    total_desembolsadas = sum(1 for s in solicitudes if s.estado == "desembolsado")
    monto_colocado = sum(float(s.monto or 0) for s in solicitudes if s.estado in ("aprobado", "desembolsado"))
    clientes_ids = set()
    for s in solicitudes:
        if s.cliente_id: clientes_ids.add(s.cliente_id)
    for c in creditos:
        if c.cliente_id: clientes_ids.add(c.cliente_id)
    cartera_items = cartera_q.filter(CarteraDiaria.estado_visita == "pendiente").count()

    scores = [s.score_usado for s in solicitudes if s.score_usado]
    promedio_score = round(sum(scores) / len(scores), 1) if scores else 0
    asesores_contados = 1 if rol != "ADMIN" else db.query(Asesor).count()

    return ResumenReportes(
        total_solicitudes=total_solicitudes,
        total_aprobadas=total_aprobadas,
        total_desembolsadas=total_desembolsadas,
        monto_colocado=monto_colocado,
        clientes_atendidos=len(clientes_ids),
        visitas_realizadas=0,
        en_cartera=cartera_items,
        promedio_score=promedio_score,
        asesores_activos=asesores_contados,
    )
