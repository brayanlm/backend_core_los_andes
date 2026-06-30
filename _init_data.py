"""Create initial data directly without SQLAlchemy."""
import sqlite3, bcrypt, uuid

db_path = "app/database/los_andes.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

def hash_pw(pwd):
    return bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()

now = "2026-06-23T21:00:00+00:00"

users = [
    ("9fd93b3f-11fc-424e-86fd-669df7e84239", "000", "admin@losandes.com", "Administrador", "Los Andes", "administrador", "ADMIN", "AG-001", 1, hash_pw("admin123"), 0, None, now),
    ("e8fd8dab-754e-4333-a03b-20e329a23fbb", "001", "juan@losandes.com", "Juan", "Perez", "supervisor", "ADMIN", "AG-001", 1, hash_pw("asesor123"), 0, None, now),
    ("3140b7fc-b4f1-4f2b-ae6c-f6b43d5d76d3", "0001", "carlos@losandes.com", "Carlos", "Ventas", "operador", "ASESOR", "AG-001", 1, hash_pw("0001123"), 0, None, now),
    (str(uuid.uuid4()), "75223330", None, "Brayan Jose", "Ochoa Segovia", "operador", "ASESOR", "AG-001", 1, hash_pw("75223330"), 0, None, now),
]

c.executemany(
    "INSERT OR IGNORE INTO cr_asesor VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
    users
)
conn.commit()
print(f"Inserted {len(users)} users")

# Verify
for row in c.execute("SELECT email, codigo_empleado FROM cr_asesor").fetchall():
    ok = bcrypt.checkpw(b"admin123" if row[0] == "admin@losandes.com" else f"{row[1]}123".encode(), c.execute("SELECT password_hash FROM cr_asesor WHERE email=? OR codigo_empleado=?", (row[0], row[1])).fetchone()[0].encode())
    print(f"  {row[0] or row[1]}: verify={'OK' if ok else 'FAIL'}")

conn.close()
print("Done!")
