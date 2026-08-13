"""initial migration

Revision ID: 0001_initial
Revises: 
Create Date: 2026-08-13
"""
from alembic import op
import sqlalchemy as sa

revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'market_candles',
        sa.Column('time', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('symbol', sa.Text, nullable=False),
        sa.Column('open', sa.Float),
        sa.Column('high', sa.Float),
        sa.Column('low', sa.Float),
        sa.Column('close', sa.Float),
        sa.Column('volume', sa.Float),
        sa.PrimaryKeyConstraint('time', 'symbol'),
    )

    op.create_table(
        'ammis_migrations',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.Text, nullable=False),
        sa.Column('applied_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()')),
    )


def downgrade() -> None:
    op.drop_table('ammis_migrations')
    op.drop_table('market_candles')
