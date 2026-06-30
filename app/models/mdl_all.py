import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, String, Integer, Float, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.database.session import Base


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


def _new_id():
    return str(uuid.uuid4())


class Cliente(Base):
    __tablename__ = "cr_cliente"

    id = Column(String, primary_key=True, default=_new_id)
    numero_documento = Column(String, unique=True, nullable=False, index=True)
    nombres = Column(String, nullable=False)
    apellidos = Column(String, nullable=False)
    telefono = Column(String)
    direccion = Column(String)
    email = Column(String)
    tipo_negocio = Column(String)
    nombre_negocio = Column(String)
    antiguedad_negocio_meses = Column(Integer)
    calificacion_sbs = Column(String, default="NORMAL")
    lat = Column(Float)
    lng = Column(Float)
    es_prospecto = Column(Integer, default=0)
    created_at = Column(String, default=_utc_now)

    usuario = relationship("UsuarioCliente", back_populates="cliente", uselist=False)
    solicitudes = relationship("SolicitudCredito", back_populates="cliente")
    creditos = relationship("Credito", back_populates="cliente")
    movimientos = relationship("Movimiento", back_populates="cliente")
    visitas = relationship("Visita", back_populates="cliente")


class UsuarioCliente(Base):
    __tablename__ = "cr_usuario_cliente"

    id = Column(String, primary_key=True, default=_new_id)
    cliente_id = Column(String, ForeignKey("cr_cliente.id"), nullable=False)
    username = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    intentos_fallidos = Column(Integer, default=0)
    bloqueado_hasta = Column(String)
    activo = Column(Integer, default=1)
    created_at = Column(String, default=_utc_now)

    cliente = relationship("Cliente", back_populates="usuario")


class Asesor(Base):
    __tablename__ = "cr_asesor"

    id = Column(String, primary_key=True, default=_new_id)
    codigo_empleado = Column(String, unique=True, nullable=False)
    email = Column(String)
    nombres = Column(String, nullable=False)
    apellidos = Column(String, nullable=False)
    perfil = Column(String, default="operador")
    rol = Column(String, default="ASESOR")
    agencia_id = Column(String)
    activo = Column(Integer, default=1)
    password_hash = Column(String)
    intentos_fallidos = Column(Integer, default=0)
    bloqueado_hasta = Column(String)
    created_at = Column(String, default=_utc_now, index=True)

    solicitudes = relationship("SolicitudCredito", back_populates="asesor")
    creditos = relationship("Credito", back_populates="asesor")
    visitas = relationship("Visita", back_populates="asesor")


class SolicitudCredito(Base):
    __tablename__ = "cr_solicitud_credito"

    id = Column(String, primary_key=True, default=_new_id)
    numero_expediente = Column(String, unique=True, nullable=False)
    asesor_id = Column(String, ForeignKey("cr_asesor.id"), index=True)
    cliente_id = Column(String, ForeignKey("cr_cliente.id"), nullable=False, index=True)
    agencia_id = Column(String)
    canal = Column(String, default="asesor")
    tipo_negocio = Column(String)
    nombre_negocio = Column(String)
    ingresos = Column(Float)
    monto = Column(Float, nullable=False)
    plazo = Column(Integer, nullable=False)
    moneda = Column(String, default="PEN")
    tipo_cuota = Column(String, default="mensual")
    garantia = Column(String, default="sin_garantia")
    destino_credito = Column(String)
    cuota_estimada = Column(Float)
    tea_referencial = Column(Float)
    firma_cliente_base64 = Column(Text)
    estado = Column(String, default="enviado", index=True)
    credito_id = Column(String, ForeignKey("cr_credito.id"))
    evaluado_por = Column(String)
    evaluado_nombre = Column(String)
    fecha_evaluacion = Column(String)
    monto_aprobado = Column(Float)
    motivo_rechazo = Column(String)
    tasa_sugerida = Column(Float)
    score_usado = Column(Integer, default=0)
    condiciones = Column(Text)
    visita_registrada = Column(Integer, default=0)
    preevaluacion_realizada = Column(Integer, default=0)
    buro_consultado = Column(Integer, default=0)
    documentos_completos = Column(Integer, default=0)
    firma_capturada = Column(Integer, default=0)
    created_at = Column(String, default=_utc_now, index=True)

    cliente = relationship("Cliente", back_populates="solicitudes")
    asesor = relationship("Asesor", back_populates="solicitudes")
    credito = relationship("Credito", uselist=False, viewonly=True,
                           foreign_keys="SolicitudCredito.credito_id")
    documentos = relationship("Documento", back_populates="solicitud")
    visitas = relationship("Visita", back_populates="solicitud")
    preevaluaciones = relationship("Preevaluacion", back_populates="solicitud")
    buro_consultas = relationship("BuroConsulta", back_populates="solicitud")


