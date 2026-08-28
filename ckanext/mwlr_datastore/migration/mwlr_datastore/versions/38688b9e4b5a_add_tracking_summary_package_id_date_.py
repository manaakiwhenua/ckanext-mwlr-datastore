"""add tracking_summary package_id/date composite index

Creating a dataset makes CKAN index it, and indexing calls
ckan.model.tracking.TrackingSummary.get_for_package, which filters on
package_id but orders by tracking_date DESC LIMIT 1.

Without a composite index the planner satisfies the ordering with
tracking_summary_date and applies package_id as a filter afterwards. A brand
new dataset has no tracking rows, so nothing matches and the whole table is
scanned and discarded - 54 seconds against 5.6M rows, and it grows with the
table. See PE-431.

Revision ID: 38688b9e4b5a
Revises:
Create Date: 2026-08-28 00:35:20.849716

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = '38688b9e4b5a'
down_revision = None
branch_labels = None
depends_on = None

INDEX_NAME = 'tracking_summary_package_id_date'


def upgrade():
    # CONCURRENTLY cannot run inside a transaction and Alembic wraps
    # migrations in one, so step outside it. Without this the index build
    # takes an ACCESS EXCLUSIVE lock, blocking writes for the length of the
    # build - on a multi-million row table that is a stall at every startup.
    with op.get_context().autocommit_block():
        op.execute(
            'CREATE INDEX CONCURRENTLY IF NOT EXISTS {} '
            'ON tracking_summary (package_id, tracking_date DESC)'.format(INDEX_NAME)
        )


def downgrade():
    with op.get_context().autocommit_block():
        op.execute('DROP INDEX CONCURRENTLY IF EXISTS {}'.format(INDEX_NAME))
