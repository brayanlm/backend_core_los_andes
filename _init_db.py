"""Create initial DB with essential data, without Firestore."""
import sys, bcrypt
sys.path.insert(0, ".")

from app.database.session import SessionLocal, engine, Base
from app.models.mdl_all import Asesor, Cliente, CarteraDiaria
from datetime import datetime, timezone

# Create all tables
Base.metadata.create_all(bind=engine)
print("Tables created")

db = SessionLocal()

def hash_pw(pwd):
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

# Admin
admin = Asesor(
    id="9fd93b3f-11fc-424e-86fd-669df7e84239",
    codigo_empleado="000",
    email="admin@losandes.com",
    nombres="Administrador",
    apellidos="Los Andes",
    perfil="administrador",
    rol="ADMIN",
    agencia_id="AG-001",
    activo=1,
    password_hash=hash_pw("admin123"),
    created_at=datetime.now(timezone.utc).isoformat(),
)
db.add(admin)

# Asesor 001 - Juan Perez
asesor1 = Asesor(
    id="e8fd8dab-754e-4333-a03b-20e329a23fbb",
    codigo_empleado="001",
    email="juan@losandes.com",
    nombres="Juan",
    apellidos="Perez",
    perfil="supervisor",
    rol="ADMIN",
    agencia_id="AG-001",
    activo=1,
    password_hash=hash_pw("asesor123"),
    created_at=datetime.now(timezone.utc).isoformat(),
)
db.add(asesor1)

# Asesor 0001 - Carlos Ventas
asesor2 = Asesor(
    id="3140b7fc-b4f1-4f2b-ae6c-f6b43d5d76d3",
    codigo_empleado="0001",
    email="carlos@losandes.com",
    nombres="Carlos",
    apellidos="Ventas",
    perfil="operador",
    rol="ASESOR",
    agencia_id="AG-001",
    activo=1,
    password_hash=hash_pw("0001123"),
    created_at=datetime.now(timezone.utc).isoformat(),
)
db.add(asesor2)

db.commit()
print("Users created")

# Verify
from app.core.cfg_security import verify_password
for a in db.query(Asesor).all():
    ok = "OK" if verify_password("admin123" if "admin" in (a.email or "") else f"{a.codigo_empleado}123", a.password_hash) else "FAIL"
    print(f"  {a.email or a.codigo_empleado}: {a.nombres} {a.apellidos} - pwd verify: {ok}")

db.close()
print("Done!")
