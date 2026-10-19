from alembic import op
import sqlalchemy as sa
revision='004'
down_revision='003'
def upgrade():
    op.create_table('support_preferences',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('preferred_contact_id',sa.Integer(),sa.ForeignKey('contacts.id',ondelete='SET NULL'),nullable=True),
        sa.Column('communication_method',sa.String(20),nullable=False,server_default='none'),
        sa.Column('preferred_actions',sa.JSON(),nullable=False,server_default='[]'),
        sa.Column('large_text',sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column('reduce_motion',sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column('simplified_view',sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column('use_feedback',sa.Boolean(),nullable=False,server_default=sa.false()),
        sa.Column('ranking_mode',sa.String(20),nullable=False,server_default='adaptive'))
    op.create_table('support_feedback',
        sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('session_id',sa.Integer(),sa.ForeignKey('attack_sessions.id'),nullable=False),
        sa.Column('action_id',sa.String(30),nullable=False),sa.Column('helpful',sa.Boolean(),nullable=False),
        sa.Column('created_at',sa.String(40),nullable=False),
        sa.UniqueConstraint('session_id','action_id',name='one_rating_per_session_action'),
        sa.CheckConstraint("action_id IN ('call_contact','prepare_sms','support_card')",name='nonemergency_feedback_action'))
def downgrade():
    raise RuntimeError('Export and review support preferences and feedback before a data-losing downgrade.')
