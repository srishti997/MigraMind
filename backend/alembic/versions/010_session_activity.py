"""Add nullable session activity without backfilling, revoking or changing health data."""
from alembic import op
import sqlalchemy as sa

revision = '010'
down_revision = '009'


def upgrade():
    op.add_column('login_sessions', sa.Column('last_activity_at_ms', sa.BigInteger(), nullable=True))


def downgrade():
    raise RuntimeError('Keep the additive activity column; use reviewed code rollback and session invalidation before removing idle enforcement.')
