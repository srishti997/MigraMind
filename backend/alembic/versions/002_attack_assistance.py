from alembic import op
import sqlalchemy as sa
revision = '002'
down_revision = '001'
def upgrade():
    op.add_column('profiles', sa.Column('communication', sa.Text(), nullable=False, server_default=''))
    op.create_table('attack_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('started_at', sa.String(40), nullable=False),
        sa.Column('ended_at', sa.String(40), nullable=True),
        sa.Column('active_slot', sa.Integer(), nullable=True, unique=True),
        sa.CheckConstraint('(ended_at IS NULL AND active_slot = 1) OR (ended_at IS NOT NULL AND active_slot IS NULL)', name='session_state'))
def downgrade():
    op.drop_table('attack_sessions')
    op.drop_column('profiles', 'communication')
