"""update review types column

Revision ID: 1009b3306198
Revises: 3e2270b91fbb
Create Date: 2026-05-10 20:26:47.178646

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1009b3306198'
down_revision = '3e2270b91fbb'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'review_comments',
        'review_type',
        new_column_name='review_types'
    )


def downgrade():
    op.alter_column(
        'review_comments',
        'review_types',
        new_column_name='review_type'
    )
