import sqlite3, os

# Check the REAL database used by the server
db_path = os.path.join(os.path.dirname(__file__), 'data', 'bd_core_mobile.db')
print(f'=== {db_path} ===')
print(f'Size: {os.path.getsize(db_path)} bytes')
conn = sqlite3.connect(db_path)
tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
print(f'Tables ({len(tables)}):')
for t in tables:
    count = conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
    cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{t}")').fetchall()]
    print(f'  {t}: {count} rows, cols={len(cols)}')
    if count > 0:
        sample = conn.execute(f'SELECT * FROM "{t}" LIMIT 2').fetchall()
        for row in sample:
            d = dict(row)
            print(f'    - { {k:str(v)[:40] for k,v in d.items()} }')
conn.close()
