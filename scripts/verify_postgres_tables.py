import os
from sqlalchemy import create_engine, text

url = os.environ["DATABASE_URL"]
if url.startswith("postgresql://") and "+" not in url:
    url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

engine = create_engine(url, echo=False)
PYTHONIOENCODING = "utf-8"

with engine.connect() as conn:
    result = conn.execute(
        text(
            "SELECT table_name FROM information_schema.tables "
            "WHERE table_schema = 'public' ORDER BY table_name"
        )
    )
    tables = [row[0] for row in result]
    print(f"=== TABLAS ENCONTRADAS: {len(tables)} ===")
    for t in tables:
        print(f"  [OK] {t}")

    print()
    print("=== COLUMNAS POR TABLA ===")
    for t in tables:
        col_result = conn.execute(
            text(
                "SELECT column_name, data_type, is_nullable "
                "FROM information_schema.columns "
                "WHERE table_schema='public' AND table_name=:t "
                "ORDER BY ordinal_position"
            ),
            {"t": t},
        )
        cols = col_result.all()
        print(f"\n--- {t} ({len(cols)} columnas) ---")
        for c in cols:
            print(f"  {c[0]:30s} {c[1]:20s} nullable={c[2]}")

    print()
    print("=== CONSTRAINTS (FK) ===")
    fk_result = conn.execute(
        text(
            "SELECT tc.table_name, kcu.column_name, "
            "ccu.table_name AS foreign_table_name, ccu.column_name AS foreign_column_name "
            "FROM information_schema.table_constraints AS tc "
            "JOIN information_schema.key_column_usage AS kcu "
            "ON tc.constraint_name = kcu.constraint_name "
            "AND tc.table_schema = kcu.table_schema "
            "JOIN information_schema.constraint_column_usage AS ccu "
            "ON ccu.constraint_name = tc.constraint_name "
            "AND ccu.table_schema = tc.table_schema "
            "WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema='public' "
            "ORDER BY tc.table_name, kcu.column_name"
        )
    )
    fks = fk_result.all()
    print(f"\nTotal FK constraints: {len(fks)}")
    for fk in fks:
        print(f"  {fk[0]:25s}.{fk[1]:20s} -> {fk[2]:25s}.{fk[3]:20s}")

print("\n=== VERIFICACION COMPLETA ===")
