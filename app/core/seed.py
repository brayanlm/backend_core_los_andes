import uuid
import random
from datetime import datetime, timezone, timedelta
from app.database.session import SessionLocal
from app.core.cfg_security import hash_password
from app.models.mdl_all import (
    Asesor, Cliente, UsuarioCliente, CuentaAhorro,
    Movimiento, Notificacion, Operacion,
)

def _hace(dias):
    return (datetime.now(timezone.utc) - timedelta(days=dias)).isoformat()

def _nuevo_id():
    return str(uuid.uuid4())

def seed_admin():
    session = SessionLocal()
    try:
        existing = session.query(Asesor).filter(Asesor.codigo_empleado == "000").first()
        if existing:
            return
        asesor = Asesor(
            id=_nuevo_id(),
            codigo_empleado="000",
            email="admin@losandes.com",
            nombres="Administrador",
            apellidos="Los Andes",
            perfil="administrador",
            rol="ASESOR",
            agencia_id="AG-001",
            activo=1,
            password_hash=hash_password("admin123"),
            created_at="2026-01-01T00:00:00Z",
        )
        session.add(asesor)
        session.commit()
    finally:
        session.close()

def seed_asesor():
    session = SessionLocal()
    try:
        existing = session.query(Asesor).filter(Asesor.codigo_empleado == "001").first()
        if existing:
            return
        asesor = Asesor(
            id=_nuevo_id(),
            codigo_empleado="001",
            email="asesor@losandes.com",
            nombres="Juan",
            apellidos="Pérez",
            perfil="operador",
            rol="ASESOR",
            agencia_id="AG-001",
            activo=1,
            password_hash=hash_password("asesor123"),
            created_at="2026-01-01T00:00:00Z",
        )
        session.add(asesor)
        session.commit()
    finally:
        session.close()

def seed_asesor_fv():
    session = SessionLocal()
    try:
        existing = session.query(Asesor).filter(Asesor.codigo_empleado == "0001").first()
        if existing:
            return
        asesor = Asesor(
            id=_nuevo_id(),
            codigo_empleado="0001",
            email="fv@losandes.com",
            nombres="Brayan José",
            apellidos="Ochoa Segovia",
            perfil="operador",
            rol="ASESOR",
            agencia_id="AG-001",
            activo=1,
            password_hash=hash_password("0001123"),
            created_at="2026-01-01T00:00:00Z",
        )
        session.add(asesor)
        session.commit()
    finally:
        session.close()

