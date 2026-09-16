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
def test_html_lang_is_one_ckans_javascript_can_load(app):
    """CKAN's JavaScript takes its locale from <html lang> and loads
    /api/i18n/<lang>. If the attribute is not a locale CKAN knows - en-GB rather
    than en_GB - that request fails and no scripted component on the site
    starts. v1.2.0 broke every table preview this way, and CKAN 2.10.11+ does
    the same by default (ckan/ckan#9473); the template pins the locale form."""
    lang = _html_lang(app)
    assert lang == "en_GB"
    app.get(f"/api/i18n/{lang}", status=200)


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("with_plugins")
def test_html_lang_default(app):
    lang = _html_lang(app)
    assert lang == "en"
    app.get(f"/api/i18n/{lang}", status=200)
