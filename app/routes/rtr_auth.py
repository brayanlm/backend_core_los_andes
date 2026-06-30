import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.sch_auth import LoginIn, TokenOut
from app.controllers import ctl_auth
from app.core.firebase_auth import login_asesor_por_email
from app.models import Asesor

logger = logging.getLogger("core_mobile")
router = APIRouter()
MAX_INTENTOS_ASESOR = 5

@router.post("/login", response_model=TokenOut)
def login(data: LoginIn, db: Session = Depends(get_db)):
    asesor_db = None
    if data.codigo_empleado:
        asesor_db = db.query(Asesor).filter(Asesor.codigo_empleado == data.codigo_empleado).first()
    elif data.email:
        asesor_db = db.query(Asesor).filter(Asesor.email == data.email).first()

    if asesor_db and asesor_db.bloqueado_hasta:
        logger.warning("LOGIN_BLOQUEADO codigo=%s email=%s", data.codigo_empleado, data.email)
        raise HTTPException(status_code=423, detail="Cuenta bloqueada por intentos fallidos")

    result = None
    if data.email:
        result = login_asesor_por_email(db, data.email, data.password)
    elif data.codigo_empleado:
        result = ctl_auth.login(db, data.codigo_empleado, data.password)

    if not result and asesor_db:
        asesor_db.intentos_fallidos = (asesor_db.intentos_fallidos or 0) + 1
        if asesor_db.intentos_fallidos >= MAX_INTENTOS_ASESOR:
            asesor_db.bloqueado_hasta = datetime.now(timezone.utc).isoformat()
            logger.warning("ASESOR_BLOQUEADO id=%s codigo=%s", asesor_db.id, data.codigo_empleado)
        db.commit()
        raise HTTPException(status_code=401, detail="Credenciales invalidas")
    elif result and asesor_db:
        asesor_db.intentos_fallidos = 0
        asesor_db.bloqueado_hasta = None
        db.commit()
        logger.info("LOGIN_OK asesor_id=%s codigo=%s", result.get("asesor", {}).get("id"), data.codigo_empleado)

    if result and result.get("_bloqueado"):
        raise HTTPException(status_code=423, detail="Cuenta bloqueada por intentos fallidos")
    if not result:
        raise HTTPException(status_code=401, detail="Credenciales invalidas")
    return result
