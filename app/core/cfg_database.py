"""
Database dependency — todas las rutas nuevas deben usar
app.database.session.get_db() para SQLAlchemy/PostgreSQL.

Este módulo se mantiene solo para compatibilidad con imports legacy.
"""
from app.database.session import get_db, init_db, Base  # noqa: F401
