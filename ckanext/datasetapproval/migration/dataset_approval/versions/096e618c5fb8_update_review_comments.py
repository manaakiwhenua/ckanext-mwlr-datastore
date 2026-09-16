"""update_review_comments

Revision ID: 096e618c5fb8
Revises: 6281c5dccb05
Create Date: 2026-04-08 09:31:53.577055

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '096e618c5fb8'
down_revision = '6281c5dccb05'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('review_comments', sa.Column('approval_details', sa.UnicodeText(), nullable=True))
    op.add_column('review_comments', sa.Column('condition_expiry_date', sa.DateTime(), nullable=True))


def downgrade():
    op.drop_column('review_comments', 'approval_details')
    op.drop_column('review_comments', 'condition_expiry_date')
