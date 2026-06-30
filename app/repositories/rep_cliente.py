import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models import (
    Cliente, UsuarioCliente, Credito, CronogramaPago, Movimiento,
    CuentaAhorro, Tarjeta, Notificacion, Operacion,
)


def _row_to_dict(row):
    if not row:
        return None
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


def _ahora():
    return datetime.now(timezone.utc).isoformat()


def _nuevo_id():
    return str(uuid.uuid4())


def get_cliente(db: Session, cliente_id: str) -> dict | None:
    row = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not row:
        return None
    return {
        "id": row.id,
        "numero_documento": row.numero_documento,
        "nombres": row.nombres,
        "apellidos": row.apellidos,
        "telefono": row.telefono or "",
        "direccion": row.direccion or "",
        "email": row.email or "",
        "tipo_negocio": row.tipo_negocio or "",
        "nombre_negocio": row.nombre_negocio or "",
        "calificacion_sbs": row.calificacion_sbs or "NORMAL",
    }


def get_cliente_by_doc(db: Session, numero_documento: str) -> dict | None:
    row = db.query(Cliente).filter(Cliente.numero_documento == numero_documento).first()
    return get_cliente(db, row.id) if row else None


def cuentas_ahorro(db: Session, cliente_id: str) -> list[dict]:
    rows = db.query(CuentaAhorro).filter(
        CuentaAhorro.cliente_id == cliente_id
    ).order_by(CuentaAhorro.cod_cuenta_ahorro).all()
    return [_row_to_dict(r) for r in rows]


def creditos(db: Session, cliente_id: str) -> list[dict]:
    rows = db.query(Credito).filter(
        Credito.cliente_id == cliente_id
    ).order_by(Credito.fecha_creacion.desc()).all()
    return [_row_to_dict(r) for r in rows]


def cronograma(db: Session, credito_id: str) -> list[dict]:
    rows = db.query(CronogramaPago).filter(
        CronogramaPago.credito_id == credito_id
    ).order_by(CronogramaPago.nro_cuota).all()
    return [_row_to_dict(r) for r in rows]


def movimientos(db: Session, cliente_id: str, limit: int = 20) -> list[dict]:
    rows = db.query(Movimiento).filter(
        Movimiento.cliente_id == cliente_id
    ).order_by(Movimiento.fecha_operacion.desc()).limit(limit).all()
    return [_row_to_dict(r) for r in rows]


def tarjetas(db: Session, cliente_id: str) -> list[dict]:
    rows = db.query(Tarjeta).filter(
        Tarjeta.cliente_id == cliente_id
    ).order_by(Tarjeta.created_at).all()
    return [_row_to_dict(r) for r in rows]


def notificaciones(db: Session, cliente_id: str, limit: int = 30) -> list[dict]:
    rows = db.query(Notificacion).filter(
        Notificacion.cliente_id == cliente_id
    ).order_by(Notificacion.created_at.desc()).limit(limit).all()
    return [_row_to_dict(r) for r in rows]


def crear_operacion(db: Session, cliente_id: str, data: dict) -> dict:
    op_id = _nuevo_id()
    ahora = _ahora()
    tipo = (data.get("tipo") or "").upper()
    monto = float(data.get("monto", 0))

    if tipo == "TRANSFERENCIA":
        cod_origen = data.get("cod_cuenta_origen")
        cuenta = db.query(CuentaAhorro).filter(
            CuentaAhorro.cod_cuenta_ahorro == cod_origen,
            CuentaAhorro.cliente_id == cliente_id,
        ).first()
        if not cuenta:
            return {"error": "Cuenta origen no encontrada"}
        if (cuenta.saldo_capital or 0) < monto:
            return {"error": "Saldo insuficiente"}
        cuenta.saldo_capital = (cuenta.saldo_capital or 0) - monto

    op = Operacion(
        id=op_id,
        cliente_id=cliente_id,
        cod_cuenta_origen=data.get("cod_cuenta_origen"),
        cod_cuenta_destino=data.get("cod_cuenta_destino"),
        tipo=tipo,
        monto=monto,
        moneda=data.get("moneda", "PEN"),
        estado="completada",
        created_at=ahora,
    )
    db.add(op)
    db.commit()
    return {"id": op_id, "estado": "completada"}


