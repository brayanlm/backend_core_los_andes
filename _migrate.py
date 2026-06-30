import sqlite3
conn = sqlite3.connect("app/database/los_andes.db")
c = conn.cursor()
try:
    c.execute("ALTER TABLE cr_asesor ADD COLUMN password_hash TEXT")
except sqlite3.OperationalError:
    print("Column already exists")
conn.commit()

from app.core.cfg_security import hash_password
from app.database.session import SessionLocal
from app.models.mdl_all import Asesor

db = SessionLocal()
creds = {
    "admin@losandes.com": "admin123",
}
for a in db.query(Asesor).all():
    pwd = creds.get(a.email, f"{a.codigo_empleado}123")
    a.password_hash = hash_password(pwd)
    print(f"Set password_hash for {a.email or a.codigo_empleado}")
db.commit()
db.close()
conn.close()
print("Done")
