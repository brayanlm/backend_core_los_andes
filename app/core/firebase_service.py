import json
import os
import firebase_admin
from firebase_admin import credentials, firestore

_initialized = False
_init_failed = False
db = None

def init_firebase():
    global _initialized, _init_failed, db
    if _initialized:
        return db
    if _init_failed:
        return None
    try:
        sa_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            "service-account.json",
        )
        if not os.path.exists(sa_path):
            alt = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "service-account.json",
            )
            if os.path.exists(alt):
                sa_path = alt
            else:
                raise FileNotFoundError(
                    f"service-account.json no encontrado en {sa_path} ni {alt}"
                )
        cred = credentials.Certificate(sa_path)
        firebase_admin.initialize_app(cred)
        db = firestore.client()
        _initialized = True
    except Exception:
        _init_failed = True
        raise
    return db


def get_firestore():
    if _init_failed:
        return None
    if db is None:
        return init_firebase()
    return db
