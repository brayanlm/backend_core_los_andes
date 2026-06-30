from app.core.firebase_auth import login_asesor


def login(db, codigo_empleado: str, password: str) -> dict | None:
    return login_asesor(codigo_empleado, password)
