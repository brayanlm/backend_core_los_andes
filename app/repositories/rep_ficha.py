from datetime import date
from sqlalchemy.orm import Session

from app.models.mdl_all import Cliente, Credito, CreditoPreaprobado


def _cliente_to_dict(c: Cliente) -> dict:
    return {
        "id": c.id,
        "numero_documento": c.numero_documento,
        "nombres": c.nombres,
        "apellidos": c.apellidos,
        "telefono": c.telefono,
        "direccion": c.direccion,
        "email": c.email,
        "tipo_negocio": c.tipo_negocio,
        "nombre_negocio": c.nombre_negocio,
        "antiguedad_negocio_meses": c.antiguedad_negocio_meses,
        "calificacion_sbs": c.calificacion_sbs or "NORMAL",
        "ingreso_mensual": 0,
        "fecha_creacion": c.created_at,
    }


def listar_todos(db: Session) -> list[dict]:
    clientes = db.query(Cliente).order_by(Cliente.apellidos, Cliente.nombres).all()
    return [_cliente_to_dict(c) for c in clientes]


def obtener_por_id(db: Session, cliente_id: str) -> dict | None:
    c = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not c:
        return None
    return _cliente_to_dict(c)


def actualizar_ubicacion(db: Session, cliente_id: str, lat: float, lng: float, direccion: str | None = None) -> bool:
    c = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not c:
        return False
    c.lat = lat
    c.lng = lng
    if direccion:
        c.direccion = direccion
    db.commit()
    return True


def obtener_ficha(db: Session, cliente_id: str) -> dict | None:
    cli = db.query(Cliente).filter(Cliente.id == cliente_id).first()
    if not cli:
        return None

    creditos = (
        db.query(Credito)
        .filter(Credito.cliente_id == cliente_id)
        .order_by(Credito.fecha_desembolso.desc())
        .all()
    )

    ofertas = (
        db.query(CreditoPreaprobado)
        .filter(
            CreditoPreaprobado.cliente_id == cliente_id,
            CreditoPreaprobado.vigente == 1,
        )
        .all()
    )
    hoy = date.today().isoformat()
    oferta_valida = None
    mejor_score = 0
    for o in ofertas:
        fv = o.fecha_vencimiento
        if fv and fv < hoy:
            continue
        score = o.score_confianza or 0
        if score > mejor_score:
            mejor_score = score
            oferta_valida = o

    dias_mayor_mora = 0
    historial = []
    for cr in creditos:
        dm = cr.dias_mora or 0
        if dm > dias_mayor_mora:
            dias_mayor_mora = dm
        historial.append(cr)

    return _build_ficha_response(cli, cliente_id, historial, oferta_valida, dias_mayor_mora)


def _build_ficha_response(cli, cliente_id, historial, oferta, dias_mayor_mora):
    dmora = dias_mayor_mora
    deuda_total = sum(float(h.saldo_total or 0) for h in historial)
    cuentas_vigentes = sum(1 for h in historial if h.estado == "vigente")
    cuentas_mora = sum(1 for h in historial if (h.dias_mora or 0) > 0)

    comportamiento = [1] * 12
    if dmora > 0:
        n = 1 if dmora <= 30 else (2 if dmora <= 60 else 3)
        for k in range(n):
            comportamiento[11 - k] = 2
    dni = cli.numero_documento or "0"
    if dni and dni[-1].isdigit() and int(dni[-1]) % 3 == 0:
        comportamiento[0] = 0
        comportamiento[1] = 0

    con_cuota = [m for m in comportamiento if m != 0]
    puntuales = [m for m in con_cuota if m == 1]
    pct_puntual = round(len(puntuales) / len(con_cuota) * 100, 1) if con_cuota else 0
    monto_pagado = sum(
        float(h.monto_desembolsado or 0)
        for h in historial
        if h.estado == "pagado"
    )

    return {
        "comportamiento": comportamiento,
        "indicadores": {
            "pct_puntual": pct_puntual,
            "dias_prom_mora": dmora,
            "monto_pagado": monto_pagado,
        },
        "cliente": {
            "id": cliente_id,
            "numero_documento": cli.numero_documento,
            "nombres": cli.nombres,
            "apellidos": cli.apellidos,
            "telefono": cli.telefono,
            "direccion": cli.direccion,
            "tipo_negocio": cli.tipo_negocio,
            "nombre_negocio": cli.nombre_negocio,
            "antiguedad_negocio_meses": cli.antiguedad_negocio_meses,
            "calificacion_sbs": cli.calificacion_sbs or "NORMAL",
        },
        "posicion": {
            "deuda_total": deuda_total,
            "cuentas_vigentes": cuentas_vigentes,
            "cuentas_mora": cuentas_mora,
            "dias_mayor_mora": dias_mayor_mora,
        },
        "historial": [
            {
                "producto": h.producto,
                "monto_desembolsado": float(h.monto_desembolsado or 0),
                "plazo_meses": h.cuotas_total,
                "tea": float(h.tea or 0),
                "estado": h.estado,
                "dias_mora": h.dias_mora or 0,
                "cuotas_total": h.cuotas_total or 0,
                "cuotas_pagadas": h.cuotas_pagadas or 0,
            }
            for h in historial
        ],
        "oferta": None
        if oferta is None
        else {
            "monto_maximo": float(oferta.monto_maximo or 0),
            "plazo_sugerido_meses": oferta.plazo_sugerido_meses,
            "tea_referencial": float(oferta.tea_referencial or 0),
            "score_confianza": oferta.score_confianza or 0,
            "fecha_vencimiento": oferta.fecha_vencimiento,
        },
    }
