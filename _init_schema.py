import os

# Remove old real DB and recreate with SQLAlchemy
db_path = os.path.join(os.path.dirname(__file__), 'data', 'bd_core_mobile.db')
if os.path.exists(db_path):
    os.remove(db_path)
    print('Removed old DB')

from app.database.session import init_db, engine
from sqlalchemy import inspect

init_db()
print('Schema created successfully')

inspector = inspect(engine)
tables = inspector.get_table_names()
print(f'Tables ({len(tables)}):')
for t in sorted(tables):
    cols = [c['name'] for c in inspector.get_columns(t)]
    print(f'  {t}: {len(cols)} cols')

# Check stale file at root
root_path = os.path.join(os.path.dirname(__file__), 'bd_core_mobile.db')
if os.path.exists(root_path):
    os.remove(root_path)
    print(f'\nRemoved stale root DB: {root_path}')