class Credito(Base):
    __tablename__ = "cr_credito"

    id = Column(String, primary_key=True, default=_new_id)
    solicitud_id = Column(String, ForeignKey("cr_solicitud_credito.id"))
    cliente_id = Column(String, ForeignKey("cr_cliente.id"), nullable=False, index=True)
    asesor_id = Column(String, ForeignKey("cr_asesor.id"), index=True)
    cod_cuenta_credito = Column(String)
    producto = Column(String, default="credito_microempresa")
    monto = Column(Float, nullable=False)
    monto_desembolsado = Column(Float)
    saldo_capital = Column(Float)
    saldo_total = Column(Float)
    plazo_meses = Column(Integer, nullable=False)
    tasa = Column(Float)
    tea = Column(Float)
    ingreso_cliente = Column(Float)
    cuota_estimada = Column(Float)
    ratio_cuota_ingreso = Column(Float)
    estado = Column(String, default="APROBADO")
    score = Column(Integer, default=500)
    calificacion_interna = Column(String)
    dias_mora = Column(Integer, default=0)
    cuotas_total = Column(Integer)
    cuotas_pagadas = Column(Integer)
    destino = Column(String)
    motivo_rechazo = Column(String)
    fecha_creacion = Column(String, default=_utc_now, index=True)
    fecha_evaluacion = Column(String)
    fecha_aprobacion = Column(String)
    fecha_desembolso = Column(String)

    cliente = relationship("Cliente", back_populates="creditos")
    asesor = relationship("Asesor", back_populates="creditos")
    solicitud = relationship("SolicitudCredito", uselist=False, viewonly=True,
                             foreign_keys="Credito.solicitud_id")
    cronograma = relationship("CronogramaPago", back_populates="credito")


class CronogramaPago(Base):
    __tablename__ = "cr_cronograma_pago"

    id = Column(String, primary_key=True, default=_new_id)
    credito_id = Column(String, ForeignKey("cr_credito.id"), nullable=False, index=True)
    nro_cuota = Column(Integer, nullable=False)
    fecha_vencimiento = Column(String)
    monto_cuota = Column(Float)
    monto_capital = Column(Float)
    monto_interes = Column(Float)
    saldo = Column(Float)
    estado_cuota = Column(String, default="pendiente")
    fecha_pago = Column(String)
    created_at = Column(String, default=_utc_now)

    credito = relationship("Credito", back_populates="cronograma")


class Movimiento(Base):
    __tablename__ = "cr_movimiento"

    id = Column(String, primary_key=True, default=_new_id)
    cliente_id = Column(String, ForeignKey("cr_cliente.id"), nullable=False, index=True)
    cod_cuenta = Column(String)
    cod_operacion = Column(String)
    tipo = Column(String)
    concepto = Column(String)
    canal = Column(String)
    monto = Column(Float, nullable=False)
    moneda = Column(String, default="PEN")
    fecha_operacion = Column(String, default=_utc_now)

    cliente = relationship("Cliente", back_populates="movimientos")


class Documento(Base):
    __tablename__ = "cr_documento"

    id = Column(String, primary_key=True, default=_new_id)
    solicitud_id = Column(String, ForeignKey("cr_solicitud_credito.id"), nullable=False, index=True)
    tipo = Column(String, nullable=False)
    nombre_archivo = Column(String)
    contenido_base64 = Column(Text)
    created_at = Column(String, default=_utc_now)

    solicitud = relationship("SolicitudCredito", back_populates="documentos")


class Visita(Base):
    __tablename__ = "cr_visita"

    id = Column(String, primary_key=True, default=_new_id)
    solicitud_id = Column(String, ForeignKey("cr_solicitud_credito.id"), index=True)
    asesor_id = Column(String, ForeignKey("cr_asesor.id"), nullable=False)
    cliente_id = Column(String, ForeignKey("cr_cliente.id"), nullable=False)
    lat = Column(Float)
    lng = Column(Float)
    observacion = Column(String)
    resultado = Column(String)
    created_at = Column(String, default=_utc_now)

    solicitud = relationship("SolicitudCredito", back_populates="visitas")
    asesor = relationship("Asesor", back_populates="visitas")
    cliente = relationship("Cliente", back_populates="visitas")


