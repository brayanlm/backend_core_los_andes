"""v004_buro_preevaluacion_flow

Adds cr_buro_consulta and cr_preevaluacion tables + flow status columns
to cr_solicitud_credito for the credit origination gate workflow.

Revision ID: d4e5f6a7b8c9
Revises: ec889048a599
Create Date: 2026-06-29 23:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "ec889048a599"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    is_sqlite = op.get_context().dialect.name == "sqlite"

    # ── Flow status columns on cr_solicitud_credito ──
    with op.batch_alter_table("cr_solicitud_credito", schema=None) as b:
        b.add_column(sa.Column("visita_registrada", sa.Integer(), server_default="0"))
        b.add_column(sa.Column("preevaluacion_realizada", sa.Integer(), server_default="0"))
        b.add_column(sa.Column("buro_consultado", sa.Integer(), server_default="0"))
        b.add_column(sa.Column("documentos_completos", sa.Integer(), server_default="0"))
        b.add_column(sa.Column("firma_capturada", sa.Integer(), server_default="0"))

    # ── cr_preevaluacion ──
    op.create_table(
        "cr_preevaluacion",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("solicitud_id", sa.String(), nullable=False),
        sa.Column("asesor_id", sa.String(), nullable=True),
        sa.Column("cliente_id", sa.String(), nullable=False),
        sa.Column("ingreso_mensual", sa.Float(), server_default="0"),
        sa.Column("gasto_mensual", sa.Float(), server_default="0"),
        sa.Column("monto_solicitado", sa.Float(), nullable=False),
        sa.Column("plazo", sa.Integer(), nullable=False),
        sa.Column("cuota_estimada", sa.Float(), nullable=True),
        sa.Column("antiguedad_negocio_meses", sa.Integer(), server_default="0"),
        sa.Column("score", sa.Integer(), server_default="0"),
        sa.Column("resultado", sa.String(), nullable=False),
        sa.Column("puntaje", sa.Integer(), nullable=False),
        sa.Column("ratio_cuota_ingreso", sa.Float(), nullable=True),
        sa.Column("observaciones", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_preevaluacion")),
    )
    if not is_sqlite:
        op.create_foreign_key(
            op.f("fk_cr_preevaluacion_solicitud_id_cr_solicitud_credito"),
            "cr_preevaluacion", "cr_solicitud_credito",
            ["solicitud_id"], ["id"],
        )
        op.create_foreign_key(
            op.f("fk_cr_preevaluacion_asesor_id_cr_asesor"),
            "cr_preevaluacion", "cr_asesor",
            ["asesor_id"], ["id"],
        )
        op.create_foreign_key(
            op.f("fk_cr_preevaluacion_cliente_id_cr_cliente"),
            "cr_preevaluacion", "cr_cliente",
            ["cliente_id"], ["id"],
        )
    with op.batch_alter_table("cr_preevaluacion", schema=None) as b:
        b.create_index(b.f("ix_cr_preevaluacion_solicitud_id"), ["solicitud_id"], unique=False)

    # ── cr_buro_consulta ──
    op.create_table(
        "cr_buro_consulta",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("solicitud_id", sa.String(), nullable=True),
        sa.Column("asesor_id", sa.String(), nullable=True),
        sa.Column("cliente_id", sa.String(), nullable=False),
        sa.Column("dni", sa.String(), nullable=False),
        sa.Column("calificacion", sa.String(), nullable=False),
        sa.Column("entidades_con_deuda", sa.Integer(), server_default="0"),
        sa.Column("deuda_total", sa.Float(), server_default="0"),
        sa.Column("mayor_deuda", sa.Float(), server_default="0"),
        sa.Column("dias_mayor_mora", sa.Integer(), server_default="0"),
        sa.Column("en_lista_negra", sa.Integer(), server_default="0"),
        sa.Column("recomendacion", sa.String(), nullable=True),
        sa.Column("motivo_bloqueo", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cr_buro_consulta")),
    )
    if not is_sqlite:
        op.create_foreign_key(
            op.f("fk_cr_buro_consulta_solicitud_id_cr_solicitud_credito"),
            "cr_buro_consulta", "cr_solicitud_credito",
            ["solicitud_id"], ["id"],
        )
        op.create_foreign_key(
            op.f("fk_cr_buro_consulta_asesor_id_cr_asesor"),
            "cr_buro_consulta", "cr_asesor",
            ["asesor_id"], ["id"],
        )
        op.create_foreign_key(
            op.f("fk_cr_buro_consulta_cliente_id_cr_cliente"),
            "cr_buro_consulta", "cr_cliente",
            ["cliente_id"], ["id"],
        )
    with op.batch_alter_table("cr_buro_consulta", schema=None) as b:
        b.create_index(b.f("ix_cr_buro_consulta_solicitud_id"), ["solicitud_id"], unique=False)


def downgrade() -> None:
    is_sqlite = op.get_context().dialect.name == "sqlite"

    with op.batch_alter_table("cr_buro_consulta", schema=None) as b:
        b.drop_index(b.f("ix_cr_buro_consulta_solicitud_id"))

    if not is_sqlite:
        op.drop_constraint(
            op.f("fk_cr_buro_consulta_solicitud_id_cr_solicitud_credito"),
            "cr_buro_consulta",
        )
        op.drop_constraint(
            op.f("fk_cr_buro_consulta_asesor_id_cr_asesor"),
            "cr_buro_consulta",
        )
        op.drop_constraint(
            op.f("fk_cr_buro_consulta_cliente_id_cr_cliente"),
            "cr_buro_consulta",
        )
    op.drop_table("cr_buro_consulta")

    with op.batch_alter_table("cr_preevaluacion", schema=None) as b:
        b.drop_index(b.f("ix_cr_preevaluacion_solicitud_id"))

    if not is_sqlite:
        op.drop_constraint(
            op.f("fk_cr_preevaluacion_solicitud_id_cr_solicitud_credito"),
            "cr_preevaluacion",
        )
        op.drop_constraint(
            op.f("fk_cr_preevaluacion_asesor_id_cr_asesor"),
            "cr_preevaluacion",
        )
        op.drop_constraint(
            op.f("fk_cr_preevaluacion_cliente_id_cr_cliente"),
            "cr_preevaluacion",
        )
    op.drop_table("cr_preevaluacion")

    with op.batch_alter_table("cr_solicitud_credito", schema=None) as b:
        b.drop_column("firma_capturada")
        b.drop_column("documentos_completos")
        b.drop_column("buro_consultado")
        b.drop_column("preevaluacion_realizada")
        b.drop_column("visita_registrada")
