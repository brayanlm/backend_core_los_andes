import uuid
from sqlalchemy import Column, String, Integer, Numeric, Date, DateTime, ForeignKey
from app.core.cfg_database import Base

class CarteraDiaria(Base):
    __tablename__ = "cartera_diaria"

    id                 = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    asesor_id          = Column(String(36), ForeignKey("asesores.id"), nullable=False)
    cliente_id         = Column(String(36), ForeignKey("clientes.id"), nullable=False)
    agencia_id         = Column(String(36), ForeignKey("agencias.id"))
    fecha_asignacion   = Column(Date, nullable=False)
    tipo_gestion       = Column(String(30), nullable=False)
    prioridad          = Column(String(10), default="normal")
    score_prioridad    = Column(Integer, default=0)
    monto_credito      = Column(Numeric(12, 2))
    estado_visita      = Column(String(20), default="pendiente")
    resultado_visita   = Column(String(30))
    observacion_visita = Column(String)
    timestamp_visita   = Column(DateTime(timezone=True))
    lat_visita         = Column(Numeric(10, 7))
    lng_visita         = Column(Numeric(10, 7))
    orden_manual       = Column(Integer)