class CarteraDiaria(Base):
    __tablename__ = "cr_cartera_diaria"

    id = Column(String, primary_key=True, default=_new_id)
    asesor_id = Column(String, ForeignKey("cr_asesor.id"), nullable=False, index=True)
    cliente_id = Column(String, ForeignKey("cr_cliente.id"), nullable=False)
    fecha_asignacion = Column(String, nullable=False)
    tipo_gestion = Column(String)
    prioridad = Column(String, default="normal")
    score_prioridad = Column(Integer, default=0)
    monto_credito = Column(Float, default=0.0)
    estado_visita = Column(String, default="pendiente")
    orden_manual = Column(Integer)
    lat = Column(Float)
    lng = Column(Float)
    resultado_visita = Column(String)
    observacion_visita = Column(String)
    timestamp_visita = Column(String)
    lat_visita = Column(Float)
    lng_visita = Column(Float)


class SyncOutbox(Base):
    __tablename__ = "cr_sync_outbox"

    id = Column(String, primary_key=True, default=_new_id)
    entidad = Column(String, nullable=False)
    operacion = Column(String, nullable=False)
    datos = Column(Text, nullable=False)
    estado = Column(String, default="pendiente")
    error_msg = Column(String)
    intentos = Column(Integer, default=0)
    created_at = Column(String, default=_utc_now)
    procesado_at = Column(String)


class SyncLog(Base):
    __tablename__ = "cr_sync_log"

    id = Column(String, primary_key=True, default=_new_id)
    tipo = Column(String, nullable=False)
    entidad = Column(String, nullable=False)
    registros = Column(Integer, default=0)
    resultado = Column(String, default="ok")
    detalle = Column(String)
    created_at = Column(String, default=_utc_now)


class CuentaAhorro(Base):
    __tablename__ = "cr_cuenta_ahorro"

    id = Column(String, primary_key=True, default=_new_id)
    cliente_id = Column(String, ForeignKey("cr_cliente.id"), nullable=False, index=True)
    cod_cuenta_ahorro = Column(String, unique=True)
    cci = Column(String, unique=True)
    tipo_cuenta = Column(String)
    moneda = Column(String, default="PEN")
    saldo_capital = Column(Float, default=0.0)
    saldo_interes = Column(Float, default=0.0)
    tea = Column(Float)
    estado = Column(String, default="activa")
    created_at = Column(String, default=_utc_now)


class Tarjeta(Base):
    __tablename__ = "cr_tarjeta"

    id = Column(String, primary_key=True, default=_new_id)
    cliente_id = Column(String, ForeignKey("cr_cliente.id"), nullable=False)
    numero_enmascarado = Column(String)
    marca = Column(String)
    linea_credito = Column(Float, default=0.0)
    saldo_utilizado = Column(Float, default=0.0)
    fecha_corte = Column(String)
    fecha_pago = Column(String)
    estado = Column(String, default="activa")
    created_at = Column(String, default=_utc_now)


class Notificacion(Base):
    __tablename__ = "cr_notificacion"

    id = Column(String, primary_key=True, default=_new_id)
    cliente_id = Column(String, ForeignKey("cr_cliente.id"), nullable=False, index=True)
    tipo = Column(String)
    titulo = Column(String, nullable=False)
    mensaje = Column(String)
    cuerpo = Column(String)
    leida = Column(Integer, default=0)
    created_at = Column(String, default=_utc_now)


class Operacion(Base):
    __tablename__ = "cr_operacion"

    id = Column(String, primary_key=True, default=_new_id)
    cliente_id = Column(String, ForeignKey("cr_cliente.id"), nullable=False)
    cod_cuenta_origen = Column(String)
    cod_cuenta_destino = Column(String)
    tipo = Column(String, nullable=False)
    monto = Column(Float, nullable=False)
    moneda = Column(String, default="PEN")
    estado = Column(String, default="pendiente")
    created_at = Column(String, default=_utc_now)


class AccionCobranza(Base):
    __tablename__ = "cr_accion_cobranza"

    id = Column(String, primary_key=True, default=_new_id)
    asesor_id = Column(String, ForeignKey("cr_asesor.id"))
    cliente_id = Column(String, ForeignKey("cr_cliente.id"), nullable=False)
    cod_cuenta_credito = Column(String)
    tipo_gestion = Column(String, nullable=False)
    resultado = Column(String, nullable=False)
    monto_pagado = Column(Float)
    fecha_compromiso = Column(String)
    monto_compromiso = Column(Float)
    observaciones = Column(String, default="")
    lat = Column(Float)
    lng = Column(Float)
    timestamp_gestion = Column(String, default=_utc_now)