def crear_cliente_y_usuario(data: dict, password_hash: str) -> dict:
    from app.database.session import SessionLocal
    db = SessionLocal()
    try:
        cli_id = _nuevo_id()
        cli = Cliente(
            id=cli_id,
            numero_documento=data.get("numero_documento", ""),
            nombres=data.get("nombres", ""),
            apellidos=data.get("apellidos", ""),
            telefono=data.get("telefono", ""),
            direccion=data.get("direccion", ""),
            email=data.get("email", ""),
        )
        db.add(cli)
        db.flush()

        usr = UsuarioCliente(
            id=_nuevo_id(),
            cliente_id=cli_id,
            username=data.get("numero_documento", ""),
            password_hash=password_hash,
        )
        db.add(usr)
        db.commit()
        return {"id": cli_id, **data}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


# ═══════════════════════════════════════════════════
#  NUEVAS FUNCIONALIDADES
# ═══════════════════════════════════════════════════

def buscar_destinatario(db: Session, query: str) -> list[dict]:
    """Busca clientes por DNI, nombre, cuenta, CCI o teléfono."""
    results = []
    q = query.strip()

    cli_rows = db.query(Cliente).filter(
        (Cliente.numero_documento == q) |
        (Cliente.telefono == q) |
        (Cliente.nombres.ilike(f"%{q}%")) |
        (Cliente.apellidos.ilike(f"%{q}%"))
    ).limit(10).all()

    for cli in cli_rows:
        cta = db.query(CuentaAhorro).filter(
            CuentaAhorro.cliente_id == cli.id
        ).first()
        results.append({
            "cliente_id": cli.id,
            "nombres": cli.nombres,
            "apellidos": cli.apellidos,
            "numero_documento": cli.numero_documento,
            "telefono": cli.telefono or "",
            "cod_cuenta": cta.cod_cuenta_ahorro if cta else None,
            "cci": cta.cci if cta else None,
        })

    if not results:
        cta_rows = db.query(CuentaAhorro).filter(
            (CuentaAhorro.cod_cuenta_ahorro == q) |
            (CuentaAhorro.cci == q)
        ).limit(5).all()
        for cta in cta_rows:
            cli = db.query(Cliente).filter(Cliente.id == cta.cliente_id).first()
            if cli:
                results.append({
                    "cliente_id": cli.id,
                    "nombres": cli.nombres,
                    "apellidos": cli.apellidos,
                    "numero_documento": cli.numero_documento,
                    "telefono": cli.telefono or "",
                    "cod_cuenta": cta.cod_cuenta_ahorro,
                    "cci": cta.cci,
                })

    return results


