from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.core.cfg_auth import get_current_asesor, requiere_rol
from app.schemas.sch_creditos import (
    CreditoOut, CronogramaCuotaOut, DesembolsarIn, DesembolsarOut,
)
from app.services import svc_creditos

router = APIRouter()


@router.get("", response_model=list[CreditoOut])
def listar_creditos(
    estado: str = None,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    if asesor.get("rol") == "ADMIN":
        return svc_creditos.listar_creditos(db, estado=estado)
    return svc_creditos.listar_creditos(db, asesor_id=asesor["asesor_id"], estado=estado)


@router.get("/stats", response_model=dict)
def creditos_stats(
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    return svc_creditos.obtener_stats(db)


@router.get("/{credito_id}", response_model=CreditoOut)
def obtener_credito(
    credito_id: str,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    cred = svc_creditos.obtener_credito(db, credito_id)
    if not cred:
        raise HTTPException(status_code=404, detail="Crédito no encontrado")
    return cred


@router.get("/{credito_id}/cronograma", response_model=list[CronogramaCuotaOut])
def obtener_cronograma(
    credito_id: str,
    db: Session = Depends(get_db),
    asesor: dict = Depends(get_current_asesor),
):
    cuotas = svc_creditos.obtener_cronograma(db, credito_id)
    if not cuotas:
        raise HTTPException(status_code=404, detail="Cronograma no encontrado")
    return cuotas


@router.post("/{credito_id}/desembolsar", response_model=DesembolsarOut, status_code=201)
def desembolsar_credito(
    credito_id: str,
    data: DesembolsarIn = None,
    db: Session = Depends(get_db),
    asesor: dict = Depends(requiere_rol("ADMIN")),
):
    try:
        return svc_creditos.desembolsar(
            db, credito_id, data.cuenta_destino if data else ""
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
