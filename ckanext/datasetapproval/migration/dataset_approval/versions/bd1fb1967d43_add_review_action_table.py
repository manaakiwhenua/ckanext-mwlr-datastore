"""Add reviewer decision table

Revision ID: bd1fb1967d43
Revises: 
Create Date: 2026-03-26 20:50:21.823437

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'bd1fb1967d43'
down_revision = None
branch_labels = None
depends_on = None
    
def upgrade():
    op.create_table('review_action',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('dataset_id', sa.UnicodeText(), sa.ForeignKey('package.id'), nullable=False, index=True),
    sa.Column('reviewer_action', sa.UnicodeText(), nullable=True),
    sa.Column('reviewer_email', sa.UnicodeText(), nullable=True),
    sa.Column('reviewer_name', sa.UnicodeText(), nullable=True),
    sa.Column('review_date', sa.DateTime(), nullable=True),
    sa.Column('submitted_date', sa.DateTime(timezone=True), nullable=True),
    sa.Column('submitted_by_user_id', sa.UnicodeText(), sa.ForeignKey('user.id'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('review_action')
