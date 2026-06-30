from fastapi import APIRouter, Depends
from app.database.session import get_db
from app.core.cfg_auth import get_current_asesor

router = APIRouter()


@router.post("/promover")
def promover(db=Depends(get_db), asesor: dict = Depends(get_current_asesor)):
    return {"status": "ok", "message": "Sync deshabilitado — usar /sync-db/"}


@router.get("/outbox")
def outbox(db=Depends(get_db), asesor: dict = Depends(get_current_asesor)):
    return []
