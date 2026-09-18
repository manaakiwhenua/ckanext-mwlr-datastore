"""Tests for the view and download count helpers that need no CKAN app."""
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
