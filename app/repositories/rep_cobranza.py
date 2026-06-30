import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.mdl_all import Credito, Cliente, AccionCobranza


def listar_mora(db: Session) -> list[dict]:
    rows = (
        db.query(Credito, Cliente)
        .join(Cliente, Credito.cliente_id == Cliente.id)
        .filter(Credito.dias_mora > 0)
        .order_by(Credito.dias_mora.desc())
        .all()
    )
    result = []
    for cr, cli in rows:
        result.append({
            "id": cr.id,
            "cod_cuenta_credito": cr.cod_cuenta_credito or "",
            "cliente_id": cr.cliente_id,
            "cliente_nombre": f"{cli.nombres} {cli.apellidos}",
            "documento": cli.numero_documento or "",
            "telefono": cli.telefono,
            "dias_mora": cr.dias_mora or 0,
            "monto_vencido": float(cr.saldo_total or 0),
        })
    return result


def registrar_accion(db: Session, asesor_id: str, d: dict) -> None:
    accion = AccionCobranza(
        id=str(uuid.uuid4()),
        asesor_id=asesor_id,
        cliente_id=d["cliente_id"],
        cod_cuenta_credito=d.get("cod_cuenta_credito"),
        tipo_gestion=d["tipo_gestion"],
        resultado=d["resultado"],
        monto_pagado=d.get("monto_pagado"),
        fecha_compromiso=d.get("fecha_compromiso"),
        monto_compromiso=d.get("monto_compromiso"),
        observaciones=d.get("observaciones", ""),
        lat=d.get("lat"),
        lng=d.get("lng"),
        timestamp_gestion=datetime.now(timezone.utc).isoformat(),
    )
    db.add(accion)
    db.commit()
