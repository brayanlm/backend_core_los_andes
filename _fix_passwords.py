import bcrypt
import sqlite3

conn = sqlite3.connect(r'D:\DAM\app_banco_los_andes\backend_core_los_andes\data\bd_core_mobile.db')
conn.row_factory = sqlite3.Row

# Generate proper bcrypt hash for password "12345678"
pwd_hash = bcrypt.hashpw(b'12345678', bcrypt.gensalt()).decode()

# Update all client users
users = conn.execute('SELECT id, username FROM cr_usuario_cliente').fetchall()
print(f"Updating {len(users)} users...")
for u in users:
    conn.execute('UPDATE cr_usuario_cliente SET password_hash = ? WHERE id = ?', (pwd_hash, u['id']))
    print(f"  {u['username']} -> password_hash updated")

conn.commit()
conn.close()
print("Done! All passwords set to '12345678'")
