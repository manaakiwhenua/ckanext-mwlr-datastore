"""Tests for the view and download count helpers that need no CKAN app."""
import ckan
import pytest

from ckanext.mwlr_datastore import tracking


@pytest.mark.parametrize('data,expected', [
    ({'tracking_summary': {'total': 7, 'recent': 2}}, {'total': 7, 'recent': 2}),
    ({'tracking_summary': {}}, {'total': 0, 'recent': 0}),
    ({'tracking_summary': None}, {'total': 0, 'recent': 0}),
    ({}, {'total': 0, 'recent': 0}),
])
def test_summary_defaults_to_zero_when_tracking_is_absent(data, expected):
    assert tracking._summary(data) == expected


@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore")
@pytest.mark.usefixtures("clean_db", "with_plugins")
def test_dataset_page_shows_view_counts_without_tracking(app):
    """The counts moved here from mwlr_tracking (MWDS-389). With tracking off
    the page still renders and shows zeros rather than failing."""
    from ckan.tests import factories

    dataset = factories.Dataset()
    body = app.get(f"/dataset/{dataset['name']}", status=200).body
    assert "Recent views" in body
    assert "Total views" in body



CKAN_2_11 = tuple(int(p) for p in ckan.__version__.split(".")[:2]) >= (2, 11)


@pytest.mark.skipif(not CKAN_2_11, reason="2.10's format_resource_items already leaves tracking_summary out")
@pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore scheming_datasets tracking")
@pytest.mark.ckan_config("scheming.dataset_schemas", "ckanext.scheming:ckan_dataset.yaml")
@pytest.mark.usefixtures("clean_db", "with_plugins")
def test_resource_page_has_no_raw_tracking_summary_row(app):
    """CKAN 2.12's tracking plugin puts tracking_summary on every resource, and
    2.12 no longer leaves it out of the additional information. The counts are
    shown as Recent and Total downloads, so the raw dict must not appear beside
    them (MWDS-488)."""
    from ckan.tests import factories, helpers

    dataset = factories.Dataset()
    resource = factories.Resource(package_id=dataset["id"])
    shown = helpers.call_action("package_show", id=dataset["id"])["resources"][0]
    assert "tracking_summary" in shown, "precondition: the key must reach the page"
    body = app.get(f"/dataset/{dataset['name']}/resource/{resource['id']}", status=200).body
    assert "Total downloads" in body
    assert "Tracking summary" not in body
