"""empty message

Revision ID: 3e2270b91fbb
Revises: 0adedad0ac98
Create Date: 2026-05-06 00:54:11.180891

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3e2270b91fbb'
down_revision = '0adedad0ac98'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('review_comments', 'approval_type')


def downgrade():
    op.add_column('review_comments', sa.Column('approval_type', sa.UnicodeText(), nullable=True))
