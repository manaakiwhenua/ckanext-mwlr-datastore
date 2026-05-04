import pytest

from ckan.model import Repository
import ckan.model.meta as meta
import sqlalchemy as sa
from sqlalchemy import MetaData, Table, inspect
from sqlalchemy.orm import close_all_sessions

import logging
from typing import Any, Dict, List, Tuple, Optional
import warnings

logger = logging.getLogger(__name__)

preserved_tables = [
    'spatial_ref_sys',
]

avoid_deleting_tables = []

class CustomRepository(Repository):
    '''
    based on https://github.com/ckan/ckan/blob/243de661bc9979e57e1afe33a5d47a64fb227c91/ckan/model/__init__.py
         and https://github.com/ckan/ckan/blob/243de661bc9979e57e1afe33a5d47a64fb227c91/ckan/tests/pytest_ckan/fixtures.py#L314
    but this one does not drop all tables
    '''

    def clean_db(self) -> None:
        logger.warning("Cleaning DB fixture!")
        self.commit_and_remove()
        meta.metadata = MetaData()

        engine = meta.engine

        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', '.*(reflection|tsvector).*')
            meta.metadata.reflect(engine)

        with engine.begin() as conn:
            tables = reversed(meta.metadata.sorted_tables)
            # filter out postgis' spatial_ref_sys table
            tables = [
                table for table in tables if table.name not in preserved_tables
            ]
            meta.metadata.drop_all(conn, tables=tables)

        self.tables_created_and_initialised = False
        logger.info('Database tables dropped')

    def delete_all(self) -> None:
        '''Delete all data from all tables.'''
        # raise RuntimeError('delete_all is not supported')

        self.session.remove()
        ## use raw connection for performance
        connection: Any = self.session.connection()
        inspector = sa.inspect(connection)
        tables = reversed(self.metadata.sorted_tables)
        for table in tables:
            # `alembic_version` contains current migration version of the
            # DB. If we drop this information, next attempt to apply migrations
            # will fail. Don't worry about `<PLUGIN>_alembic_version` tables
            # created by extensions - CKAN metadata does not track them, so
            # they'll never appear in this list.
            if table.name in preserved_tables \
                    or table.name in avoid_deleting_tables \
                    or table.name == "alembic_version":
                continue

            # if custom model imported without migrations applied,
            # corresponding table can be missing from DB
            if not inspector.has_table(table.name):
                continue
            logger.info(f'Deleting table {table.name}')
            connection.execute(sa.delete(table))
        self.session.commit()
        logger.info('Database table data deleted')


repo = CustomRepository(meta.metadata, meta.Session)


@pytest.fixture(scope=u"session")
def reset_db():
    logger.warning("Cleaning DB fixture!")

    def reset_db_inner():
        close_all_sessions()
        repo.rebuild_db()

    return reset_db_inner


@pytest.fixture()
def clean_db(reset_db, migrate_db_for):
    reset_db()
    logger.warning("Cleaning DB fixture!")
    migrate_db_for('mnc_data')


@pytest.fixture()
@pytest.mark.ckan_config("ckan.plugins", "mnc_data")
def standard_plugins_config(ckan_config):
    pass


@pytest.fixture()
def standard_plugins(standard_plugins_config, with_plugins):
    pass