import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, MetaData
from sqlalchemy.orm import sessionmaker, declarative_base

# Cargar .env desde la raíz del proyecto
dotenv_path = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

def _resolve_db_url() -> str:
    env_url = os.getenv("DATABASE_URL")
    if not env_url:
        raise RuntimeError(
            "DATABASE_URL no configurada. "
            "Define DATABASE_URL en .env o como variable de entorno. "
            "Ej: postgresql+psycopg2://user:pass@host/db?sslmode=require"
        )
    url = env_url.strip()
    if url.startswith("postgresql://") and "+" not in url:
        url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url

SQLALCHEMY_DATABASE_URL = _resolve_db_url()

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=300,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}
Base = declarative_base(metadata=MetaData(naming_convention=convention))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create tables if they don't exist, add missing columns, and verify connection."""
    import logging
    logger = logging.getLogger("core_mobile")

    import app.models  # noqa: F401 — ensure models are importable
    Base.metadata.create_all(bind=engine)

    # Add missing columns that exist in the model but not in the actual table
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text(
                "ALTER TABLE cr_cuenta_ahorro ADD COLUMN IF NOT EXISTS cci VARCHAR"
            ))
            conn.commit()
            logger.info("Column 'cci' verified on cr_cuenta_ahorro")
    except Exception as e:
        logger.warning("Could not alter table cr_cuenta_ahorro: %s", e)

    try:
        engine.connect().close()
    except Exception as e:
        raise RuntimeError(f"Cannot connect to database: {e}")
