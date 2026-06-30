# Core Mobile — Banco de los Andes (FastAPI)

Backend unificado para la Banca Móvil, Fuerza de Ventas y Portal del Personal.

- DB: PostgreSQL (Neon) · Puerto API: **8010**
- Stack: FastAPI · SQLAlchemy 2 · JWT (python-jose) · bcrypt (passlib) · Alembic

## Puesta en marcha (desarrollo local)

```powershell
# 1) Entorno virtual
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# 2) Variables de entorno
copy .env.example .env
# Editar .env: DATABASE_URL, SECRET_KEY

# 3) Migraciones
python -m alembic upgrade head

# 4) Levantar el API
uvicorn main:app --reload --host 0.0.0.0 --port 8010
```

Docs interactivas: http://localhost:8010/docs

## Publicar en Render

1. Conectar repositorio a Render.
2. Servicio **Web Service** con:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python -m alembic upgrade head && uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Health Check Path:** `/health`
3. Configurar variables de entorno (ver `render.yaml`).
4. `DATABASE_URL` y `SECRET_KEY` se marcan como **Sync: false** (se ingresan manualmente).

## Variables de entorno (producción)

| Variable | Descripción |
|----------|-------------|
| `DATABASE_URL` | Connection string PostgreSQL (Neon) |
| `SECRET_KEY` | Clave JWT (generar con `secrets.token_urlsafe(32)`) |
| `CORS_ORIGINS` | Orígenes permitidos separados por coma |
| `ENV` | `production` (oculta errores internos) |
| `ALGORITHM` | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` |

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/auth/login` | Login (email o codigo_empleado + password) -> JWT |
| GET  | `/health` | Health check |
| GET  | `/cartera` | Cartera del día del asesor |
| POST | `/cartera/{id}/visita` | Registrar resultado de visita |
| POST | `/solicitudes` | Crear solicitud de crédito |
| GET  | `/cliente/notificaciones` | Notificaciones del cliente |
| PUT  | `/cliente/notificaciones/{id}/leer` | Marcar notificación como leída |

## Prueba rápida

```bash
# login como asesor FV
curl -X POST http://localhost:8010/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"codigo_empleado\":\"0001\",\"password\":\"0001123\"}"

# health
curl http://localhost:8010/health
```