def seed_clientes_demo():
    session = SessionLocal()
    try:
        existing = session.query(Cliente).filter(Cliente.numero_documento == "12345678").first()
        if existing:
            return

        ahora = datetime.now(timezone.utc)
        clientes_data = [
            {
                "numero_documento": "12345678",
                "nombres": "María",
                "apellidos": "García López",
                "telefono": "999000111",
                "email": "maria.garcia@email.com",
                "direccion": "Av. Principal 123, Lima",
                "tipo_negocio": "comercio",
                "nombre_negocio": "Bodega María",
                "antiguedad_negocio_meses": 36,
                "calificacion_sbs": "NORMAL",
                "saldo_cuenta": 8500.00,
                "movimientos": [
                    ("DEPOSITO", "Depósito por ventas", 3200.00, 15),
                    ("TRANSFERENCIA", "Transferencia a proveedor", -1200.00, 12),
                    ("PAGO", "Pago de servicios", -350.00, 10),
                    ("TRANSFERENCIA_ENTRANTE", "Transferencia recibida", 800.00, 7),
                    ("PAGO", "Pago cuota crédito", -450.00, 3),
                ],
                "notificaciones": [
                    ("recordatorio", "Recordatorio de pago", "Tu cuota del crédito vence en 5 días", 5),
                    ("exito", "Transferencia exitosa", "Transferencia a Pedro López por S/ 1,200.00", 3),
                    ("promocion", "Nueva oferta", "Preaprobado para ampliación de línea hasta S/ 5,000", 1),
                ],
            },
            {
                "numero_documento": "23456789",
                "nombres": "Pedro",
                "apellidos": "López Ramírez",
                "telefono": "999000222",
                "email": "pedro.lopez@email.com",
                "direccion": "Jr. Las Flores 456, Arequipa",
                "tipo_negocio": "comercio",
                "nombre_negocio": "Ferretería López",
                "antiguedad_negocio_meses": 60,
                "calificacion_sbs": "NORMAL",
                "saldo_cuenta": 3250.00,
                "movimientos": [
                    ("DEPOSITO", "Depósito por ventas", 1800.00, 20),
                    ("TRANSFERENCIA", "Transferencia a cuenta", -500.00, 18),
                    ("PAGO", "Recarga celular", -30.00, 15),
                    ("TRANSFERENCIA_ENTRANTE", "Pago de cliente", 650.00, 10),
                    ("PAGO", "Pago cuota crédito", -280.00, 5),
                ],
                "notificaciones": [
                    ("exito", "Cuota pagada", "Cuota 6 de tu crédito fue pagada exitosamente", 5),
                    ("recordatorio", "¡No te pierdas esta oferta!", "Tasa preferencial para tu próximo crédito", 2),
                ],
            },
            {
                "numero_documento": "34567890",
                "nombres": "Ana Cecilia",
                "apellidos": "Torres Mendoza",
                "telefono": "999000333",
                "email": "ana.torres@email.com",
                "direccion": "Calle Real 789, Cusco",
                "tipo_negocio": "servicios",
                "nombre_negocio": "Centro de Belleza Ana",
                "antiguedad_negocio_meses": 24,
                "calificacion_sbs": "NORMAL",
                "saldo_cuenta": 15000.00,
                "movimientos": [
                    ("DEPOSITO", "Depósito por servicios", 5000.00, 25),
                    ("DEPOSITO", "Depósito por ventas", 2500.00, 20),
                    ("TRANSFERENCIA", "Transferencia a proveedor", -800.00, 18),
                    ("PAGO", "Pago de servicios", -200.00, 12),
                    ("TRANSFERENCIA_ENTRANTE", "Transferencia recibida de cliente", 1500.00, 8),
                    ("PAGO", "Pago de luz", -180.00, 4),
                ],
                "notificaciones": [
                    ("promocion", "Crédito preaprobado", "Tienes S/ 15,000 preaprobados para tu negocio", 3),
                    ("exito", "Depósito recibido", "Depósito de S/ 5,000.00 en tu cuenta", 1),
                ],
            },
            {
                "numero_documento": "45678901",
                "nombres": "Luis Alberto",
                "apellidos": "Ramos Castillo",
                "telefono": "999000444",
                "email": "luis.ramos@email.com",
                "direccion": "Av. Central 321, Trujillo",
                "tipo_negocio": "transporte",
                "nombre_negocio": "Transportes Ramos",
                "antiguedad_negocio_meses": 48,
                "calificacion_sbs": "NORMAL",
                "saldo_cuenta": 12200.00,
                "movimientos": [
                    ("DEPOSITO", "Depósito por servicio de transporte", 4200.00, 22),
                    ("TRANSFERENCIA", "Pago a mecánico", -1500.00, 19),
                    ("TRANSFERENCIA_ENTRANTE", "Pago de cliente corporativo", 3200.00, 14),
                    ("PAGO", "Pago cuota crédito", -580.00, 8),
                    ("PAGO", "Pago de gasolina", -350.00, 3),
                ],
                "notificaciones": [
                    ("exito", "Pago recibido", "Recibiste S/ 3,200.00 de Cliente Corporativo", 14),
                    ("recordatorio", "Próxima cuota", "Cuota 5 de tu crédito vence en 7 días", 2),
                ],
            },
            {
                "numero_documento": "56789012",
                "nombres": "Sofía Isabel",
                "apellidos": "Díaz Paredes",
                "telefono": "999000555",
                "email": "sofia.diaz@email.com",
                "direccion": "Jr. Los Olivos 654, Piura",
                "tipo_negocio": "comercio",
                "nombre_negocio": "Tienda Sofía",
                "antiguedad_negocio_meses": 18,
                "calificacion_sbs": "NORMAL",
                "saldo_cuenta": 5600.00,
                "movimientos": [
                    ("DEPOSITO", "Depósito por ventas", 1800.00, 14),
                    ("TRANSFERENCIA", "Transferencia a proveedor", -600.00, 11),
                    ("TRANSFERENCIA_ENTRANTE", "Pago de cliente", 400.00, 7),
                    ("PAGO", "Recarga celular", -20.00, 4),
                    ("PAGO", "Pago de servicios", -150.00, 2),
                ],
                "notificaciones": [
                    ("promocion", "¡Tu tienda crece!", "Solicita un crédito desde S/ 3,000 para tu negocio", 6),
                    ("exito", "¡Bienvenida!", "Gracias por confiar en Banco Los Andes", 30),
                ],
            },
        ]

        clientes_ids = []
        for d in clientes_data:
            cli_id = _nuevo_id()
            cli = Cliente(
                id=cli_id,
                numero_documento=d["numero_documento"],
                nombres=d["nombres"],
                apellidos=d["apellidos"],
                telefono=d["telefono"],
                email=d["email"],
                direccion=d["direccion"],
                tipo_negocio=d["tipo_negocio"],
                nombre_negocio=d["nombre_negocio"],
                antiguedad_negocio_meses=d["antiguedad_negocio_meses"],
                calificacion_sbs=d["calificacion_sbs"],
            )
            session.add(cli)
            session.flush()
            clientes_ids.append(cli_id)

            usr = UsuarioCliente(
                id=_nuevo_id(),
                cliente_id=cli_id,
                username=d["numero_documento"],
                password_hash=hash_password(d["numero_documento"]),
                activo=1,
                created_at=_hace(30),
            )
            session.add(usr)

            cc = d["numero_documento"]
            cuenta_id = _nuevo_id()
            cod_cta = f"001-{cc}-{str(uuid.uuid4())[:8].upper()}"
            cci = f"002{cc}0{cod_cta.replace('-', '')}29"
            cuenta = CuentaAhorro(
                id=cuenta_id,
                cliente_id=cli_id,
                cod_cuenta_ahorro=cod_cta,
                cci=cci,
                tipo_cuenta="ahorro",
                moneda="PEN",
                saldo_capital=d["saldo_cuenta"],
                saldo_interes=0,
                tea=0.005,
                estado="activa",
                created_at=_hace(60),
            )
            session.add(cuenta)
            session.flush()

            for idx, (tipo, concepto, monto, dias) in enumerate(d["movimientos"]):
                mov = Movimiento(
                    id=_nuevo_id(),
                    cliente_id=cli_id,
                    cod_cuenta=cod_cta,
                    tipo=tipo,
                    concepto=concepto,
                    monto=monto,
                    moneda="PEN",
                    fecha_operacion=_hace(dias),
                )
                session.add(mov)

            for idx, (tipo, titulo, mensaje, dias) in enumerate(d["notificaciones"]):
                notif = Notificacion(
                    id=_nuevo_id(),
                    cliente_id=cli_id,
                    tipo=tipo,
                    titulo=titulo,
                    mensaje=mensaje,
                    leida=1 if dias > 15 else 0,
                    created_at=_hace(dias),
                )
                session.add(notif)

        session.commit()
    finally:
        session.close()

