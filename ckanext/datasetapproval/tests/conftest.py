import pytest
import uuid
from ckan.model import Repository
import ckan.model.meta as meta
import sqlalchemy as sa
from sqlalchemy import MetaData, Table, inspect
from sqlalchemy.orm import close_all_sessions
from ckan.tests import factories
import ckan.plugins.toolkit as tk

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
    migrate_db_for('dataset_approval')


@pytest.fixture()
@pytest.mark.ckan_config("ckan.plugins", "dataset_approval")
def standard_plugins_config(ckan_config):
    pass


@pytest.fixture()
def standard_plugins(standard_plugins_config, with_plugins):
    pass

@pytest.fixture()
def make_basic_data_dict():
    def _make_basic_data_dict(org_id):
        data = {
            "name": f"dataset-{uuid.uuid4().hex[:8]}",
            "title": "Basic Dataset",
            "owner_org": org_id,
            "private": "true",
            "publisher": "New Zealand Institute for Bioeconomy Science",
            "publication_year": "2026",
            "publishing_status": "in_progress",
            "chosen_visibility": "false",
            "author":"Test Author",
            "author_email": "author@example.com",
            "maintainer": "Test Maintainer",
            "maintainer_email": "maintainer@email.com",
            "notes": "Testing Notes...",
            "ethics_security_risk_review_required": "false",
            "intellectual_property_review_required": "false",
            "scientific_technical_review_required": "false",
            "te_ao_māori_review_required": "false",
        }
        return data
    return _make_basic_data_dict

@pytest.fixture()
def org_with_editor():
    user = factories.User()
    users = [{"name": user["name"], "capacity": "editor"}]
    organization = factories.Organization(users=users)

    return organization, user


@pytest.fixture()
def org_with_admin():
    user = factories.User()
    users = [{"name": user["name"], "capacity": "admin"}]
    organization = factories.Organization(users=users)

    return organization, user


@pytest.fixture()
# creates a basic dataset (with chosen visibility of "false"(public)) given whether user is an admin or editor
def make_dataset(make_basic_data_dict):
    def _make_dataset(org_id, user, submit_review=False, admin_editing=False, **overrides):
        
        data = make_basic_data_dict(org_id)

        data.update(overrides)
        

        # editor simply creating dataset, so not submitting for review
        context = {
            "user": user["name"],
            "submit_review": submit_review,
            "admin_editing": admin_editing,
        }
        logger.debug(f"data and context\ndata: {data}\ncontext: {context}")

        return tk.get_action("package_create")(
            context,
            data
        )

    return _make_dataset