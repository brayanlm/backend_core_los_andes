import sys, bcrypt
sys.path.insert(0, ".")

import sqlite3
db_path = "app/database/los_andes.db"
conn = sqlite3.connect(db_path)
c = conn.cursor()

cols = [row[1] for row in c.execute("PRAGMA table_info(cr_asesor)").fetchall()]
if "password_hash" not in cols:
    c.execute("ALTER TABLE cr_asesor ADD COLUMN password_hash TEXT")
    print("Added password_hash column")

rows = c.execute("SELECT id, codigo_empleado, email FROM cr_asesor").fetchall()
for rid, cod, email in rows:
    if email == "admin@losandes.com":
        pwd = "admin123"
    else:
        pwd = f"{cod}123"
    ph = bcrypt.hashpw(pwd.encode(), bcrypt.gensalt()).decode()
    c.execute("UPDATE cr_asesor SET password_hash=? WHERE id=?", (ph, rid))
    print(f"Set pwd for {email or cod}")

conn.commit()
conn.close()
print("Done!")
