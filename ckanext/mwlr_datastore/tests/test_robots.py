"""The robots.txt override (MWDS-438).

Run against a CKAN with this extension installed:

    pytest --ckan-ini=test.ini ckanext/mwlr_datastore
"""
import pytest

FACET_PARAMS = [
    "organization",
    "groups",
    "tags",
    "res_format",
    "license_id",
    "vocab_author",
    "sort",
]


def _robots(app):
    return app.get("/robots.txt", status=200).body


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("with_plugins")
def test_every_facet_parameter_is_disallowed(app):
    """The facet space is what a crawler walks: the five facets in
    search.facets, vocab_author which this extension adds, and sort. They
    combine with each other and with paging, so the crawlable space is
    effectively unbounded (PE-600)."""
    body = _robots(app)
    for param in FACET_PARAMS:
        assert f"Disallow: /*?*{param}=" in body, param


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("with_plugins")
def test_the_catalogue_stays_crawlable(app):
    """Datasets must stay indexable, and paging is how a crawler reaches the
    ones past the first page - CKAN publishes no sitemap. A bare `Disallow:
    /dataset` or a rule on `page=` would leave them allowed but unreachable."""
    body = _robots(app)
    assert "Disallow: /dataset\n" not in body
    assert "Disallow: /dataset/\n" not in body
    assert "page=" not in body


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("with_plugins")
def test_ckans_own_rules_survive(app):
    """The override extends CKAN's template rather than replacing it, so the
    stock rules and the crawl delay are still there."""
    body = _robots(app)
    for line in ("Disallow: /api/", "Disallow: /dataset/rate/", "Crawl-Delay: 10"):
        assert line in body, line
