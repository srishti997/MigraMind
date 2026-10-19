from alembic import op
import sqlalchemy as sa
revision = '003'
down_revision = '002'
def upgrade():
    with op.batch_alter_table('episodes') as batch:
        batch.alter_column('severity', existing_type=sa.Integer(), nullable=True)
        batch.alter_column('duration', existing_type=sa.Integer(), nullable=True)
        for column in [sa.Column('started_at',sa.String(40)),sa.Column('ended_at',sa.String(40)),sa.Column('timezone_name',sa.String(100)),sa.Column('pain_location',sa.String(200),nullable=False,server_default=''),sa.Column('symptoms',sa.JSON(),nullable=False,server_default='[]'),sa.Column('functional_impact',sa.String(100),nullable=False,server_default=''),sa.Column('medications',sa.JSON(),nullable=False,server_default='[]'),sa.Column('attack_session_id',sa.Integer())]: batch.add_column(column)
    op.create_table('wellness',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('date',sa.String(10),nullable=False,unique=True),sa.Column('timezone_name',sa.String(100),nullable=False),sa.Column('recorded_at',sa.String(40),nullable=False),sa.Column('sleep_hours',sa.Float()),sa.Column('sleep_quality',sa.Integer()),sa.Column('stress',sa.Integer()),sa.Column('hydration_ml',sa.Integer()),sa.Column('missed_meals',sa.Boolean()),sa.Column('screen_hours',sa.Float()),sa.Column('menstrual_notes',sa.Text()))
    op.create_table('early_symptoms',sa.Column('id',sa.Integer(),primary_key=True),sa.Column('symptom',sa.String(200),nullable=False),sa.Column('onset_at',sa.String(40),nullable=False),sa.Column('timezone_name',sa.String(100),nullable=False),sa.Column('recorded_at',sa.String(40),nullable=False),sa.Column('notes',sa.Text(),nullable=False))
def downgrade():
    # Deliberately non-destructive: advanced records may contain unknown severity/duration.
    raise RuntimeError('Export and review Sprint 3 data before an explicit downgrade; automatic data loss is disabled.')