def transferir(db: Session, cliente_id: str, data: dict) -> dict:
    """Transferencia simulada — descuenta de origen, acredita a destino si existe."""
    ahora = _ahora()
    monto = float(data["monto"])
    op_id = _nuevo_id()
    descripcion = data.get("descripcion", "Transferencia")

    cuenta_origen = db.query(CuentaAhorro).filter(
        CuentaAhorro.id == data["cuenta_origen_id"],
        CuentaAhorro.cliente_id == cliente_id,
    ).first()
    if not cuenta_origen:
        return {"error": "Cuenta origen no encontrada"}
    if (cuenta_origen.saldo_capital or 0) < monto:
        return {"error": "Saldo insuficiente"}

    emisor = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    nombre_emisor = f"{emisor.nombres} {emisor.apellidos}" if emisor else "Desconocido"

    destino_cod = data.get("cuenta_destino_cod", "")
    # No permitir transferir a la misma cuenta
    if emisor:
        cta_origen = db.query(CuentaAhorro).filter(
            CuentaAhorro.id == data["cuenta_origen_id"],
            CuentaAhorro.cliente_id == cliente_id,
        ).first()
        if cta_origen and cta_origen.cod_cuenta_ahorro == destino_cod:
            return {"error": "No puedes transferir a tu misma cuenta"}

    # Buscar destino — si no existe, igual descontamos (simulación)
    cuenta_destino = db.query(CuentaAhorro).filter(
        CuentaAhorro.cod_cuenta_ahorro == destino_cod
    ).first()

    destinatario = None
    if cuenta_destino:
        destinatario = db.query(Cliente).filter(Cliente.id == cuenta_destino.cliente_id).first()

    nombre_destino = data.get("destinatario_nombre",
                              f"{destinatario.nombres} {destinatario.apellidos}" if destinatario
                              else (data.get("cuenta_destino_cod", "Externo")))

    cuenta_origen.saldo_capital = (cuenta_origen.saldo_capital or 0) - monto

    if cuenta_destino:
        cuenta_destino.saldo_capital = (cuenta_destino.saldo_capital or 0) + monto

    op = Operacion(
        id=op_id,
        cliente_id=cliente_id,
        cod_cuenta_origen=cuenta_origen.cod_cuenta_ahorro,
        cod_cuenta_destino=data.get("cuenta_destino_cod"),
        tipo="TRANSFERENCIA",
        monto=monto,
        moneda="PEN",
        estado="completada",
        created_at=ahora,
    )
    db.add(op)

    mov_emisor = Movimiento(
        id=_nuevo_id(),
        cliente_id=cliente_id,
        cod_cuenta=cuenta_origen.cod_cuenta_ahorro,
        cod_operacion=op_id,
        tipo="TRANSFERENCIA",
        concepto=f"{descripcion} · {nombre_destino}",
        canal="app",
        monto=-monto,
        moneda="PEN",
        fecha_operacion=ahora,
    )
    db.add(mov_emisor)

    if destinatario and cuenta_destino:
        mov_receptor = Movimiento(
            id=_nuevo_id(),
            cliente_id=destinatario.id,
            cod_cuenta=cuenta_destino.cod_cuenta_ahorro,
            cod_operacion=op_id,
            tipo="TRANSFERENCIA_ENTRANTE",
            concepto=f"Transferencia de {nombre_emisor}",
            canal="app",
            monto=monto,
            moneda="PEN",
            fecha_operacion=ahora,
        )
        db.add(mov_receptor)

        notif_receptor = Notificacion(
            id=_nuevo_id(),
            cliente_id=destinatario.id,
            tipo="exito",
            titulo="Transferencia recibida",
            mensaje=f"Recibiste S/ {monto:.2f} de {nombre_emisor}",
            created_at=ahora,
        )
        db.add(notif_receptor)

    notif_emisor = Notificacion(
        id=_nuevo_id(),
        cliente_id=cliente_id,
        tipo="exito",
        titulo="Transferencia exitosa",
        mensaje=f"Transferiste S/ {monto:.2f} a {nombre_destino}",
        created_at=ahora,
    )
    db.add(notif_emisor)

    db.commit()

    return {
        "id": op_id,
        "estado": "completada",
        "monto": monto,
        "cuenta_origen": cuenta_origen.cod_cuenta_ahorro,
        "cuenta_destino": data.get("cuenta_destino_cod"),
        "destinatario": nombre_destino,
        "created_at": ahora,
    }