class AlertaCartera(Base):
    __tablename__ = "cr_alerta_cartera"

    id = Column(String, primary_key=True, default=_new_id)
    asesor_id = Column(String, ForeignKey("cr_asesor.id"), index=True)
    cliente_id = Column(String, ForeignKey("cr_cliente.id"), nullable=False)
    tipo_alerta = Column(String, nullable=False)
    mensaje = Column(String, default="")
    leida = Column(Integer, default=0)
    created_at = Column(String, default=_utc_now)


class CampanaActiva(Base):
    __tablename__ = "cr_campana_activa"

    id = Column(String, primary_key=True, default=_new_id)
    asesor_id = Column(String, ForeignKey("cr_asesor.id"), index=True)
    cliente_id = Column(String, ForeignKey("cr_cliente.id"), nullable=False)
    tipo = Column(String)
    monto_ofertado = Column(Float, default=0)
    fecha_vencimiento = Column(String)
    activa = Column(Integer, default=1)
    created_at = Column(String, default=_utc_now)


class CreditoPreaprobado(Base):
    __tablename__ = "cr_credito_preaprobado"

    id = Column(String, primary_key=True, default=_new_id)
    cliente_id = Column(String, ForeignKey("cr_cliente.id"), nullable=False)
    monto_maximo = Column(Float, nullable=False)
    plazo_sugerido_meses = Column(Integer)
    tea_referencial = Column(Float)
    score_confianza = Column(Integer, default=0)
    vigente = Column(Integer, default=1)
    fecha_vencimiento = Column(String)
    created_at = Column(String, default=_utc_now)


class HistorialCredito(Base):
    __tablename__ = "cr_historial_credito"

    id = Column(String, primary_key=True, default=_new_id)
    credito_id = Column(String, ForeignKey("cr_credito.id"), nullable=False)
    estado_anterior = Column(String)
    estado_nuevo = Column(String, nullable=False)
    usuario_id = Column(String)
    usuario_nombre = Column(String)
    comentario = Column(String)
    timestamp = Column(String, default=_utc_now)


class Preevaluacion(Base):
    __tablename__ = "cr_preevaluacion"

    id = Column(String, primary_key=True, default=_new_id)
    solicitud_id = Column(String, ForeignKey("cr_solicitud_credito.id"), nullable=False, index=True)
    asesor_id = Column(String, ForeignKey("cr_asesor.id"))
    cliente_id = Column(String, ForeignKey("cr_cliente.id"), nullable=False)
    ingreso_mensual = Column(Float, default=0)
    gasto_mensual = Column(Float, default=0)
    monto_solicitado = Column(Float, nullable=False)
    plazo = Column(Integer, nullable=False)
    cuota_estimada = Column(Float)
    antiguedad_negocio_meses = Column(Integer, default=0)
    score = Column(Integer, default=0)
    resultado = Column(String, nullable=False)
    puntaje = Column(Integer, nullable=False)
    ratio_cuota_ingreso = Column(Float)
    observaciones = Column(String)
    created_at = Column(String, default=_utc_now)

    solicitud = relationship("SolicitudCredito", back_populates="preevaluaciones")


class BuroConsulta(Base):
    __tablename__ = "cr_buro_consulta"

    id = Column(String, primary_key=True, default=_new_id)
    solicitud_id = Column(String, ForeignKey("cr_solicitud_credito.id"), index=True)
    asesor_id = Column(String, ForeignKey("cr_asesor.id"))
    cliente_id = Column(String, ForeignKey("cr_cliente.id"), nullable=False)
    dni = Column(String, nullable=False)
    calificacion = Column(String, nullable=False)
    entidades_con_deuda = Column(Integer, default=0)
    deuda_total = Column(Float, default=0)
    mayor_deuda = Column(Float, default=0)
    dias_mayor_mora = Column(Integer, default=0)
    en_lista_negra = Column(Integer, default=0)
    recomendacion = Column(String)
    motivo_bloqueo = Column(String)
    created_at = Column(String, default=_utc_now)

    solicitud = relationship("SolicitudCredito", back_populates="buro_consultas")


class NotaInterna(Base):
    __tablename__ = "cr_nota_interna"

    id = Column(String, primary_key=True, default=_new_id)
    solicitud_id = Column(String, ForeignKey("cr_solicitud_credito.id"), nullable=False)
    asesor_id = Column(String, ForeignKey("cr_asesor.id"))
    contenido = Column(String, nullable=False)
    created_at = Column(String, default=_utc_now)
