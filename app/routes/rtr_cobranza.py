from fastapi import APIRouter, Depends
from app.database.session import get_db
from app.core.cfg_auth import get_current_asesor, requiere_rol
from app.schemas.sch_cobranza import MoraItemOut, AccionCobranzaIn
from app.repositories import rep_cobranza

router = APIRouter()


@router.get("/mora", response_model=list[MoraItemOut])
def listar_mora(
    db=Depends(get_db),
    asesor: dict = Depends(requiere_rol("ADMIN")),
):
    return rep_cobranza.listar_mora(db)


@router.post("/accion")
def registrar_accion(
    data: AccionCobranzaIn,
    db=Depends(get_db),
    asesor: dict = Depends(requiere_rol("ADMIN")),
):
    rep_cobranza.registrar_accion(db, asesor["asesor_id"], data.model_dump())
    return {"status": "ok"}