def seed_cliente_prueba():
    """Cliente de prueba con saldo en cuenta, sin crédito activo, para simular Yape/transferencias."""
    import logging
    logger = logging.getLogger("core_mobile")
    session = SessionLocal()
    try:
        dni = "99999999"
        existing = session.query(UsuarioCliente).filter(UsuarioCliente.username == dni).first()
        if existing:
            return

        cli_id = _nuevo_id()
        ahora = datetime.now(timezone.utc)
        logger.info("Creando cliente de prueba DNI=%s ...", dni)

        cli = Cliente(
            id=cli_id,
            numero_documento=dni,
            nombres="Usuario Test",
            apellidos="Yape Transfer",
            telefono="999000999",
            email="test.yape@email.com",
            direccion="Av. Prueba 456, Lima",
            tipo_negocio="servicios",
            nombre_negocio="Test EIRL",
            antiguedad_negocio_meses=12,
            calificacion_sbs="NORMAL",
        )
        session.add(cli)

        usr = UsuarioCliente(
            id=_nuevo_id(),
            cliente_id=cli_id,
            username=dni,
            password_hash=hash_password(dni),
            activo=1,
            intentos_fallidos=0,
            created_at=(ahora - timedelta(days=30)).isoformat(),
        )
        session.add(usr)
        session.flush()

        cod_cta = f"001-{dni}-{str(uuid.uuid4())[:8].upper()}"
        cci = f"002{dni}0{cod_cta.replace('-', '')}29"
        cuenta = CuentaAhorro(
            id=_nuevo_id(),
            cliente_id=cli_id,
            cod_cuenta_ahorro=cod_cta,
            cci=cci,
            tipo_cuenta="ahorro",
            moneda="PEN",
            saldo_capital=5000.00,
            saldo_interes=0,
            tea=0.005,
            estado="activa",
            created_at=(ahora - timedelta(days=60)).isoformat(),
        )
        session.add(cuenta)
        session.flush()

        movimientos = [
            ("DEPOSITO", "Depósito inicial", 5000.00, 15),
        ]
        for idx, (tipo, concepto, monto, dias) in enumerate(movimientos):
            mov = Movimiento(
                id=_nuevo_id(),
                cliente_id=cli_id,
                cod_cuenta=cod_cta,
                tipo=tipo,
                concepto=concepto,
                monto=monto,
                moneda="PEN",
                fecha_operacion=(ahora - timedelta(days=dias)).isoformat(),
            )
            session.add(mov)

        notificaciones = [
            ("bienvenida", "¡Bienvenido!", "Tu cuenta está lista para usar Yape y transferencias", 1),
        ]
        for idx, (tipo, titulo, mensaje, dias) in enumerate(notificaciones):
            notif = Notificacion(
                id=_nuevo_id(),
                cliente_id=cli_id,
                tipo=tipo,
                titulo=titulo,
                mensaje=mensaje,
                leida=0,
                created_at=(ahora - timedelta(days=dias)).isoformat(),
            )
            session.add(notif)

        session.commit()
        logger.info("Cliente de prueba creado: DNI=%s / password=%s / saldo=S/5000", dni, dni)
    except Exception as e:
        logger.error("Error creando cliente prueba: %s", e)
        session.rollback()
    finally:
        session.close()


