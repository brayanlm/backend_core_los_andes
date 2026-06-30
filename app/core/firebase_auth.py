"""
Auth service — PostgreSQL only. Firestore removed.

Authentication is done against the local Asesor table using bcrypt password hashes.
"""
from app.core.cfg_security import create_access_token, verify_password


PERFIL_A_ROL = {
    "operador": "ASESOR",
    "super_operador": "ASESOR",
    "supervisor": "ADMIN",
    "administrador": "ADMIN",
}


def _build_response_local(a, email: str) -> dict:
    asesor = {
        "id": a.id,
        "codigo_empleado": a.codigo_empleado,
        "email": email,
        "nombres": a.nombres,
        "apellidos": a.apellidos,
        "full_name": f'{a.nombres} {a.apellidos}'.strip(),
        "perfil": a.perfil or "operador",
        "rol": a.rol or "ASESOR",
        "agencia_id": a.agencia_id,
    }
    token = create_access_token({
        "sub": a.id,
        "asesor_id": a.id,
        "codigo_empleado": a.codigo_empleado,
        "perfil": asesor["perfil"],
        "nombre": asesor["full_name"],
        "rol": asesor["rol"],
    })
    return {"access_token": token, "token_type": "bearer", "asesor": asesor}


def login_asesor(codigo_empleado: str, password: str) -> dict | None:
    """Login por codigo de empleado — ahora solo usa PostgreSQL."""
    from app.models.mdl_all import Asesor
    from app.database.session import SessionLocal
    db = SessionLocal()
    try:
        a = db.query(Asesor).filter(Asesor.codigo_empleado == codigo_empleado).first()
        if a and a.password_hash and verify_password(password, a.password_hash):
            return _build_response_local(a, a.email or f"{codigo_empleado}@bancodelosandes.com")
    finally:
        db.close()
    return None


def login_asesor_por_email(db_session, email: str, password: str) -> dict | None:
    """Login por email — usa PostgreSQL directamente."""
    from app.models.mdl_all import Asesor
    a = db_session.query(Asesor).filter(Asesor.email == email).first()
    if a and a.password_hash and verify_password(password, a.password_hash):
        return _build_response_local(a, email)
    return None
