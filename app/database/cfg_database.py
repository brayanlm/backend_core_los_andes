"""BD config — usa SQLAlchemy/PostgreSQL. Firestore eliminado."""


def init_db():
    from app.database.session import init_db as _init
    _init()
