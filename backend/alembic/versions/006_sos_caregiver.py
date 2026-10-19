"""Add optional assistance preferences without changing existing records."""
from alembic import op
import sqlalchemy as sa
revision='006'
down_revision='005'

def upgrade():
    op.add_column('profiles',sa.Column('environment',sa.Text(),nullable=False,server_default=''))
    op.add_column('support_preferences',sa.Column('help_message',sa.String(400),nullable=False,
        server_default='I am having a migraine attack and would appreciate support. Please check in by text when you can.'))
    op.add_column('support_preferences',sa.Column('emergency_number',sa.String(6),nullable=False,server_default='112'))

def downgrade():
    raise RuntimeError('Review and export saved assistance preferences before a data-losing downgrade.')
