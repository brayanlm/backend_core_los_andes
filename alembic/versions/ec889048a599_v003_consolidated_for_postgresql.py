"""v003_consolidated_for_postgresql

Consolidates all tables with proper FK ordering for PostgreSQL.
Handles circular FK between cr_credito <-> cr_solicitud_credito
by adding one of the FKs with ALTER TABLE after both tables exist.

Revision ID: ec889048a599
Revises: a1b2c3d4e5f6
Create Date: 2026-06-25 11:21:04.004062
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "ec889048a599"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _fk_name(table, column, ref_table):
    return op.f(f"fk_{table}_{column}_{ref_table}")


def upgrade() -> None:
    is_sqlite = op.get_context().dialect.name == "sqlite"

    # ── Tables without FKs ─────────────────────────────────
    op.create_table(
        "cr_cliente",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("numero_documento", sa.String(), nullable=False),
        sa.Column("nombres", sa.String(), nullable=False),
        sa.Column("apellidos", sa.String(), nullable=False),
        sa.Column("telefono", sa.String(), nullable=True),
        sa.Column("direccion", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("tipo_negocio", sa.String(), nullable=True),
        sa.Column("nombre_negocio", sa.String(), nullable=True),
        sa.Column("antiguedad_negocio_meses", sa.Integer(), nullable=True),
        sa.Column("calificacion_sbs", sa.String(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("es_prospecto", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_cliente")),
    )
    with op.batch_alter_table("cr_cliente", schema=None) as b:
        b.create_index(b.f("ix_cr_cliente_numero_documento"), ["numero_documento"], unique=True)

    op.create_table(
        "cr_asesor",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("codigo_empleado", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("nombres", sa.String(), nullable=False),
        sa.Column("apellidos", sa.String(), nullable=False),
        sa.Column("perfil", sa.String(), nullable=True),
        sa.Column("rol", sa.String(), nullable=True),
        sa.Column("agencia_id", sa.String(), nullable=True),
        sa.Column("activo", sa.Integer(), nullable=True),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.Column("intentos_fallidos", sa.Integer(), nullable=True),
        sa.Column("bloqueado_hasta", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_asesor")),
        sa.UniqueConstraint("codigo_empleado", name=op.f("uq_cr_asesor_codigo_empleado")),
    )
    with op.batch_alter_table("cr_asesor", schema=None) as b:
        b.create_index(b.f("ix_cr_asesor_created_at"), ["created_at"], unique=False)

    op.create_table(
        "cr_sync_log",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("entidad", sa.String(), nullable=False),
        sa.Column("registros", sa.Integer(), nullable=True),
        sa.Column("resultado", sa.String(), nullable=True),
        sa.Column("detalle", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_sync_log")),
    )

    op.create_table(
        "cr_sync_outbox",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("entidad", sa.String(), nullable=False),
        sa.Column("operacion", sa.String(), nullable=False),
        sa.Column("datos", sa.Text(), nullable=False),
        sa.Column("estado", sa.String(), nullable=True),
        sa.Column("error_msg", sa.String(), nullable=True),
        sa.Column("intentos", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.Column("procesado_at", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_sync_outbox")),
    )

    op.create_table(
        "dcliente",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("cod_cliente", sa.String(), nullable=True),
        sa.Column("numero_documento", sa.String(), nullable=True),
        sa.Column("nombres", sa.String(), nullable=True),
        sa.Column("apellidos", sa.String(), nullable=True),
        sa.Column("calificacion_sbs", sa.String(), nullable=True),
        sa.Column("estado", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dcliente")),
    )

    op.create_table(
        "cr_actividad_economica",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("codigo", sa.String(), nullable=True),
        sa.Column("nombre", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_actividad_economica")),
    )

    op.create_table(
        "cr_garantia",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("descripcion", sa.String(), nullable=True),
        sa.Column("porcentaje_cobertura", sa.Float(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_garantia")),
    )

    # ── cr_credito (FK to cr_cliente, cr_asesor; NOT to solicitud yet) ──
    op.create_table(
        "cr_credito",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("solicitud_id", sa.String(), nullable=True),
        sa.Column("cliente_id", sa.String(), nullable=False),
        sa.Column("asesor_id", sa.String(), nullable=True),
        sa.Column("cod_cuenta_credito", sa.String(), nullable=True),
        sa.Column("producto", sa.String(), nullable=True),
        sa.Column("monto", sa.Float(), nullable=False),
        sa.Column("monto_desembolsado", sa.Float(), nullable=True),
        sa.Column("saldo_capital", sa.Float(), nullable=True),
        sa.Column("saldo_total", sa.Float(), nullable=True),
        sa.Column("plazo_meses", sa.Integer(), nullable=False),
        sa.Column("tasa", sa.Float(), nullable=True),
        sa.Column("tea", sa.Float(), nullable=True),
        sa.Column("ingreso_cliente", sa.Float(), nullable=True),
        sa.Column("cuota_estimada", sa.Float(), nullable=True),
        sa.Column("ratio_cuota_ingreso", sa.Float(), nullable=True),
        sa.Column("estado", sa.String(), nullable=True),
        sa.Column("score", sa.Integer(), nullable=True),
        sa.Column("calificacion_interna", sa.String(), nullable=True),
        sa.Column("dias_mora", sa.Integer(), nullable=True),
        sa.Column("cuotas_total", sa.Integer(), nullable=True),
        sa.Column("cuotas_pagadas", sa.Integer(), nullable=True),
        sa.Column("destino", sa.String(), nullable=True),
        sa.Column("motivo_rechazo", sa.String(), nullable=True),
        sa.Column("fecha_creacion", sa.String(), nullable=True),
        sa.Column("fecha_evaluacion", sa.String(), nullable=True),
        sa.Column("fecha_aprobacion", sa.String(), nullable=True),
        sa.Column("fecha_desembolso", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["asesor_id"], ["cr_asesor.id"],
            name=_fk_name("cr_credito", "asesor_id", "cr_asesor"),
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id"], ["cr_cliente.id"],
            name=_fk_name("cr_credito", "cliente_id", "cr_cliente"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_credito")),
    )
    with op.batch_alter_table("cr_credito", schema=None) as b:
        b.create_index(b.f("ix_cr_credito_asesor_id"), ["asesor_id"], unique=False)
        b.create_index(b.f("ix_cr_credito_cliente_id"), ["cliente_id"], unique=False)
        b.create_index(b.f("ix_cr_credito_fecha_creacion"), ["fecha_creacion"], unique=False)

    # ── cr_solicitud_credito (FK to cr_credito via ALTER TABLE later) ──
    op.create_table(
        "cr_solicitud_credito",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("numero_expediente", sa.String(), nullable=False),
        sa.Column("asesor_id", sa.String(), nullable=True),
        sa.Column("cliente_id", sa.String(), nullable=False),
        sa.Column("agencia_id", sa.String(), nullable=True),
        sa.Column("canal", sa.String(), nullable=True),
        sa.Column("tipo_negocio", sa.String(), nullable=True),
        sa.Column("nombre_negocio", sa.String(), nullable=True),
        sa.Column("ingresos", sa.Float(), nullable=True),
        sa.Column("monto", sa.Float(), nullable=False),
        sa.Column("plazo", sa.Integer(), nullable=False),
        sa.Column("moneda", sa.String(), nullable=True),
        sa.Column("tipo_cuota", sa.String(), nullable=True),
        sa.Column("garantia", sa.String(), nullable=True),
        sa.Column("destino_credito", sa.String(), nullable=True),
        sa.Column("cuota_estimada", sa.Float(), nullable=True),
        sa.Column("tea_referencial", sa.Float(), nullable=True),
        sa.Column("firma_cliente_base64", sa.Text(), nullable=True),
        sa.Column("estado", sa.String(), nullable=True),
        sa.Column("credito_id", sa.String(), nullable=True),
        sa.Column("evaluado_por", sa.String(), nullable=True),
        sa.Column("evaluado_nombre", sa.String(), nullable=True),
        sa.Column("fecha_evaluacion", sa.String(), nullable=True),
        sa.Column("monto_aprobado", sa.Float(), nullable=True),
        sa.Column("motivo_rechazo", sa.String(), nullable=True),
        sa.Column("tasa_sugerida", sa.Float(), nullable=True),
        sa.Column("score_usado", sa.Integer(), nullable=True),
        sa.Column("condiciones", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["asesor_id"], ["cr_asesor.id"],
            name=_fk_name("cr_solicitud_credito", "asesor_id", "cr_asesor"),
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id"], ["cr_cliente.id"],
            name=_fk_name("cr_solicitud_credito", "cliente_id", "cr_cliente"),
        ),
        # FK to cr_credito added below via ALTER TABLE
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_solicitud_credito")),
        sa.UniqueConstraint(
            "numero_expediente",
            name=op.f("uq_cr_solicitud_credito_numero_expediente"),
        ),
    )
    with op.batch_alter_table("cr_solicitud_credito", schema=None) as b:
        b.create_index(b.f("ix_cr_solicitud_credito_asesor_id"), ["asesor_id"], unique=False)
        b.create_index(b.f("ix_cr_solicitud_credito_cliente_id"), ["cliente_id"], unique=False)
        b.create_index(b.f("ix_cr_solicitud_credito_created_at"), ["created_at"], unique=False)
        b.create_index(b.f("ix_cr_solicitud_credito_estado"), ["estado"], unique=False)

    # ── Circular FKs (both tables exist now) ──
    if not is_sqlite:
        op.create_foreign_key(
            _fk_name("cr_credito", "solicitud_id", "cr_solicitud_credito"),
            "cr_credito", "cr_solicitud_credito",
            ["solicitud_id"], ["id"],
        )
        op.create_foreign_key(
            _fk_name("cr_solicitud_credito", "credito_id", "cr_credito"),
            "cr_solicitud_credito", "cr_credito",
            ["credito_id"], ["id"],
        )

    # ── Tables with FKs to already-existing tables ──
    op.create_table(
        "cr_cronograma_pago",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("credito_id", sa.String(), nullable=False),
        sa.Column("nro_cuota", sa.Integer(), nullable=False),
        sa.Column("fecha_vencimiento", sa.String(), nullable=True),
        sa.Column("monto_cuota", sa.Float(), nullable=True),
        sa.Column("monto_capital", sa.Float(), nullable=True),
        sa.Column("monto_interes", sa.Float(), nullable=True),
        sa.Column("saldo", sa.Float(), nullable=True),
        sa.Column("estado_cuota", sa.String(), nullable=True),
        sa.Column("fecha_pago", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["credito_id"], ["cr_credito.id"],
            name=_fk_name("cr_cronograma_pago", "credito_id", "cr_credito"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_cronograma_pago")),
    )
    with op.batch_alter_table("cr_cronograma_pago", schema=None) as b:
        b.create_index(b.f("ix_cr_cronograma_pago_credito_id"), ["credito_id"], unique=False)

    op.create_table(
        "cr_movimiento",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("cliente_id", sa.String(), nullable=False),
        sa.Column("cod_cuenta", sa.String(), nullable=True),
        sa.Column("cod_operacion", sa.String(), nullable=True),
        sa.Column("tipo", sa.String(), nullable=True),
        sa.Column("concepto", sa.String(), nullable=True),
        sa.Column("canal", sa.String(), nullable=True),
        sa.Column("monto", sa.Float(), nullable=False),
        sa.Column("moneda", sa.String(), nullable=True),
        sa.Column("fecha_operacion", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["cliente_id"], ["cr_cliente.id"],
            name=_fk_name("cr_movimiento", "cliente_id", "cr_cliente"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_movimiento")),
    )
    with op.batch_alter_table("cr_movimiento", schema=None) as b:
        b.create_index(b.f("ix_cr_movimiento_cliente_id"), ["cliente_id"], unique=False)

    op.create_table(
        "cr_documento",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("solicitud_id", sa.String(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("nombre_archivo", sa.String(), nullable=True),
        sa.Column("contenido_base64", sa.Text(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["solicitud_id"], ["cr_solicitud_credito.id"],
            name=_fk_name("cr_documento", "solicitud_id", "cr_solicitud_credito"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_documento")),
    )
    with op.batch_alter_table("cr_documento", schema=None) as b:
        b.create_index(b.f("ix_cr_documento_solicitud_id"), ["solicitud_id"], unique=False)

    op.create_table(
        "cr_visita",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("solicitud_id", sa.String(), nullable=True),
        sa.Column("asesor_id", sa.String(), nullable=False),
        sa.Column("cliente_id", sa.String(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("observacion", sa.String(), nullable=True),
        sa.Column("resultado", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["asesor_id"], ["cr_asesor.id"],
            name=_fk_name("cr_visita", "asesor_id", "cr_asesor"),
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id"], ["cr_cliente.id"],
            name=_fk_name("cr_visita", "cliente_id", "cr_cliente"),
        ),
        sa.ForeignKeyConstraint(
            ["solicitud_id"], ["cr_solicitud_credito.id"],
            name=_fk_name("cr_visita", "solicitud_id", "cr_solicitud_credito"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_visita")),
    )
    with op.batch_alter_table("cr_visita", schema=None) as b:
        b.create_index(b.f("ix_cr_visita_solicitud_id"), ["solicitud_id"], unique=False)

    op.create_table(
        "cr_cartera_diaria",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("asesor_id", sa.String(), nullable=False),
        sa.Column("cliente_id", sa.String(), nullable=False),
        sa.Column("fecha_asignacion", sa.String(), nullable=False),
        sa.Column("tipo_gestion", sa.String(), nullable=True),
        sa.Column("prioridad", sa.String(), nullable=True),
        sa.Column("score_prioridad", sa.Integer(), nullable=True),
        sa.Column("monto_credito", sa.Float(), nullable=True),
        sa.Column("estado_visita", sa.String(), nullable=True),
        sa.Column("orden_manual", sa.Integer(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("resultado_visita", sa.String(), nullable=True),
        sa.Column("observacion_visita", sa.String(), nullable=True),
        sa.Column("timestamp_visita", sa.String(), nullable=True),
        sa.Column("lat_visita", sa.Float(), nullable=True),
        sa.Column("lng_visita", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(
            ["asesor_id"], ["cr_asesor.id"],
            name=_fk_name("cr_cartera_diaria", "asesor_id", "cr_asesor"),
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id"], ["cr_cliente.id"],
            name=_fk_name("cr_cartera_diaria", "cliente_id", "cr_cliente"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_cartera_diaria")),
    )
    with op.batch_alter_table("cr_cartera_diaria", schema=None) as b:
        b.create_index(b.f("ix_cr_cartera_diaria_asesor_id"), ["asesor_id"], unique=False)

    op.create_table(
        "cr_cuenta_ahorro",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("cliente_id", sa.String(), nullable=False),
        sa.Column("cod_cuenta_ahorro", sa.String(), nullable=True),
        sa.Column("tipo_cuenta", sa.String(), nullable=True),
        sa.Column("moneda", sa.String(), nullable=True),
        sa.Column("saldo_capital", sa.Float(), nullable=True),
        sa.Column("saldo_interes", sa.Float(), nullable=True),
        sa.Column("tea", sa.Float(), nullable=True),
        sa.Column("estado", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["cliente_id"], ["cr_cliente.id"],
            name=_fk_name("cr_cuenta_ahorro", "cliente_id", "cr_cliente"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_cuenta_ahorro")),
        sa.UniqueConstraint(
            "cod_cuenta_ahorro",
            name=op.f("uq_cr_cuenta_ahorro_cod_cuenta_ahorro"),
        ),
    )
    with op.batch_alter_table("cr_cuenta_ahorro", schema=None) as b:
        b.create_index(b.f("ix_cr_cuenta_ahorro_cliente_id"), ["cliente_id"], unique=False)

    op.create_table(
        "cr_usuario_cliente",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("cliente_id", sa.String(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("intentos_fallidos", sa.Integer(), nullable=True),
        sa.Column("bloqueado_hasta", sa.String(), nullable=True),
        sa.Column("activo", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["cliente_id"], ["cr_cliente.id"],
            name=_fk_name("cr_usuario_cliente", "cliente_id", "cr_cliente"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_usuario_cliente")),
        sa.UniqueConstraint("username", name=op.f("uq_cr_usuario_cliente_username")),
    )

    op.create_table(
        "cr_accion_cobranza",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("asesor_id", sa.String(), nullable=True),
        sa.Column("cliente_id", sa.String(), nullable=False),
        sa.Column("cod_cuenta_credito", sa.String(), nullable=True),
        sa.Column("tipo_gestion", sa.String(), nullable=False),
        sa.Column("resultado", sa.String(), nullable=False),
        sa.Column("monto_pagado", sa.Float(), nullable=True),
        sa.Column("fecha_compromiso", sa.String(), nullable=True),
        sa.Column("monto_compromiso", sa.Float(), nullable=True),
        sa.Column("observaciones", sa.String(), nullable=True),
        sa.Column("lat", sa.Float(), nullable=True),
        sa.Column("lng", sa.Float(), nullable=True),
        sa.Column("timestamp_gestion", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["asesor_id"], ["cr_asesor.id"],
            name=_fk_name("cr_accion_cobranza", "asesor_id", "cr_asesor"),
        ),
        sa.ForeignKeyConstraint(
            ["cliente_id"], ["cr_cliente.id"],
            name=_fk_name("cr_accion_cobranza", "cliente_id", "cr_cliente"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_accion_cobranza")),
    )

    op.create_table(
        "cr_credito_preaprobado",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("cliente_id", sa.String(), nullable=False),
        sa.Column("monto_maximo", sa.Float(), nullable=False),
        sa.Column("plazo_sugerido_meses", sa.Integer(), nullable=True),
        sa.Column("tea_referencial", sa.Float(), nullable=True),
        sa.Column("score_confianza", sa.Integer(), nullable=True),
        sa.Column("vigente", sa.Integer(), nullable=True),
        sa.Column("fecha_vencimiento", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["cliente_id"], ["cr_cliente.id"],
            name=_fk_name("cr_credito_preaprobado", "cliente_id", "cr_cliente"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_credito_preaprobado")),
    )

    op.create_table(
        "cr_tarjeta",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("cliente_id", sa.String(), nullable=False),
        sa.Column("numero_enmascarado", sa.String(), nullable=True),
        sa.Column("marca", sa.String(), nullable=True),
        sa.Column("linea_credito", sa.Float(), nullable=True),
        sa.Column("saldo_utilizado", sa.Float(), nullable=True),
        sa.Column("fecha_corte", sa.String(), nullable=True),
        sa.Column("fecha_pago", sa.String(), nullable=True),
        sa.Column("estado", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["cliente_id"], ["cr_cliente.id"],
            name=_fk_name("cr_tarjeta", "cliente_id", "cr_cliente"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_tarjeta")),
    )

    op.create_table(
        "cr_notificacion",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("cliente_id", sa.String(), nullable=False),
        sa.Column("tipo", sa.String(), nullable=True),
        sa.Column("titulo", sa.String(), nullable=False),
        sa.Column("mensaje", sa.String(), nullable=True),
        sa.Column("cuerpo", sa.String(), nullable=True),
        sa.Column("leida", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["cliente_id"], ["cr_cliente.id"],
            name=_fk_name("cr_notificacion", "cliente_id", "cr_cliente"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_notificacion")),
    )
    with op.batch_alter_table("cr_notificacion", schema=None) as b:
        b.create_index(b.f("ix_cr_notificacion_cliente_id"), ["cliente_id"], unique=False)

    op.create_table(
        "cr_operacion",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("cliente_id", sa.String(), nullable=False),
        sa.Column("cod_cuenta_origen", sa.String(), nullable=True),
        sa.Column("cod_cuenta_destino", sa.String(), nullable=True),
        sa.Column("tipo", sa.String(), nullable=False),
        sa.Column("monto", sa.Float(), nullable=False),
        sa.Column("moneda", sa.String(), nullable=True),
        sa.Column("estado", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["cliente_id"], ["cr_cliente.id"],
            name=_fk_name("cr_operacion", "cliente_id", "cr_cliente"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_operacion")),
    )

    op.create_table(
        "cr_historial_credito",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("credito_id", sa.String(), nullable=False),
        sa.Column("estado_anterior", sa.String(), nullable=True),
        sa.Column("estado_nuevo", sa.String(), nullable=False),
        sa.Column("usuario_id", sa.String(), nullable=True),
        sa.Column("usuario_nombre", sa.String(), nullable=True),
        sa.Column("comentario", sa.String(), nullable=True),
        sa.Column("timestamp", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["credito_id"], ["cr_credito.id"],
            name=_fk_name("cr_historial_credito", "credito_id", "cr_credito"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_historial_credito")),
    )

    op.create_table(
        "cr_nota_interna",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("solicitud_id", sa.String(), nullable=False),
        sa.Column("asesor_id", sa.String(), nullable=True),
        sa.Column("contenido", sa.String(), nullable=False),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["asesor_id"], ["cr_asesor.id"],
            name=_fk_name("cr_nota_interna", "asesor_id", "cr_asesor"),
        ),
        sa.ForeignKeyConstraint(
            ["solicitud_id"], ["cr_solicitud_credito.id"],
            name=_fk_name("cr_nota_interna", "solicitud_id", "cr_solicitud_credito"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_nota_interna")),
    )

    op.create_table(
        "dsolicitud",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("cod_cliente", sa.String(), nullable=True),
        sa.Column("cod_solicitud", sa.String(), nullable=True),
        sa.Column("monto", sa.Float(), nullable=True),
        sa.Column("plazo_meses", sa.Integer(), nullable=True),
        sa.Column("estado", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["cod_cliente"], ["dcliente.id"],
            name=_fk_name("dsolicitud", "cod_cliente", "dcliente"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_dsolicitud")),
    )

    # For SQLite: add circular FKs with batch mode
    if is_sqlite:
        with op.batch_alter_table("cr_credito", schema=None) as b:
            b.create_foreign_key(
                _fk_name("cr_credito", "solicitud_id", "cr_solicitud_credito"),
                "cr_solicitud_credito", ["solicitud_id"], ["id"],
            )
        with op.batch_alter_table("cr_solicitud_credito", schema=None) as b:
            b.create_foreign_key(
                _fk_name("cr_solicitud_credito", "credito_id", "cr_credito"),
                "cr_credito", ["credito_id"], ["id"],
            )


def downgrade() -> None:
    is_sqlite = op.get_context().dialect.name == "sqlite"

    if is_sqlite:
        with op.batch_alter_table("cr_solicitud_credito", schema=None) as b:
            b.drop_constraint(_fk_name("cr_solicitud_credito", "credito_id", "cr_credito"))
        with op.batch_alter_table("cr_credito", schema=None) as b:
            b.drop_constraint(_fk_name("cr_credito", "solicitud_id", "cr_solicitud_credito"))
    else:
        op.drop_constraint(
            _fk_name("cr_credito", "solicitud_id", "cr_solicitud_credito"),
            "cr_credito",
        )
        op.drop_constraint(
            _fk_name("cr_solicitud_credito", "credito_id", "cr_credito"),
            "cr_solicitud_credito",
        )

    op.drop_table("dsolicitud")
    op.drop_table("cr_nota_interna")
    op.drop_table("cr_historial_credito")
    op.drop_table("cr_operacion")
    with op.batch_alter_table("cr_notificacion", schema=None) as b:
        b.drop_index(b.f("ix_cr_notificacion_cliente_id"))
    op.drop_table("cr_notificacion")
    op.drop_table("cr_tarjeta")
    op.drop_table("cr_credito_preaprobado")
    op.drop_table("cr_accion_cobranza")
    op.drop_table("cr_usuario_cliente")
    with op.batch_alter_table("cr_cuenta_ahorro", schema=None) as b:
        b.drop_index(b.f("ix_cr_cuenta_ahorro_cliente_id"))
    op.drop_table("cr_cuenta_ahorro")
    with op.batch_alter_table("cr_cartera_diaria", schema=None) as b:
        b.drop_index(b.f("ix_cr_cartera_diaria_asesor_id"))
    op.drop_table("cr_cartera_diaria")
    with op.batch_alter_table("cr_visita", schema=None) as b:
        b.drop_index(b.f("ix_cr_visita_solicitud_id"))
    op.drop_table("cr_visita")
    with op.batch_alter_table("cr_documento", schema=None) as b:
        b.drop_index(b.f("ix_cr_documento_solicitud_id"))
    op.drop_table("cr_documento")
    with op.batch_alter_table("cr_movimiento", schema=None) as b:
        b.drop_index(b.f("ix_cr_movimiento_cliente_id"))
    op.drop_table("cr_movimiento")
    with op.batch_alter_table("cr_cronograma_pago", schema=None) as b:
        b.drop_index(b.f("ix_cr_cronograma_pago_credito_id"))
    op.drop_table("cr_cronograma_pago")
    with op.batch_alter_table("cr_solicitud_credito", schema=None) as b:
        b.drop_index(b.f("ix_cr_solicitud_credito_estado"))
        b.drop_index(b.f("ix_cr_solicitud_credito_created_at"))
        b.drop_index(b.f("ix_cr_solicitud_credito_cliente_id"))
        b.drop_index(b.f("ix_cr_solicitud_credito_asesor_id"))
    op.drop_table("cr_solicitud_credito")
    with op.batch_alter_table("cr_credito", schema=None) as b:
        b.drop_index(b.f("ix_cr_credito_fecha_creacion"))
        b.drop_index(b.f("ix_cr_credito_cliente_id"))
        b.drop_index(b.f("ix_cr_credito_asesor_id"))
    op.drop_table("cr_credito")
    op.drop_table("cr_garantia")
    op.drop_table("cr_actividad_economica")
    op.drop_table("dcliente")
    op.drop_table("cr_sync_outbox")
    op.drop_table("cr_sync_log")
    with op.batch_alter_table("cr_asesor", schema=None) as b:
        b.drop_index(b.f("ix_cr_asesor_created_at"))
    op.drop_table("cr_asesor")
    with op.batch_alter_table("cr_cliente", schema=None) as b:
        b.drop_index(b.f("ix_cr_cliente_numero_documento"))
    op.drop_table("cr_cliente")
