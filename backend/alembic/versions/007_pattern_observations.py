"""Optional explicit whole-day observations; old/missing records remain unknown."""
from alembic import op
import sqlalchemy as sa
revision='007'
down_revision='006'

def upgrade():
    op.add_column('wellness',sa.Column('episode_observation',sa.String(20),nullable=True))
    op.add_column('wellness',sa.Column('observation_recorded_at',sa.String(40),nullable=True))

def downgrade():
    raise RuntimeError('Export and review whole-day observations before a data-losing downgrade.')
