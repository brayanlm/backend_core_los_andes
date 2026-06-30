from pydantic import BaseModel
from typing import Optional

class LoginClienteIn(BaseModel):
    numero_documento: str
    password: str

class ClienteOut(BaseModel):
    id: str
    numero_documento: str
    nombres: str
    apellidos: str
    email: str | None = None
    telefono: str | None = None

class TokenClienteOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    cliente: ClienteOut | None = None

class CuentaAhorroOut(BaseModel):
    id: str
    cod_cuenta_ahorro: str | None = None
    cci: str | None = None
    tipo_cuenta: str | None = None
    moneda: str | None = None
    saldo_capital: float | None = None
    saldo_interes: float | None = None
    tea: float | None = None
    estado: str | None = None

class CreditoOut(BaseModel):
    id: str
    cod_cuenta_credito: str | None = None
    producto: str | None = None
    monto_desembolsado: float | None = None
    saldo_capital: float | None = None
    saldo_total: float | None = None
    dias_mora: int = 0
    calificacion_interna: str | None = None
    estado: str | None = None
    fecha_desembolso: str | None = None
    tea: float | None = None
    cuotas_total: int | None = None
    cuotas_pagadas: int | None = None

class CuotaOut(BaseModel):
    id: str
    nro_cuota: int
    fecha_vencimiento: str
    monto_cuota: float | None = None
    monto_capital: float | None = None
    monto_interes: float | None = None
    saldo: float | None = None
    estado_cuota: str | None = None
    fecha_pago: str | None = None

class MovimientoOut(BaseModel):
    id: str
    cod_operacion: str | None = None
    cod_cuenta: str | None = None
    tipo: str | None = None
    concepto: str | None = None
    canal: str | None = None
    monto: float
    moneda: str | None = None
    fecha_operacion: str | None = None

class TarjetaOut(BaseModel):
    id: str
    numero_enmascarado: str | None = None
    marca: str | None = None
    linea_credito: float | None = None
    saldo_utilizado: float | None = None
    fecha_corte: str | None = None
    fecha_pago: str | None = None
    estado: str | None = None

class NotificacionOut(BaseModel):
    id: str
    titulo: str
    cuerpo: str | None = None
    tipo: str | None = None
    leida: bool = False
    created_at: str | None = None

class RegisterClienteIn(BaseModel):
    numero_documento: str
    password: str
    nombres: str
    apellidos: str
    email: str | None = None
    telefono: str | None = None
    direccion: str | None = None

class SolicitudClienteIn(BaseModel):
    monto_solicitado: float
    plazo: int = 12
    tea: float = 0.25
    destino: str
    ingresos_declarados: float | None = None
    ruc: str | None = None
    nombre_negocio: str | None = None
    rubro_negocio: str | None = None
    antiguedad_negocio_meses: int | None = None
    tipo_negocio: str | None = None
    garantia: str | None = None
    gastos_mensuales: float = 0
    tipo_cuota: str = "mensual"
    tiene_recibo_servicio: bool = False
    tiene_declaracion_igv: bool = False
    tiene_pdt: bool = False

class OperacionIn(BaseModel):
    cod_cuenta_origen: str
    cod_cuenta_destino: str | None = None
    tipo: str
    monto: float
    moneda: str = "PEN"

class OperacionOut(BaseModel):
    id: str
    cod_cuenta_origen: str | None = None
    cod_cuenta_destino: str | None = None
    tipo: str | None = None
    monto: float
    moneda: str | None = None
    estado: str

# ── Nuevos schemas para la mejora ──

class DestinatarioOut(BaseModel):
    cliente_id: str
    nombres: str
    apellidos: str
    numero_documento: str
    telefono: str | None = None
    cod_cuenta: str | None = None
    cci: str | None = None

class TransferirIn(BaseModel):
    cuenta_origen_id: str
    cuenta_destino_cod: str
    monto: float
    descripcion: str = ""
    destinatario_nombre: str = ""
    destinatario_cliente_id: str = ""

class YapeIn(BaseModel):
    cuenta_origen_id: str
    telefono_destino: str
    monto: float
    descripcion: str = ""

class PagoCuotaIn(BaseModel):
    cuenta_origen_id: str
    credito_id: str
    cuota_id: str

class RecargaIn(BaseModel):
    cuenta_origen_id: str
    operador: str
    telefono: str
    monto: float

class ServicioPagoIn(BaseModel):
    cuenta_origen_id: str
    servicio: str
    codigo_servicio: str
    monto: float

class ComprobanteOut(BaseModel):
    id: str
    tipo: str
    monto: float
    moneda: str = "PEN"
    estado: str
    codigo_operacion: str | None = None
    cuenta_origen: str | None = None
    cuenta_destino: str | None = None
    descripcion: str | None = None
    comision: float = 0.0
    created_at: str | None = None
    cliente_nombre: str | None = None
    cliente_documento: str | None = None
