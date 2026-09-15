"""Tests for the extension's base template (MWDS-385).

Run against a CKAN with this extension installed:

    pytest --ckan-ini=test.ini ckanext/mwlr_datastore
"""
import re

import pytest


def _html_lang(app):
    page = app.get("/terms_of_use", status=200).body
    return re.search(r'<html lang="([^"]*)"', page).group(1)


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.ckan_config("ckan.locale_default", "en_GB")
@pytest.mark.usefixtures("with_plugins")
def test_html_lang_is_a_language_tag_not_a_locale(app):
    """A region must be joined with a hyphen, or browsers and screen readers
    do not recognise the language. en_GB ships with CKAN; en_NZ behaves the same."""
    assert _html_lang(app) == "en-GB"


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("with_plugins")
def test_html_lang_without_a_region_is_unchanged(app):
    assert _html_lang(app) == "en"
