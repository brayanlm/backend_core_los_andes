"""Legacy connection module — kept for import compatibility.

Runtime uses app.database.session for all PostgreSQL connections.
"""

from app.database.session import engine


def get_raw_connection():
    """Retorna una conexión cruda desde el engine de SQLAlchemy (PostgreSQL)."""
    return engine.connect()
