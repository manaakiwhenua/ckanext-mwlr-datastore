"""Tests for the extension's config declarations (MWDS-536).

Run against a CKAN with this extension installed:

    pytest --ckan-ini=test.ini ckanext/mwlr_datastore
"""
import pytest

import ckan.plugins.toolkit as toolkit
from ckan.common import config_declaration

EMAIL = "ckan.datastore.data_management_email"


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("with_plugins")
@pytest.mark.parametrize("key", [
    "ckanext.mwlr_datastore.readiness_path",
    "ckanext.mwlr_datastore.whats_new_path",
    "ckanext.mwlr_datastore.environment",
    EMAIL,
])
def test_options_are_declared(key):
    """An undeclared option logs "Option ... is not declared" on every read."""
    assert key in config_declaration


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("with_plugins")
@pytest.mark.parametrize("value", [None, ""])
def test_data_management_email_is_required(value):
    """Missing or empty, CKAN 2.11+ refuses to start, rather than serve the
    mailto:unknown link production once rendered."""
    settings = {k: v for k, v in toolkit.config.items() if k != EMAIL}
    if value is not None:
        settings[EMAIL] = value
    _, errors = config_declaration.validate(settings)
    assert EMAIL in {str(key) for key in errors}


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.ckan_config(EMAIL, "data-team@example.org")
@pytest.mark.usefixtures("with_plugins", "with_request_context")
def test_resource_help_links_the_configured_address():
    html = toolkit.render("package/snippets/resource_help.html")
    assert 'href="mailto:data-team@example.org"' in html
