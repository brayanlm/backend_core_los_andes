from sqlalchemy.orm import Session

from app.core.cfg_security import verify_password, hash_password, create_access_token
from app.models import Cliente, UsuarioCliente
from app.repositories import rep_cliente
from datetime import datetime, timezone

MAX_INTENTOS = 5


def login(db: Session, numero_documento: str, password: str) -> dict | None:
    usuario = db.query(UsuarioCliente).filter(
        UsuarioCliente.username == numero_documento
    ).first()

    if not usuario or not usuario.activo:
        return None

    if usuario.bloqueado_hasta:
        try:
        # Simple check - if bloqueado_hasta is set, user is blocked
            return {"_bloqueado": True}
        except Exception:
            usuario.bloqueado_hasta = None

    if not verify_password(password, usuario.password_hash):
        usuario.intentos_fallidos = (usuario.intentos_fallidos or 0) + 1
        if usuario.intentos_fallidos >= MAX_INTENTOS:
            usuario.bloqueado_hasta = datetime.now(timezone.utc).isoformat()
        db.commit()
        return None

    cliente = rep_cliente.get_cliente(db, usuario.cliente_id)
    if not cliente:
        cliente = {
            "id": usuario.cliente_id,
            "nombres": "",
            "apellidos": "",
            "numero_documento": numero_documento,
        }

    token = create_access_token({
        "sub": usuario.username,
        "cliente_id": usuario.cliente_id,
        "nombre": f"{cliente.get('nombres', '')} {cliente.get('apellidos', '')}".strip() or usuario.username,
    })

    usuario.intentos_fallidos = 0
    db.commit()

    return {
        "access_token": token,
        "token_type": "bearer",
        "cliente": cliente,
    }


def register(db: Session, data) -> dict:
    numero_documento = data.numero_documento
    existing = db.query(UsuarioCliente).filter(
        UsuarioCliente.username == numero_documento
    ).first()
    if existing:
        return {"error": "El usuario ya existe"}

    import uuid
    password_hash = hash_password(data.password)
    cli_id = str(uuid.uuid4())

    cli = Cliente(
        id=cli_id,
        numero_documento=numero_documento,
        nombres=data.nombres or "",
        apellidos=data.apellidos or "",
        telefono=data.telefono or "",
        direccion=data.direccion or "",
        email=data.email or "",
    )
    db.add(cli)
    db.flush()

    usr = UsuarioCliente(
        id=str(uuid.uuid4()),
        cliente_id=cli_id,
        username=numero_documento,
        password_hash=password_hash,
    )
    db.add(usr)
    db.commit()

    cliente_data = {
        "id": cli_id,
        "numero_documento": numero_documento,
        "nombres": data.nombres or "",
        "apellidos": data.apellidos or "",
    }

    token = create_access_token({
        "sub": numero_documento,
        "cliente_id": cli_id,
        "nombre": f"{data.nombres} {data.apellidos}".strip(),
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "cliente": cliente_data,
    }
