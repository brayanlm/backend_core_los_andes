"""
Migracion de datos desde SQLite a PostgreSQL (SQLAlchemy 2.0 compatible).
Maneja FK circular entre cr_solicitud_credito <-> cr_credito.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy import create_engine, MetaData, text
from app.database.session import SQLALCHEMY_DATABASE_URL as PG_URL
from app.database.connection import DB_PATH

SQLITE_URL = f"sqlite:///{DB_PATH}"

CIRCULAR_TABLAS = ["cr_solicitud_credito", "cr_credito"]
CIRCULAR_FK = {
    "cr_credito": "solicitud_id",
    "cr_solicitud_credito": "credito_id",
}
TABLAS = [
    "cr_cliente", "cr_usuario_cliente", "cr_asesor",
    # cr_solicitud_credito comes after cr_credito (circular handled)
    "cr_credito", "cr_solicitud_credito",
    "cr_cronograma_pago", "cr_movimiento", "cr_documento",
    "cr_visita", "cr_cartera_diaria", "cr_sync_outbox", "cr_sync_log",
    "cr_cuenta_ahorro", "cr_tarjeta", "cr_notificacion", "cr_operacion",
    "cr_accion_cobranza", "cr_credito_preaprobado", "cr_historial_credito",
    "cr_nota_interna", "dcliente", "dsolicitud", "cr_actividad_economica",
    "cr_garantia",
]

def migrate():
    if not PG_URL or PG_URL.startswith("sqlite"):
        print("ERROR: DATABASE_URL debe apuntar a PostgreSQL (Neon)")
        print(f"  Actual: {PG_URL}")
        sys.exit(1)

    sqlite_engine = create_engine(SQLITE_URL, connect_args={"check_same_thread": False})
    pg_engine = create_engine(PG_URL)

    sqlite_meta = MetaData()
    sqlite_meta.reflect(bind=sqlite_engine)
    pg_meta = MetaData()
    pg_meta.reflect(bind=pg_engine)

    # Store circular FK data for post-processing
    circular_data = {}

    total = 0
    for tabla in TABLAS:
        if tabla not in sqlite_meta.tables:
            print(f"[SKIP] {tabla} -- no existe en SQLite")
            continue
        if tabla not in pg_meta.tables:
            print(f"[SKIP] {tabla} -- no existe en PostgreSQL")
            continue

        sqlite_table = sqlite_meta.tables[tabla]
        pg_table = pg_meta.tables[tabla]
        column_names = [c.name for c in pg_table.columns]

        with sqlite_engine.connect() as sqlite_conn:
            rows = sqlite_conn.execute(text(f"SELECT * FROM {tabla}")).mappings().all()

        if not rows:
            print(f"[VACIO] {tabla}")
            continue

        # For circular FK tables, strip the circular FK column during INSERT
        strip_col = CIRCULAR_FK.get(tabla)
        if strip_col:
            circular_data[tabla] = []
            for row in rows:
                data = {k: row[k] for k in column_names if k in row}
                circ_val = data.pop(strip_col, None)
                circular_data[tabla].append((data, circ_val))
            rows_to_insert = [d for d, _ in circular_data[tabla]]
        else:
            rows_to_insert = [{k: row[k] for k in column_names if k in row} for row in rows]

        insertados = 0
        with pg_engine.connect() as pg_conn:
            for data in rows_to_insert:
                try:
                    pg_conn.execute(pg_table.insert().values(**data))
                    insertados += 1
                except Exception as e:
                    pg_conn.rollback()
                    print(f"  [ERROR] {tabla}: fila {insertados+1}: {e}")
                    break
            else:
                pg_conn.commit()
                total += insertados
                print(f"[OK] {tabla}: {insertados} registros migrados")

    # Post-process circular FK: cr_credito.solicitud_id and cr_solicitud_credito.credito_id
    print("\n[POST] Restaurando FK circular...")
    with pg_engine.connect() as pg_conn:
        # First, set cr_credito.solicitud_id from stored data
        if "cr_credito" in circular_data:
            ok = 0
            for data, circ_val in circular_data["cr_credito"]:
                if circ_val is not None:
                    pg_conn.execute(
                        text("UPDATE cr_credito SET solicitud_id = :val WHERE id = :id"),
                        {"val": circ_val, "id": data["id"]}
                    )
                    ok += 1
            pg_conn.commit()
            print(f"  cr_credito.solicitud_id: {ok} actualizados")

        # Then, set cr_solicitud_credito.credito_id
        if "cr_solicitud_credito" in circular_data:
            ok = 0
            for data, circ_val in circular_data["cr_solicitud_credito"]:
                if circ_val is not None:
                    pg_conn.execute(
                        text("UPDATE cr_solicitud_credito SET credito_id = :val WHERE id = :id"),
                        {"val": circ_val, "id": data["id"]}
                    )
                    ok += 1
            pg_conn.commit()
            print(f"  cr_solicitud_credito.credito_id: {ok} actualizados")

    print(f"\nMigracion completada. {total} registros migrados a PostgreSQL.")

if __name__ == "__main__":
    migrate()
