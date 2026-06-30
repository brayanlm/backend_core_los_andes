import sqlite3
conn = sqlite3.connect("bd_core_mobile.db")
cur = conn.execute("PRAGMA table_list")
tables = cur.fetchall()
print("Tables:", tables)

for t in tables:
    name = t[1]
    if name.startswith("sqlite"): continue
    cur = conn.execute(f"PRAGMA table_info({name})")
    cols = [r[1] for r in cur.fetchall()]
    print(f"\n--- {name} --- cols: {cols}")
    cur = conn.execute(f"SELECT * FROM {name}")
    rows = cur.fetchall()
    for r in rows[:5]:
        print(" ", {cols[i]: r[i] for i in range(min(len(cols), 10))})
conn.close()
