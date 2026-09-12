"""Tests for plugin.py.

Run against a CKAN with this extension installed:

    pytest --ckan-ini=test.ini ckanext/mwlr_datastore
"""
import pytest

from ckan.plugins import plugin_loaded


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("with_plugins")
def test_plugin_loads():
    assert plugin_loaded("mwlr_datastore")
