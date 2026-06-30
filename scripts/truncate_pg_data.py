import os
url = os.environ["DATABASE_URL"]
if url.startswith("postgresql://") and "+" not in url:
    url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
from sqlalchemy import create_engine, text
engine = create_engine(url)

with engine.connect() as conn:
    trans = conn.begin()
    # Break circular FK first
    conn.execute(text("UPDATE cr_credito SET solicitud_id = NULL WHERE solicitud_id IS NOT NULL"))
    tables = [
        "cr_cronograma_pago", "cr_historial_credito", "cr_nota_interna", "cr_documento",
        "cr_visita", "cr_notificacion", "cr_movimiento", "cr_operacion", "cr_cuenta_ahorro",
        "cr_tarjeta", "cr_accion_cobranza", "cr_credito_preaprobado", "dsolicitud",
        "cr_cartera_diaria", "cr_sync_outbox", "cr_sync_log",
        "cr_credito", "cr_solicitud_credito", "cr_usuario_cliente",
        "cr_cliente", "cr_asesor", "dcliente", "cr_actividad_economica", "cr_garantia"
    ]
    for t in tables:
        conn.execute(text(f"DELETE FROM {t}"))
    trans.commit()
    print(f"Datos truncados de {len(tables)} tablas")