def seed_creditos_demo():
    """Crea solicitudes y créditos demo para que los reportes muestren datos reales."""
    import logging
    from app.models.mdl_all import SolicitudCredito, Credito, CronogramaPago
    from app.services.svc_financiero import calcular_cuota_mensual, generar_cronograma
    logger = logging.getLogger("core_mobile")
    session = SessionLocal()
    try:
        existing = session.query(SolicitudCredito).first()
        if existing:
            return
        admin = session.query(Asesor).filter(Asesor.codigo_empleado == "000").first()
        asesor_juan = session.query(Asesor).filter(Asesor.codigo_empleado == "001").first()
        asesor_brayan = session.query(Asesor).filter(Asesor.codigo_empleado == "0001").first()
        clientes = session.query(Cliente).all()
        if not admin or not clientes:
            logger.warning("No hay asesores o clientes para seed creditos")
            return
        ahora = datetime.now(timezone.utc)
        estados_solicitud = ["enviado", "recibido_comite", "en_evaluacion", "aprobado", "desembolsado", "rechazado"]
        asesores = [a for a in [asesor_juan, asesor_brayan, admin] if a]
        for idx, cli in enumerate(clientes[:5]):
            asesor = asesores[idx % len(asesores)]
            monto = round(5000 + idx * 3500 + (idx * idx * 200), -2)
            plazo = 12 + (idx * 6)
            tea = 0.25 - (idx * 0.01)
            cuota = calcular_cuota_mensual(monto, plazo, tea)
            ingreso = round(monto * random.uniform(0.15, 0.35), 0)
            estado = estados_solicitud[idx % len(estados_solicitud)]
            score = random.randint(55, 95)
            sol_id = _nuevo_id()
            sol = SolicitudCredito(
                id=sol_id,
                numero_expediente=f"EXP-DEMO-{str(idx+1).zfill(3)}",
                asesor_id=asesor.id if estado != "rechazado" else None,
                cliente_id=cli.id,
                agencia_id="AG-001",
                canal="asesor",
                tipo_negocio=cli.tipo_negocio or "comercio",
                nombre_negocio=cli.nombre_negocio or f"Negocio {cli.nombres}",
                ingresos=ingreso,
                monto=monto,
                plazo=plazo,
                moneda="PEN",
                destino_credito="capital_trabajo",
                garantia="sin_garantia",
                tea_referencial=tea,
                cuota_estimada=cuota,
                score_usado=score,
                estado=estado,
                visita_registrada=1 if estado != "enviado" else 0,
                preevaluacion_realizada=1 if estado not in ("enviado",) else 0,
                buro_consultado=1 if estado not in ("enviado",) else 0,
                documentos_completos=1 if estado not in ("enviado",) else 0,
                created_at=_hace(30 - idx * 5),
            )
            session.add(sol)
            session.flush()
            if estado in ("aprobado", "desembolsado"):
                cred_id = _nuevo_id()
                cred = Credito(
                    id=cred_id,
                    solicitud_id=sol_id,
                    cliente_id=cli.id,
                    asesor_id=asesor.id,
                    cod_cuenta_credito=f"CRED-{str(idx+1).zfill(4)}",
                    producto="credito_microempresa",
                    monto=monto,
                    monto_desembolsado=monto if estado == "desembolsado" else None,
                    saldo_capital=monto * 0.85,
                    saldo_total=monto * 1.02,
                    plazo_meses=plazo,
                    tasa=tea,
                    tea=tea,
                    ingreso_cliente=ingreso,
                    cuota_estimada=cuota,
                    ratio_cuota_ingreso=round(cuota / ingreso, 4) if ingreso else 0,
                    estado="DESEMBOLSADO" if estado == "desembolsado" else "APROBADO",
                    score=score,
                    destino="capital_trabajo",
                    cuotas_total=plazo,
                    cuotas_pagadas=round(plazo * 0.2) if estado == "desembolsado" else 0,
                    dias_mora=random.choice([0, 0, 0, 5, 15]),
                    fecha_creacion=(ahora - timedelta(days=25 - idx * 3)).isoformat(),
                    fecha_aprobacion=(ahora - timedelta(days=23 - idx * 3)).isoformat(),
                    fecha_desembolso=(ahora - timedelta(days=20 - idx * 3)).isoformat() if estado == "desembolsado" else None,
                )
                session.add(cred)
                session.flush()
                sol.credito_id = cred_id
                cronograma, total_int, total_pagar = generar_cronograma(monto, plazo, tea)
                for cuota_item in cronograma:
                    cp = CronogramaPago(
                        id=_nuevo_id(),
                        credito_id=cred_id,
                        nro_cuota=cuota_item["nro_cuota"],
                        fecha_vencimiento=cuota_item["fecha_vencimiento"],
                        monto_cuota=cuota_item["monto_cuota"],
                        monto_capital=cuota_item["monto_capital"],
                        monto_interes=cuota_item["monto_interes"],
                        saldo=cuota_item["saldo"],
                        estado_cuota="pagada" if cuota_item["nro_cuota"] <= cred.cuotas_pagadas else "pendiente",
                        created_at=_hace(20 - idx * 3),
                    )
                    session.add(cp)
        session.commit()
        total = session.query(SolicitudCredito).count()
        logger.info("Seed creditos demo: %s solicitudes y creditos creados", total)
    except Exception as e:
        logger.error("Error seed creditos demo: %s", e)
        session.rollback()
    finally:
        session.close()

def seed_clientes_sqlite():
    pass

def seed_asesores_sqlite():
    pass

def seed_cartera_demo():
    pass
