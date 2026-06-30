import os, sys, uuid
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
url = os.environ["DATABASE_URL"]
if url.startswith("postgresql://") and "+" not in url:
    url = url.replace("postgresql://", "postgresql+psycopg2://", 1)

from sqlalchemy import create_engine, text
engine = create_engine(url, echo=False)

from app.core.cfg_security import hash_password

asesores = [
    {"codigo": "000",  "nombres": "Administrador", "apellidos": "Los Andes",   "email": "admin@losandes.com",  "password": "admin123",  "perfil": "administrador"},
    {"codigo": "001",  "nombres": "Juan",          "apellidos": "Perez",       "email": "asesor@losandes.com", "password": "asesor123",  "perfil": "operador"},
    {"codigo": "0001", "nombres": "Carlos",        "apellidos": "Ventas",      "email": "fv@losandes.com",     "password": "0001123",   "perfil": "operador"},
    {"codigo": "75223330", "nombres": "Brayan",    "apellidos": "Quispe",      "email": "brayan@losandes.com", "password": "75223330",  "perfil": "operador"},
]

with engine.connect() as conn:
    for a in asesores:
        existing = conn.execute(
            text("SELECT id FROM cr_asesor WHERE codigo_empleado = :cod"),
            {"cod": a["codigo"]}
        ).first()
        if existing:
            print(f"[SKIP] {a['codigo']} ya existe")
            continue
        aid = str(uuid.uuid4())
        pw_hash = hash_password(a["password"])
        conn.execute(
            text("""
                INSERT INTO cr_asesor (id, codigo_empleado, email, nombres, apellidos, perfil, rol, agencia_id, activo, password_hash, created_at)
                VALUES (:id, :cod, :email, :nombres, :apellidos, :perfil, :rol, :agencia, :activo, :pwhash, :now)
            """),
            {
                "id": aid, "cod": a["codigo"], "email": a["email"],
                "nombres": a["nombres"], "apellidos": a["apellidos"],
                "perfil": a["perfil"], "rol": "ASESOR", "agencia": "AG-001",
                "activo": 1, "pwhash": pw_hash, "now": "2026-01-01T00:00:00Z"
            }
        )
        print(f"[OK] Creado {a['codigo']} / {a['password']}")
    conn.commit()

print("\nSeed completado.")
