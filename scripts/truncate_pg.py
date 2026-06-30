import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("DATABASE_URL", "")

url = os.environ["DATABASE_URL"]
if not url:
    print("ERROR: DATABASE_URL no definida")
    sys.exit(1)
if url.startswith("postgresql://") and "+" not in url:
    url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

from sqlalchemy import create_engine, text

engine = create_engine(url)

with engine.connect() as conn:
    conn.execute(text("SET session_replication_role = 'replica';"))
    conn.execute(text(
        "TRUNCATE TABLE cr_cronograma_pago, cr_historial_credito, cr_nota_interna, "
        "cr_documento, cr_visita, cr_notificacion, cr_movimiento, cr_operacion, "
        "cr_cuenta_ahorro, cr_tarjeta, cr_accion_cobranza, cr_credito_preaprobado, "
        "dsolicitud, cr_cartera_diaria, cr_sync_outbox, cr_sync_log, "
        "cr_credito, cr_solicitud_credito, cr_usuario_cliente, "
        "cr_cliente, cr_asesor, dcliente, cr_actividad_economica, cr_garantia "
        "CASCADE"
    ))
    conn.execute(text("SET session_replication_role = 'origin';"))
    conn.commit()

print("Datos truncados en PostgreSQL. Ejecutando migracion desde SQLite...")
