import logging
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.cfg_security import decode_token

logger = logging.getLogger("core_mobile")
bearer = HTTPBearer(auto_error=True)

ROLES = {
    "operador": "ASESOR",
    "super_operador": "ASESOR",
    "supervisor": "ADMIN",
    "administrador": "ADMIN",
}

def get_current_asesor(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    payload = decode_token(cred.credentials)
    if not payload or "asesor_id" not in payload:
        raise HTTPException(status_code=401, detail="Token invalido o expirado")
    logger.info("AUTH asesor_id=%s rol=%s path=?", payload.get("asesor_id"), payload.get("rol"))
    return payload


def get_current_cliente(
    cred: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    payload = decode_token(cred.credentials)
    if not payload or "cliente_id" not in payload:
        raise HTTPException(status_code=401, detail="Token invalido o expirado")
    return payload


def requiere_rol(*roles: str):
    """Dependency factory: verifica que el perfil tenga un rol permitido."""
    roles_esperados = set(roles)

    def _verificador(asesor: dict = Depends(get_current_asesor)) -> dict:
        perfil = asesor.get("perfil", "")
        rol = ROLES.get(perfil, "")
        if rol not in roles_esperados:
            raise HTTPException(
                status_code=403,
                detail=f"Se requiere rol {roles_esperados}, tienes {rol} (perfil: {perfil})",
            )
        return asesor

    return _verificador
