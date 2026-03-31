"""Add review action table

Revision ID: 6281c5dccb05
Revises: bd1fb1967d43
Create Date: 2026-03-31 01:09:34.808655

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6281c5dccb05'
down_revision = 'bd1fb1967d43'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('review_comments',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('dataset_id', sa.UnicodeText(), sa.ForeignKey('package.id'), nullable=False),
    sa.Column('review_action_id', sa.UnicodeText(), sa.ForeignKey('review_action.id'), nullable=False),
    sa.Column('compliance_status', sa.UnicodeText(), nullable=True),
    sa.Column('rejection_reason', sa.UnicodeText(), nullable=True),
    sa.Column('rejection_reason_comments', sa.UnicodeText(), nullable=True),
    sa.Column('resubmission_comments', sa.UnicodeText(), nullable=True),
    sa.Column('approval_outcome', sa.UnicodeText(), nullable=True),
    sa.Column('approval_outcome_comments', sa.UnicodeText(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('review_comments')