def transferir_yape(db: Session, cliente_id: str, data: dict) -> dict:
    """Yape simulado — descuenta de origen aunque el destino no exista."""
    telefono = data["telefono_destino"].strip()
    monto = float(data["monto"])
    op_id = _nuevo_id()
    ahora = _ahora()
    descripcion = data.get("descripcion", "Yape")

    cuenta_origen = db.query(CuentaAhorro).filter(
        CuentaAhorro.id == data["cuenta_origen_id"],
        CuentaAhorro.cliente_id == cliente_id,
    ).first()
    if not cuenta_origen:
        return {"error": "Cuenta origen no encontrada"}
    if (cuenta_origen.saldo_capital or 0) < monto:
        return {"error": "Saldo insuficiente"}
    emisor = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if emisor and emisor.telefono == telefono:
        return {"error": "No puedes enviarte Yape a ti mismo"}
    nombre_emisor = f"{emisor.nombres} {emisor.apellidos}" if emisor else "Desconocido"

    # Buscar destino por teléfono — si no existe, igual descontamos (simulación)
    destinatario = db.query(Cliente).filter(Cliente.telefono == telefono).first()
    cuenta_destino = None
    if destinatario:
        cuenta_destino = db.query(CuentaAhorro).filter(
            CuentaAhorro.cliente_id == destinatario.id
        ).first()

    nombre_destino = f"{destinatario.nombres} {destinatario.apellidos}" if destinatario else telefono

    cuenta_origen.saldo_capital = (cuenta_origen.saldo_capital or 0) - monto
    if cuenta_destino:
        cuenta_destino.saldo_capital = (cuenta_destino.saldo_capital or 0) + monto

    op = Operacion(
        id=op_id,
        cliente_id=cliente_id,
        cod_cuenta_origen=cuenta_origen.cod_cuenta_ahorro,
        tipo="YAPE",
        monto=monto,
        moneda="PEN",
        estado="completada",
        created_at=ahora,
    )
    db.add(op)

    mov = Movimiento(
        id=_nuevo_id(),
        cliente_id=cliente_id,
        cod_cuenta=cuenta_origen.cod_cuenta_ahorro,
        cod_operacion=op_id,
        tipo="YAPE",
        concepto=f"{descripcion} · {nombre_destino}",
        canal="app",
        monto=-monto,
        moneda="PEN",
        fecha_operacion=ahora,
    )
    db.add(mov)

    if destinatario and cuenta_destino:
        mov_rec = Movimiento(
            id=_nuevo_id(),
            cliente_id=destinatario.id,
            cod_cuenta=cuenta_destino.cod_cuenta_ahorro,
            cod_operacion=op_id,
            tipo="YAPE_ENTRANTE",
            concepto=f"Yape de {nombre_emisor}",
            canal="app",
            monto=monto,
            moneda="PEN",
            fecha_operacion=ahora,
        )
        db.add(mov_rec)

        notif_rec = Notificacion(
            id=_nuevo_id(),
            cliente_id=destinatario.id,
            tipo="exito",
            titulo="Yape recibido",
            mensaje=f"Recibiste S/ {monto:.2f} de {nombre_emisor}",
            created_at=ahora,
        )
        db.add(notif_rec)

    notif = Notificacion(
        id=_nuevo_id(),
        cliente_id=cliente_id,
        tipo="exito",
        titulo="Yape enviado",
        mensaje=f"Yapeaste S/ {monto:.2f} a {nombre_destino}",
        created_at=ahora,
    )
    db.add(notif)

    db.commit()

    return {
        "id": op_id,
        "estado": "completada",
        "monto": monto,
        "cuenta_origen": cuenta_origen.cod_cuenta_ahorro,
        "destinatario": nombre_destino,
        "created_at": ahora,
    }


