"""Generic Alembic script template (mako)
This file is intentionally minimal to allow alembic autogeneration if desired.
"""
<%text>
from alembic import op
import sqlalchemy as sa
</%text>

revision = '${rev_id}'
down_revision = ${down_revision}
branch_labels = None
depends_on = None

def upgrade():
    ${upgrades if upgrades else 'pass'}

def downgrade():
    ${downgrades if downgrades else 'pass'}
