"""Add accounts without claiming or deleting legacy health records."""
from alembic import op
import sqlalchemy as sa

revision = '005'
down_revision = '004'
HEALTH = ('episodes','wellness','early_symptoms','contacts','profiles','attack_sessions','support_preferences','support_feedback')

def upgrade():
    op.create_table('users',sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('email',sa.String(254),nullable=False,unique=True),
        sa.Column('display_name',sa.String(100),nullable=False),
        sa.Column('password_hash',sa.String(300),nullable=False),sa.Column('created_at',sa.String(40),nullable=False))
    op.create_table('login_sessions',sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('user_id',sa.Integer(),sa.ForeignKey('users.id'),nullable=True),
        sa.Column('token_digest',sa.String(64),nullable=False,unique=True),
        sa.Column('csrf_token',sa.String(100),nullable=False),sa.Column('expires_at',sa.String(40),nullable=False))
    op.create_index('ix_login_sessions_user_id','login_sessions',['user_id'])
    op.create_index('ix_login_sessions_expires_at','login_sessions',['expires_at'])
    naming={'uq':'uq_%(table_name)s_%(column_0_name)s'}
    for table in HEALTH:
        uniques=sa.inspect(op.get_bind()).get_unique_constraints(table)
        with op.batch_alter_table(table,naming_convention=naming) as batch:
            batch.add_column(sa.Column('owner_id',sa.Integer(),nullable=True))
            batch.create_foreign_key('fk_'+table+'_owner','users',['owner_id'],['id'])
            batch.create_index('ix_'+table+'_owner_id',['owner_id'])
            old='date' if table=='wellness' else 'active_slot' if table=='attack_sessions' else None
            if old:
                for constraint in uniques:
                    if constraint['column_names']==[old]:
                        batch.drop_constraint(constraint['name'] or f'uq_{table}_{old}',type_='unique')
                batch.create_unique_constraint('wellness_owner_date' if table=='wellness' else 'session_owner_active',['owner_id',old])
            if table in ('profiles','support_preferences'):
                batch.create_unique_constraint(table+'_owner',['owner_id'])
    op.create_table('sharing_consents',sa.Column('id',sa.Integer(),primary_key=True),
        sa.Column('owner_id',sa.Integer(),sa.ForeignKey('users.id'),nullable=True),
        sa.Column('contact_id',sa.Integer(),sa.ForeignKey('contacts.id',ondelete='SET NULL'),nullable=True),
        sa.Column('scope',sa.String(30),nullable=False),sa.Column('granted_at',sa.String(40),nullable=False),
        sa.Column('revoked_at',sa.String(40),nullable=True))
    op.create_index('ix_sharing_consents_owner_id','sharing_consents',['owner_id'])

def downgrade():
    raise RuntimeError('Downgrade would remove account ownership. Back up and review data before changing authentication schemas.')
