-- ============================================================
-- bd_core_mobile — DDL Completo
-- Tablas espejo cr_* + sync_outbox + tablas del núcleo financiero
-- ============================================================

PRAGMA foreign_keys = ON;

-- -----------------------------------------------------------
-- 1. cr_actividad_economica (catálogo)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_actividad_economica (
    cod_actividad    TEXT PRIMARY KEY,
    descripcion      TEXT NOT NULL,
    riesgo_sbs       TEXT DEFAULT 'NORMAL'
);

-- -----------------------------------------------------------
-- 2. cr_garantia (catálogo)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_garantia (
    cod_garantia     TEXT PRIMARY KEY,
    descripcion      TEXT NOT NULL,
    factor_liquidez  REAL DEFAULT 0.0
);

-- -----------------------------------------------------------
-- 3. cr_asesor
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_asesor (
    id               TEXT PRIMARY KEY,
    codigo_empleado  TEXT UNIQUE NOT NULL,
    email            TEXT,
    nombres          TEXT NOT NULL,
    apellidos        TEXT NOT NULL,
    perfil           TEXT NOT NULL DEFAULT 'operador',
    rol              TEXT NOT NULL DEFAULT 'ASESOR',
    agencia_id       TEXT,
    activo           INTEGER DEFAULT 1,
    created_at       TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 4. cr_cliente
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_cliente (
    id                      TEXT PRIMARY KEY,
    numero_documento        TEXT UNIQUE NOT NULL,
    nombres                 TEXT NOT NULL,
    apellidos               TEXT NOT NULL,
    telefono                TEXT,
    direccion               TEXT,
    email                   TEXT,
    tipo_negocio            TEXT,
    nombre_negocio          TEXT,
    antiguedad_negocio_meses INTEGER,
    calificacion_sbs        TEXT DEFAULT 'NORMAL',
    lat                     REAL,
    lng                     REAL,
    es_prospecto            INTEGER DEFAULT 0,
    created_at              TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 5. cr_usuario_cliente (login credenciales)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_usuario_cliente (
    id               TEXT PRIMARY KEY,
    cliente_id       TEXT NOT NULL REFERENCES cr_cliente(id),
    username         TEXT UNIQUE NOT NULL,
    password_hash    TEXT NOT NULL,
    intentos_fallidos INTEGER DEFAULT 0,
    bloqueado_hasta  TEXT,
    activo           INTEGER DEFAULT 1,
    created_at       TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 6. cr_solicitud_credito
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_solicitud_credito (
    id                 TEXT PRIMARY KEY,
    numero_expediente  TEXT UNIQUE NOT NULL,
    asesor_id          TEXT REFERENCES cr_asesor(id),
    cliente_id         TEXT NOT NULL REFERENCES cr_cliente(id),
    agencia_id         TEXT,
    canal              TEXT DEFAULT 'asesor',
    tipo_negocio       TEXT,
    nombre_negocio     TEXT,
    ingresos           REAL,
    monto              REAL NOT NULL,
    plazo              INTEGER NOT NULL,
    moneda             TEXT DEFAULT 'PEN',
    tipo_cuota         TEXT DEFAULT 'mensual',
    garantia           TEXT DEFAULT 'sin_garantia',
    destino_credito    TEXT,
    cuota_estimada     REAL,
    tea_referencial    REAL,
    firma_cliente_base64 TEXT,
    estado             TEXT DEFAULT 'enviado',
    credito_id         TEXT,
    evaluado_por       TEXT,
    evaluado_nombre    TEXT,
    fecha_evaluacion   TEXT,
    monto_aprobado     REAL,
    motivo_rechazo     TEXT,
    tasa_sugerida      REAL,
    score_usado        INTEGER DEFAULT 0,
    created_at         TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 7. cr_credito
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_credito (
    id                  TEXT PRIMARY KEY,
    solicitud_id        TEXT REFERENCES cr_solicitud_credito(id),
    cliente_id          TEXT NOT NULL REFERENCES cr_cliente(id),
    asesor_id           TEXT REFERENCES cr_asesor(id),
    cod_cuenta_credito  TEXT,
    producto            TEXT DEFAULT 'credito_microempresa',
    monto               REAL NOT NULL,
    monto_desembolsado  REAL,
    saldo_capital       REAL,
    saldo_total         REAL,
    plazo_meses         INTEGER NOT NULL,
    tasa                REAL,
    tea                 REAL,
    ingreso_cliente     REAL,
    cuota_estimada      REAL,
    ratio_cuota_ingreso REAL,
    estado              TEXT DEFAULT 'APROBADO',
    score               INTEGER DEFAULT 500,
    calificacion_interna TEXT,
    dias_mora           INTEGER DEFAULT 0,
    cuotas_total        INTEGER,
    cuotas_pagadas      INTEGER,
    destino             TEXT,
    motivo_rechazo      TEXT,
    fecha_creacion      TEXT DEFAULT (datetime('now')),
    fecha_evaluacion    TEXT,
    fecha_aprobacion    TEXT,
    fecha_desembolso    TEXT
);

-- -----------------------------------------------------------
-- 8. cr_cronograma_pago
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_cronograma_pago (
    id                 TEXT PRIMARY KEY,
    credito_id         TEXT NOT NULL REFERENCES cr_credito(id),
    cod_cuenta_credito TEXT,
    nro_cuota          INTEGER NOT NULL,
    fecha_vencimiento  TEXT,
    monto_cuota        REAL,
    monto_capital      REAL,
    monto_interes      REAL,
    saldo              REAL,
    estado_cuota       TEXT DEFAULT 'pendiente',
    fecha_pago         TEXT,
    created_at         TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 9. cr_cuenta_ahorro
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_cuenta_ahorro (
    id               TEXT PRIMARY KEY,
    cliente_id       TEXT NOT NULL REFERENCES cr_cliente(id),
    cod_cuenta_ahorro TEXT UNIQUE,
    tipo_cuenta      TEXT,
    moneda           TEXT DEFAULT 'PEN',
    saldo_capital    REAL DEFAULT 0.0,
    saldo_interes    REAL DEFAULT 0.0,
    tea              REAL,
    estado           TEXT DEFAULT 'activa',
    created_at       TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 10. cr_movimiento
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_movimiento (
    id              TEXT PRIMARY KEY,
    cliente_id      TEXT NOT NULL REFERENCES cr_cliente(id),
    cod_cuenta      TEXT,
    cod_operacion   TEXT,
    tipo            TEXT,
    concepto        TEXT,
    canal           TEXT,
    monto           REAL NOT NULL,
    moneda          TEXT DEFAULT 'PEN',
    fecha_operacion TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 11. cr_tarjeta
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_tarjeta (
    id                TEXT PRIMARY KEY,
    cliente_id        TEXT NOT NULL REFERENCES cr_cliente(id),
    numero_enmascarado TEXT,
    marca             TEXT,
    linea_credito     REAL DEFAULT 0.0,
    saldo_utilizado   REAL DEFAULT 0.0,
    fecha_corte       TEXT,
    fecha_pago        TEXT,
    estado            TEXT DEFAULT 'activa',
    created_at        TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 12. cr_notificacion
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_notificacion (
    id            TEXT PRIMARY KEY,
    cliente_id    TEXT NOT NULL REFERENCES cr_cliente(id),
    tipo          TEXT,
    titulo        TEXT NOT NULL,
    mensaje       TEXT,
    cuerpo        TEXT,
    leida         INTEGER DEFAULT 0,
    created_at    TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 13. cr_operacion (registro de transferencias/pagos)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_operacion (
    id                TEXT PRIMARY KEY,
    cliente_id        TEXT NOT NULL REFERENCES cr_cliente(id),
    cod_cuenta_origen  TEXT,
    cod_cuenta_destino TEXT,
    tipo              TEXT NOT NULL,
    monto             REAL NOT NULL,
    moneda            TEXT DEFAULT 'PEN',
    estado            TEXT DEFAULT 'pendiente',
    created_at        TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 14. cr_accion_cobranza
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_accion_cobranza (
    id                TEXT PRIMARY KEY,
    asesor_id         TEXT REFERENCES cr_asesor(id),
    cliente_id        TEXT NOT NULL REFERENCES cr_cliente(id),
    cod_cuenta_credito TEXT,
    tipo_gestion      TEXT NOT NULL,
    resultado         TEXT NOT NULL,
    monto_pagado      REAL,
    fecha_compromiso  TEXT,
    monto_compromiso  REAL,
    observaciones     TEXT DEFAULT '',
    lat               REAL,
    lng               REAL,
    timestamp_gestion TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 15. cr_credito_preaprobado
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_credito_preaprobado (
    id                TEXT PRIMARY KEY,
    cliente_id        TEXT NOT NULL REFERENCES cr_cliente(id),
    monto_maximo      REAL NOT NULL,
    plazo_sugerido_meses INTEGER,
    tea_referencial   REAL,
    score_confianza   INTEGER DEFAULT 0,
    vigente           INTEGER DEFAULT 1,
    fecha_vencimiento TEXT,
    created_at        TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 16. cr_historial_credito
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_historial_credito (
    id              TEXT PRIMARY KEY,
    credito_id      TEXT NOT NULL REFERENCES cr_credito(id),
    estado_anterior TEXT,
    estado_nuevo    TEXT NOT NULL,
    usuario_id      TEXT,
    usuario_nombre  TEXT,
    comentario      TEXT,
    timestamp       TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 17. cr_nota_interna
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_nota_interna (
    id            TEXT PRIMARY KEY,
    solicitud_id  TEXT NOT NULL REFERENCES cr_solicitud_credito(id),
    asesor_id     TEXT REFERENCES cr_asesor(id),
    contenido     TEXT NOT NULL,
    created_at    TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 18. cr_cartera_diaria
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_cartera_diaria (
    id              TEXT PRIMARY KEY,
    asesor_id       TEXT NOT NULL REFERENCES cr_asesor(id),
    cliente_id      TEXT NOT NULL REFERENCES cr_cliente(id),
    fecha_asignacion TEXT NOT NULL,
    tipo_gestion    TEXT,
    prioridad       TEXT DEFAULT 'normal',
    score_prioridad INTEGER DEFAULT 0,
    monto_credito   REAL DEFAULT 0.0,
    estado_visita   TEXT DEFAULT 'pendiente',
    orden_manual    INTEGER,
    lat             REAL,
    lng             REAL,
    resultado_visita    TEXT,
    observacion_visita  TEXT,
    timestamp_visita    TEXT,
    lat_visita          REAL,
    lng_visita          REAL
);

-- -----------------------------------------------------------
-- 19. cr_sync_outbox — cola de pendientes de sincronización
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_sync_outbox (
    id              TEXT PRIMARY KEY,
    entidad         TEXT NOT NULL,       -- nombre tabla/colección
    operacion       TEXT NOT NULL,       -- INSERT / UPDATE / DELETE
    datos           TEXT NOT NULL,       -- JSON con payload
    estado          TEXT DEFAULT 'pendiente',  -- pendiente / procesado / error
    error_msg       TEXT,
    intentos        INTEGER DEFAULT 0,
    created_at      TEXT DEFAULT (datetime('now')),
    procesado_at    TEXT
);

-- -----------------------------------------------------------
-- 20. cr_sync_log — registro de sincronizaciones
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS cr_sync_log (
    id              TEXT PRIMARY KEY,
    tipo            TEXT NOT NULL,       -- push / pull
    entidad         TEXT NOT NULL,
    registros       INTEGER DEFAULT 0,
    resultado       TEXT DEFAULT 'ok',   -- ok / error
    detalle         TEXT,
    created_at      TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 21. dcliente — espejo del núcleo financiero (bd_core_financiero)
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS dcliente (
    cod_cliente         TEXT PRIMARY KEY,
    numero_documento    TEXT NOT NULL,
    nombres             TEXT NOT NULL,
    apellidos           TEXT NOT NULL,
    direccion           TEXT,
    telefono            TEXT,
    email               TEXT,
    tipo_persona        TEXT DEFAULT 'natural',
    fecha_registro      TEXT,
    calificacion_sbs    TEXT DEFAULT 'NORMAL',
    deuda_total         REAL DEFAULT 0.0,
    estado              TEXT DEFAULT 'activo',
    ultima_actualizacion TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- 22. dsolicitud — espejo del núcleo financiero
-- -----------------------------------------------------------
CREATE TABLE IF NOT EXISTS dsolicitud (
    cod_solicitud       TEXT PRIMARY KEY,
    cod_cliente         TEXT NOT NULL REFERENCES dcliente(cod_cliente),
    monto_solicitado    REAL NOT NULL,
    plazo_solicitado    INTEGER NOT NULL,
    destino             TEXT,
    estado              TEXT DEFAULT 'pendiente',  -- pendiente / aprobado / rechazado / desembolsado
    cod_credito_asignado TEXT,
    fecha_solicitud     TEXT,
    fecha_aprobacion    TEXT,
    fecha_desembolso    TEXT,
    observaciones       TEXT,
    ultima_actualizacion TEXT DEFAULT (datetime('now'))
);

-- -----------------------------------------------------------
-- Índices
-- -----------------------------------------------------------
CREATE INDEX IF NOT EXISTS idx_cliente_documento ON cr_cliente(numero_documento);
CREATE INDEX IF NOT EXISTS idx_solicitud_cliente ON cr_solicitud_credito(cliente_id);
CREATE INDEX IF NOT EXISTS idx_solicitud_estado ON cr_solicitud_credito(estado);
CREATE INDEX IF NOT EXISTS idx_credito_cliente ON cr_credito(cliente_id);
CREATE INDEX IF NOT EXISTS idx_credito_estado ON cr_credito(estado);
CREATE INDEX IF NOT EXISTS idx_cronograma_credito ON cr_cronograma_pago(credito_id);
CREATE INDEX IF NOT EXISTS idx_cuenta_cliente ON cr_cuenta_ahorro(cliente_id);
CREATE INDEX IF NOT EXISTS idx_movimiento_cliente ON cr_movimiento(cliente_id);
CREATE INDEX IF NOT EXISTS idx_notificacion_cliente ON cr_notificacion(cliente_id);
CREATE INDEX IF NOT EXISTS idx_cartera_asesor ON cr_cartera_diaria(asesor_id, fecha_asignacion);
CREATE INDEX IF NOT EXISTS idx_outbox_estado ON cr_sync_outbox(estado);
CREATE INDEX IF NOT EXISTS idx_dcliente_documento ON dcliente(numero_documento);
CREATE INDEX IF NOT EXISTS idx_dsolicitud_cliente ON dsolicitud(cod_cliente);
