"""v002_add_asesor_lockout_and_missing_tables

Revision ID: a1b2c3d4e5f6
Revises: c1caf38129c8
Create Date: 2026-06-17 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = 'c1caf38129c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    is_sqlite = op.get_context().dialect.name == 'sqlite'

    # ── 1. Add lockout columns to cr_asesor ──
    with op.batch_alter_table('cr_asesor', schema=None) as batch_op:
        batch_op.add_column(sa.Column('intentos_fallidos', sa.Integer(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('bloqueado_hasta', sa.String(), nullable=True))

    # ── 2. Create missing tables ──
    # dcliente — mirror of core financiero client master
    op.create_table('dcliente',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('cod_cliente', sa.String(), nullable=True),
        sa.Column('numero_documento', sa.String(), nullable=True),
        sa.Column('nombres', sa.String(), nullable=True),
        sa.Column('apellidos', sa.String(), nullable=True),
        sa.Column('calificacion_sbs', sa.String(), nullable=True),
        sa.Column('estado', sa.String(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_dcliente')),
    )
    # dsolicitud — mirror of core financiero loan application
    op.create_table('dsolicitud',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('cod_cliente', sa.String(), nullable=True),
        sa.Column('cod_solicitud', sa.String(), nullable=True),
        sa.Column('monto', sa.Float(), nullable=True),
        sa.Column('plazo_meses', sa.Integer(), nullable=True),
        sa.Column('estado', sa.String(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['cod_cliente'], ['dcliente.id'],
                                name=op.f('fk_dsolicitud_cod_cliente_dcliente')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_dsolicitud')),
    )
    # cr_actividad_economica — catalog
    op.create_table('cr_actividad_economica',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('codigo', sa.String(), nullable=True),
        sa.Column('nombre', sa.String(), nullable=False),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_cr_actividad_economica')),
    )
    # cr_garantia — catalog
    op.create_table('cr_garantia',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('tipo', sa.String(), nullable=False),
        sa.Column('descripcion', sa.String(), nullable=True),
        sa.Column('porcentaje_cobertura', sa.Float(), nullable=True),
        sa.Column('created_at', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_cr_garantia')),
    )


def downgrade() -> None:
    is_sqlite = op.get_context().dialect.name == 'sqlite'

    op.drop_table('cr_garantia')
    op.drop_table('cr_actividad_economica')
    op.drop_table('dsolicitud')
    op.drop_table('dcliente')

    with op.batch_alter_table('cr_asesor', schema=None) as batch_op:
        batch_op.drop_column('bloqueado_hasta')
        batch_op.drop_column('intentos_fallidos')
