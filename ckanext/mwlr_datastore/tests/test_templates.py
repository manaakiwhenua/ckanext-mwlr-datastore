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


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("with_plugins")
def test_html_tag_carries_the_js_class(app):
    """CKAN's stylesheet hides and shows components under ".js ..." rules. 2.10
    added the class from JavaScript; 2.12 writes it into <html>, which this
    extension overrides, so the override must keep it (MWDS-483)."""
    page = app.get("/terms_of_use", status=200).body
    tag = re.search(r'<html lang="[^"]*"[^>]*>', page).group(0)
    assert re.search(r'class="[^"]*\bjs\b', tag), tag


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore stats")
@pytest.mark.usefixtures("clean_db", "with_plugins")
def test_stats_menu_starts_on_the_first_section(app):
    """Bootstrap 5 hides the previous section by finding the active menu link.
    With none marked active, every section clicked stays on screen (MWDS-483)."""
    page = app.get("/stats", status=200).body
    links = re.findall(r'<a href="#stats-[^"]+"[^>]*>', page)
    assert links, "stats menu not rendered"
    assert 'class="active"' in links[0]
    assert all('class="active"' not in link for link in links[1:])
