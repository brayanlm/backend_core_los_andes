import sqlite3
conn = sqlite3.connect("bd_core_mobile.db")
cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print("Tables:", tables)

for t in tables:
    cur = conn.execute(f"SELECT * FROM {t} LIMIT 3")
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    print(f"\n--- {t} ---")
    print("Columns:", cols)
    for r in rows:
        print(" ", r[:min(len(r), 6)])
conn.close()
