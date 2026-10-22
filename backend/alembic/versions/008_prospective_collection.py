"""Add collection and revision tables without changing existing health records."""
from alembic import op
import sqlalchemy as sa
revision = '008'
down_revision = '007'


def upgrade():
    op.create_table('daily_checkins',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('date', sa.String(10), nullable=False),
        sa.Column('timezone_name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.String(40), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('deleted_at', sa.String(40), nullable=True),
        sa.Column('values', sa.JSON(), nullable=True),
        sa.UniqueConstraint('owner_id', 'date', name='daily_owner_date'),
        sa.CheckConstraint('revision >= 1', name='daily_revision_positive'))
    op.create_index('ix_daily_checkins_owner_id', 'daily_checkins', ['owner_id'])
    op.create_table('checkin_revisions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('owner_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('checkin_id', sa.Integer(), sa.ForeignKey('daily_checkins.id'), nullable=False),
        sa.Column('revision', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(20), nullable=False),
        sa.Column('recorded_at', sa.String(40), nullable=False),
        sa.Column('values', sa.JSON(), nullable=True),
        sa.UniqueConstraint('checkin_id', 'revision', name='checkin_revision_unique'))
    op.create_index('ix_checkin_revisions_owner_id', 'checkin_revisions', ['owner_id'])


def downgrade():
    raise RuntimeError('Collection history must be privately exported and reviewed before a data-losing downgrade.')
