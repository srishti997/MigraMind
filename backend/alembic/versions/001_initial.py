from alembic import op
import sqlalchemy as sa
revision = '001'
down_revision = None
def upgrade():
    op.create_table('episodes',sa.Column('id',sa.Integer,primary_key=True),sa.Column('date',sa.String(10),nullable=False),sa.Column('severity',sa.Integer,nullable=False),sa.Column('duration',sa.Integer,nullable=False),sa.Column('trigger',sa.String(100),nullable=False),sa.Column('notes',sa.Text,nullable=False))
    op.create_table('contacts',sa.Column('id',sa.Integer,primary_key=True),sa.Column('name',sa.String(100),nullable=False),sa.Column('relationship',sa.String(100),nullable=False),sa.Column('phone',sa.String(32),nullable=False))
    op.create_table('profiles',sa.Column('id',sa.Integer,primary_key=True),sa.Column('name',sa.String(100),nullable=False),sa.Column('support',sa.Text,nullable=False),sa.Column('avoid',sa.Text,nullable=False))
def downgrade():
    for table in ['profiles','contacts','episodes']: op.drop_table(table)
