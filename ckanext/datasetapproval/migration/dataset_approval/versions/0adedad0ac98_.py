"""empty message

Revision ID: 0adedad0ac98
Revises: b37ce7505714
Create Date: 2026-05-04 23:51:50.555696

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0adedad0ac98'
down_revision = 'b37ce7505714'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column(
        'review_comments',
        'rejection_reason',
        new_column_name='rejection_reasons'
    )


def downgrade():
    op.alter_column(
        'review_comments',
        'rejection_reasons',
        new_column_name='rejection_reason'
    )