def pagar_cuota(db: Session, cliente_id: str, data: dict) -> dict:
    """Paga una cuota de crédito descontando de la cuenta de ahorro."""
    ahora = _ahora()
    op_id = _nuevo_id()

    cuenta = db.query(CuentaAhorro).filter(
        CuentaAhorro.id == data["cuenta_origen_id"],
        CuentaAhorro.cliente_id == cliente_id,
    ).first()
    if not cuenta:
        return {"error": "Cuenta origen no encontrada"}

    credito = db.query(Credito).filter(
        Credito.id == data["credito_id"],
        Credito.cliente_id == cliente_id,
    ).first()
    if not credito:
        return {"error": "Crédito no encontrado"}

    cuota = db.query(CronogramaPago).filter(
        CronogramaPago.id == data["cuota_id"],
        CronogramaPago.credito_id == credito.id,
    ).first()
    if not cuota:
        return {"error": "Cuota no encontrada"}
    if cuota.estado_cuota == "pagada":
        return {"error": "Esta cuota ya fue pagada"}

    monto_pagar = (cuota.monto_cuota or 0)
    if (cuenta.saldo_capital or 0) < monto_pagar:
        return {"error": f"Saldo insuficiente. Necesitas S/ {monto_pagar:.2f}"}

    cuenta.saldo_capital = (cuenta.saldo_capital or 0) - monto_pagar
    credito.saldo_capital = max(0, (credito.saldo_capital or 0) - (cuota.monto_capital or 0))
    credito.saldo_total = max(0, (credito.saldo_total or 0) - monto_pagar)
    credito.cuotas_pagadas = (credito.cuotas_pagadas or 0) + 1
    cuota.estado_cuota = "pagada"
    cuota.fecha_pago = ahora

    op = Operacion(
        id=op_id,
        cliente_id=cliente_id,
        cod_cuenta_origen=cuenta.cod_cuenta_ahorro,
        tipo="PAGO_CREDITO",
        monto=monto_pagar,
        moneda="PEN",
        estado="completada",
        created_at=ahora,
    )
    db.add(op)

    mov = Movimiento(
        id=_nuevo_id(),
        cliente_id=cliente_id,
        cod_cuenta=cuenta.cod_cuenta_ahorro,
        cod_operacion=op_id,
        tipo="PAGO",
        concepto=f"Pago cuota {cuota.nro_cuota} - Crédito {credito.cod_cuenta_credito or ''}",
        canal="app",
        monto=-monto_pagar,
        moneda="PEN",
        fecha_operacion=ahora,
    )
    db.add(mov)

    notif = Notificacion(
        id=_nuevo_id(),
        cliente_id=cliente_id,
        tipo="exito",
        titulo="Cuota pagada",
        mensaje=f"Pagaste la cuota {cuota.nro_cuota} de tu crédito por S/ {monto_pagar:.2f}",
        created_at=ahora,
    )
    db.add(notif)

    db.commit()

    return {
        "id": op_id,
        "estado": "completada",
        "monto": monto_pagar,
        "cuota": cuota.nro_cuota,
        "nuevo_saldo_capital": credito.saldo_capital,
        "cuotas_pagadas": credito.cuotas_pagadas,
        "total_cuotas": credito.cuotas_total,
        "created_at": ahora,
    }


def recargar_celular(db: Session, cliente_id: str, data: dict) -> dict:
    """Recarga de celular simulada."""
    ahora = _ahora()
    monto = float(data["monto"])
    op_id = _nuevo_id()
    operador = data["operador"]
    telefono = data["telefono"]

    cuenta = db.query(CuentaAhorro).filter(
        CuentaAhorro.id == data["cuenta_origen_id"],
        CuentaAhorro.cliente_id == cliente_id,
    ).first()
    if not cuenta:
        return {"error": "Cuenta origen no encontrada"}
    if (cuenta.saldo_capital or 0) < monto:
        return {"error": "Saldo insuficiente"}

    cuenta.saldo_capital = (cuenta.saldo_capital or 0) - monto

    op = Operacion(
        id=op_id,
        cliente_id=cliente_id,
        cod_cuenta_origen=cuenta.cod_cuenta_ahorro,
        tipo="RECARGA",
        monto=monto,
        moneda="PEN",
        estado="completada",
        created_at=ahora,
    )
    db.add(op)

    comprobante_id = str(uuid.uuid4())[:8].upper()
    mov = Movimiento(
        id=_nuevo_id(),
        cliente_id=cliente_id,
        cod_cuenta=cuenta.cod_cuenta_ahorro,
        cod_operacion=op_id,
        tipo="RECARGA",
        concepto=f"Recarga {operador} - {telefono} - Comp. {comprobante_id}",
        canal="app",
        monto=-monto,
        moneda="PEN",
        fecha_operacion=ahora,
    )
    db.add(mov)

    notif = Notificacion(
        id=_nuevo_id(),
        cliente_id=cliente_id,
        tipo="exito",
        titulo="Recarga exitosa",
        mensaje=f"Recargaste S/ {monto:.2f} a {telefono} ({operador})",
        created_at=ahora,
    )
    db.add(notif)

    db.commit()

    return {
        "id": op_id,
        "comprobante": comprobante_id,
        "estado": "completada",
        "monto": monto,
        "operador": operador,
        "telefono": telefono,
        "created_at": ahora,
    }


