from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.core.cfg_auth import get_current_asesor, requiere_rol
from app.models import Asesor, SolicitudCredito

router = APIRouter()

class ProductividadAsesor(BaseModel):
    asesor_nombre: str
    enviadas: int
    aprobadas: int
    desembolsadas: int
    monto_total: float
    tasa_aprobacion: float

@router.get("/productividad", response_model=list[ProductividadAsesor])
def productividad(db: Session = Depends(get_db), asesor: dict = Depends(requiere_rol("ADMIN"))):
    mes_actual = datetime.now(timezone.utc).strftime("%Y-%m")
    asesores = db.query(Asesor).all()
    result = []
    for a in asesores:
        solicitudes = db.query(SolicitudCredito).filter(
            SolicitudCredito.asesor_id == a.id
        ).all()
        enviadas = aprobadas = desembolsadas = 0
        monto_total = 0.0
        for s in solicitudes:
            if not s.created_at or not s.created_at.startswith(mes_actual):
                continue
            enviadas += 1
            if s.estado in ("aprobado", "desembolsado"):
                aprobadas += 1
            if s.estado == "desembolsado":
                desembolsadas += 1
            monto_total += float(s.monto or 0)
        if enviadas > 0:
            result.append(ProductividadAsesor(
                asesor_nombre=f"{a.nombres} {a.apellidos}",
                enviadas=enviadas,
                aprobadas=aprobadas,
                desembolsadas=desembolsadas,
                monto_total=monto_total,
                tasa_aprobacion=round((aprobadas / enviadas * 100) if enviadas else 0, 1),
            ))
    result.sort(key=lambda x: x.enviadas, reverse=True)
    return result
