"""Add an empty demonstration provenance marker; never label existing data synthetic."""
from alembic import op
import sqlalchemy as sa

revision = '009'
down_revision = '008'


def upgrade():
    op.create_table('demo_deployments',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('fixture_version', sa.String(40), nullable=False),
        sa.Column('created_at', sa.String(40), nullable=False))


def downgrade():
    raise RuntimeError('Use a verified snapshot and reviewed release rollback; do not erase demo provenance automatically.')
