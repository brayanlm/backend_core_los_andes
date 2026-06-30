import logging
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.core.cfg_config import settings
from app.database.cfg_database import init_db
from app.routes import (
    rtr_auth, rtr_cartera, rtr_ficha, rtr_cobranza, rtr_preeval, rtr_buro,
    rtr_solicitudes, rtr_reportes, rtr_alertas, rtr_campanas, rtr_sync,
    rtr_cliente, rtr_creditos, rtr_sync_db, rtr_evaluacion,
)

logger = logging.getLogger("core_mobile")

def _parse_cors_origins(raw: str) -> list[str]:
    return [o.strip() for o in raw.split(",") if o.strip()]


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    from app.database.session import SessionLocal
    from app.models.mdl_all import Cliente
    session = SessionLocal()
    try:
        already_has_data = session.query(Cliente).first() is not None
    finally:
        session.close()
    if not already_has_data:
        from app.core.seed import seed_admin, seed_asesor, seed_asesor_fv, seed_clientes_demo
        seed_admin()
        seed_asesor()
        seed_asesor_fv()
        seed_clientes_demo()
    from app.core.seed import seed_cliente_prueba
    seed_cliente_prueba()
    yield


app = FastAPI(
    title="Core Mobile — Banco de los Andes",
    description="API unificada de créditos PYME. SQLAlchemy + PostgreSQL (Neon).",
    version="2.0.0",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Excepción no manejada en %s %s: %s", request.method, request.url.path, exc)
    detail = "Error interno del servidor"
    if settings.ENV == "development":
        detail = str(exc)
    return JSONResponse(
        status_code=500,
        content={"detail": detail},
    )


cors_origins = _parse_cors_origins(settings.CORS_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    elapsed = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s → %s (%.0fms)",
        request.method, request.url.path, response.status_code, elapsed,
    )
    return response

app.include_router(rtr_auth.router,    prefix="/auth",     tags=["Auth"])
app.include_router(rtr_cartera.router, prefix="/cartera",  tags=["Cartera"])
app.include_router(rtr_ficha.router,   prefix="/clientes", tags=["Ficha"])
app.include_router(rtr_cobranza.router, prefix="/cobranza", tags=["Cobranza"])
app.include_router(rtr_preeval.router,    prefix="/pre-evaluar", tags=["PreEvaluacion"])
app.include_router(rtr_evaluacion.router, prefix="/evaluacion",  tags=["Evaluacion"])
app.include_router(rtr_buro.router,       prefix="/buro",        tags=["Buro"])
app.include_router(rtr_solicitudes.router, prefix="/solicitudes", tags=["Solicitudes"])
app.include_router(rtr_reportes.router, prefix="/reportes", tags=["Reportes"])
app.include_router(rtr_alertas.router, prefix="/alertas", tags=["Alertas"])
app.include_router(rtr_campanas.router, prefix="/campanas", tags=["Campanas"])
app.include_router(rtr_sync.router, prefix="/sync", tags=["Sync"])
app.include_router(rtr_sync_db.router, prefix="/sync-db", tags=["Sync DB"])

app.include_router(rtr_cliente.router, prefix="/cliente", tags=["Cliente (App)"])
app.include_router(rtr_creditos.router, prefix="/creditos", tags=["Creditos"])


@app.get("/")
def root():
    return {"sistema": "Core Mobile Banco de los Andes", "version": "2.0.0", "status": "ok"}


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
