from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator


# ─── Solicitud ───

class SolicitudCreate(BaseModel):
    cliente_id: str = ""
    numero_documento: str = ""
    nombres: str = ""
    apellidos: str = ""
    telefono: str = ""
    tipo_negocio: str = ""
    nombre_negocio: str = ""
    ingresos_estimados: float = 0
    monto_solicitado: float
    plazo_meses: int
    destino_credito: str = ""
    garantia: str = "sin_garantia"
    tea_referencial: float = 0.25
    canal: str = "asesor"

    @field_validator("monto_solicitado")
    @classmethod
    def monto_positivo(cls, v):
        if v <= 0:
            raise ValueError("El monto debe ser positivo")
        return v

    @field_validator("plazo_meses")
    @classmethod
    def plazo_valido(cls, v):
        if v < 1 or v > 120:
            raise ValueError("El plazo debe estar entre 1 y 120 meses")
        return v

    @field_validator("ingresos_estimados")
    @classmethod
    def ingresos_no_negativos(cls, v):
        if v < 0:
            raise ValueError("Los ingresos no pueden ser negativos")
        return v


class SolicitudOut(BaseModel):
    id: str
    numero_expediente: str
    cliente_id: str
    cliente_nombre: str = ""
    asesor_id: Optional[str] = None
    canal: str
    monto: float
    plazo: int
    cuota_estimada: Optional[float] = None
    ingresos: Optional[float] = None
    estado: str
    destino_credito: Optional[str] = None
    garantia: Optional[str] = None
    motivo_rechazo: Optional[str] = None
    condiciones: Optional[str] = None
    credito_id: Optional[str] = None
    visita_registrada: int = 0
    preevaluacion_realizada: int = 0
    buro_consultado: int = 0
    documentos_completos: int = 0
    firma_capturada: int = 0
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


class SolicitudPendienteOut(BaseModel):
    id: str
    cliente_id: str
    cliente_nombre: str
    monto: float
    plazo: int
    ingresos: Optional[float] = None
    destino: Optional[str] = None
    cuota_estimada: Optional[float] = None
    estado: str
    created_at: Optional[str] = None
    score_usado: Optional[int] = None
    ratio: Optional[float] = None


# ─── Documentos ───

class DocumentoIn(BaseModel):
    tipo: str
    nombre_archivo: str = ""
    contenido_base64: str = ""


class DocumentoOut(BaseModel):
    id: str
    solicitud_id: str
    tipo: str
    nombre_archivo: str
    created_at: str


# ─── Visita ───

class VisitaIn(BaseModel):
    lat: Optional[float] = None
    lng: Optional[float] = None
    observacion: str = ""
    resultado: str = "visitado"


class VisitaOut(BaseModel):
    id: str
    solicitud_id: Optional[str] = None
    asesor_id: str
    cliente_id: str
    lat: Optional[float] = None
    lng: Optional[float] = None
    observacion: Optional[str] = None
    resultado: Optional[str] = None
    created_at: Optional[str] = None


# ─── Asignar ───

class AsignarIn(BaseModel):
    asesor_id: str


class AsignarGenerarIn(BaseModel):
    codigo_empleado: str


# ─── Comité ───

class ComiteIn(BaseModel):
    comentario: str = ""


# ─── Evaluar ───

class EvaluarIn(BaseModel):
    score: Optional[int] = None
    comentario: str = ""


# ─── Aprobar ───

class AprobarIn(BaseModel):
    monto_aprobado: Optional[float] = None
    tasa_final: Optional[float] = None
    comentario: str = ""


# ─── Condicionar ───

class CondicionarIn(BaseModel):
    condiciones: str
    monto_aprobado: Optional[float] = None
    tasa_final: Optional[float] = None


# ─── Rechazar ───

class RechazarIn(BaseModel):
    motivo: str


# ─── Crédito ───

class CreditoOut(BaseModel):
    id: str
    solicitud_id: Optional[str] = None
    cliente_id: str
    cliente_nombre: str = ""
    asesor_id: Optional[str] = None
    asesor_nombre: str = ""
    monto: float
    monto_desembolsado: Optional[float] = None
    plazo_meses: int
    tasa: Optional[float] = None
    cuota_estimada: Optional[float] = None
    estado: str
    destino: Optional[str] = None
    fecha_creacion: Optional[str] = None
    fecha_aprobacion: Optional[str] = None
    fecha_desembolso: Optional[str] = None

    model_config = {"from_attributes": True}


class CronogramaCuotaOut(BaseModel):
    nro_cuota: int
    fecha_vencimiento: Optional[str] = None
    monto_cuota: float
    monto_capital: float
    monto_interes: float
    saldo: float
    estado_cuota: str


class DesembolsarIn(BaseModel):
    cuenta_destino: str = ""


class DesembolsarOut(BaseModel):
    id: str
    estado: str
    monto_desembolsado: float
    total_cuotas: int
    mensaje: str


# ─── Pre-evaluación ───

class PreevaluacionIn(BaseModel):
    solicitud_id: str


class PreevaluacionOut(BaseModel):
    id: str
    solicitud_id: str
    asesor_id: Optional[str] = None
    cliente_id: str
    ingreso_mensual: float = 0
    gasto_mensual: float = 0
    monto_solicitado: float
    plazo: int
    cuota_estimada: Optional[float] = None
    antiguedad_negocio_meses: int = 0
    score: int = 0
    resultado: str
    puntaje: int
    ratio_cuota_ingreso: Optional[float] = None
    observaciones: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}


# ─── Buró ───

class BuroConsultaIn(BaseModel):
    dni: str
    solicitud_id: Optional[str] = None
    cliente_id: Optional[str] = None


class BuroConsultaOut(BaseModel):
    id: str
    solicitud_id: Optional[str] = None
    asesor_id: Optional[str] = None
    cliente_id: str
    dni: str
    calificacion: str
    entidades_con_deuda: int = 0
    deuda_total: float = 0
    mayor_deuda: float = 0
    dias_mayor_mora: int = 0
    en_lista_negra: bool = False
    recomendacion: Optional[str] = None
    motivo_bloqueo: Optional[str] = None
    created_at: Optional[str] = None

    model_config = {"from_attributes": True}
