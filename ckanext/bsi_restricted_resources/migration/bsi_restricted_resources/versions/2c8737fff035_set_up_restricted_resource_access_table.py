"""set up restricted resource access table

Revision ID: 2c8737fff035
Revises: 
Create Date: 2026-09-23 21:03:54.957785

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '2c8737fff035'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'restricted_resource_access',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('resource_id', sa.UnicodeText(), sa.ForeignKey('resource.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.UnicodeText(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('granted_by_user_id', sa.UnicodeText(), sa.ForeignKey('user.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('resource_id', 'user_id', name='uq_resource_user')        
    )

def downgrade():
    op.drop_table('restricted_resource_access')