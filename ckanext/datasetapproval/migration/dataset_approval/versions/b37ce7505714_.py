"""empty message

Revision ID: b37ce7505714
Revises: 096e618c5fb8
Create Date: 2026-04-28 04:32:29.294302

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b37ce7505714'
down_revision = '096e618c5fb8'
branch_labels = None
depends_on = None


def upgrade():
    # Removes the column named 'my_column' from 'my_table'
    op.drop_column('review_comments', 'compliance_status')

def downgrade():
    # Restore the column if you need to roll back
    op.add_column('review_comments', sa.Column('compliance_status', sa.UnicodeText(), nullable=True))