def pagar_servicio(db: Session, cliente_id: str, data: dict) -> dict:
    """Pago de servicio simulado."""
    ahora = _ahora()
    monto = float(data["monto"])
    op_id = _nuevo_id()
    servicio = data["servicio"]
    codigo = data["codigo_servicio"]

    cuenta = db.query(CuentaAhorro).filter(
        CuentaAhorro.id == data["cuenta_origen_id"],
        CuentaAhorro.cliente_id == cliente_id,
    ).first()
    if not cuenta:
        return {"error": "Cuenta origen no encontrada"}
    if (cuenta.saldo_capital or 0) < monto:
        return {"error": "Saldo insuficiente"}

    cuenta.saldo_capital = (cuenta.saldo_capital or 0) - monto

    op = Operacion(
        id=op_id,
        cliente_id=cliente_id,
        cod_cuenta_origen=cuenta.cod_cuenta_ahorro,
        tipo="PAGO_SERVICIO",
        monto=monto,
        moneda="PEN",
        estado="completada",
        created_at=ahora,
    )
    db.add(op)

    comprobante_id = str(uuid.uuid4())[:8].upper()
    mov = Movimiento(
        id=_nuevo_id(),
        cliente_id=cliente_id,
        cod_cuenta=cuenta.cod_cuenta_ahorro,
        cod_operacion=op_id,
        tipo="PAGO",
        concepto=f"Pago {servicio} - {codigo} - Comp. {comprobante_id}",
        canal="app",
        monto=-monto,
        moneda="PEN",
        fecha_operacion=ahora,
    )
    db.add(mov)

    notif = Notificacion(
        id=_nuevo_id(),
        cliente_id=cliente_id,
        tipo="exito",
        titulo=f"Pago de {servicio} exitoso",
        mensaje=f"Pagaste S/ {monto:.2f} de {servicio} - {codigo}",
        created_at=ahora,
    )
    db.add(notif)

    db.commit()

    return {
        "id": op_id,
        "comprobante": comprobante_id,
        "estado": "completada",
        "monto": monto,
        "servicio": servicio,
        "codigo_servicio": codigo,
        "created_at": ahora,
    }


def obtener_comprobante(db: Session, cliente_id: str, operacion_id: str) -> dict | None:
    """Obtiene el comprobante de una operación."""
    op = db.query(Operacion).filter(
        Operacion.id == operacion_id,
        Operacion.cliente_id == cliente_id,
    ).first()
    if not op:
        return None

    cli = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    cta_origen = db.query(CuentaAhorro).filter(
        CuentaAhorro.cod_cuenta_ahorro == op.cod_cuenta_origen
    ).first()

    return {
        "id": op.id,
        "tipo": op.tipo,
        "monto": op.monto,
        "moneda": op.moneda or "PEN",
        "estado": op.estado,
        "codigo_operacion": op.id[:8].upper(),
        "cuenta_origen": op.cod_cuenta_origen,
        "cuenta_destino": op.cod_cuenta_destino,
        "descripcion": op.tipo,
        "comision": 0.0,
        "created_at": op.created_at,
        "cliente_nombre": f"{cli.nombres} {cli.apellidos}" if cli else None,
        "cliente_documento": cli.numero_documento if cli else None,
    }


def listar_operaciones_recientes(db: Session, cliente_id: str, limit: int = 20) -> list[dict]:
    """Lista operaciones recientes del cliente."""
    ops = db.query(Operacion).filter(
        Operacion.cliente_id == cliente_id
    ).order_by(Operacion.created_at.desc()).limit(limit).all()
    return [_row_to_dict(o) for o in ops]
