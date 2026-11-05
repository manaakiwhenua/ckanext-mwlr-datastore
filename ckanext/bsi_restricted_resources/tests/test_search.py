import json
from ckanext.bsi_restricted_resources.tests.fixtures import searchable_dataset
import pytest
import ckan.plugins.toolkit as tk

# Spatial_metadata is required due to the spatial_query.html snippet being included in the search
pytestmark = pytest.mark.ckan_config(
    "ckan.plugins",
    "mwlr_datastore bsi_restricted_resources spatial_metadata",
)


def test_ui_search_hides_restricted_resource_metadata(app, searchable_dataset):

    dataset_search_url = tk.url_for("dataset.search", q=f"id:{searchable_dataset['dataset_id']}")
    response = app.get(dataset_search_url)

    assert response.status_code == 200
    assert searchable_dataset["dataset_name"] in response.text, "The public dataset must appear in the search results."

    for value in searchable_dataset["restricted_values"]:
        assert value not in response.text, f"UI search exposed restricted resource metadata: {value!r}"


def test_package_search_hides_restricted_resource_metadata(app, searchable_dataset):

    package_search_url = tk.url_for(
        "api.action", ver=3, logic_function="package_search", q=f"id:{searchable_dataset['dataset_id']}"
    )
    response = app.get(package_search_url)

    public_resource_id = searchable_dataset["public_resource"]["id"]
    dataset_id = searchable_dataset["dataset_id"]

    assert response.status_code == 200
    payload = response.json
    assert payload["success"] is True

    results = payload["result"]["results"]
    assert len(results) == 1, "The public dataset must be present in the search results."

    search_result_dataset = results[0]
    assert search_result_dataset["id"] == dataset_id

    search_result_resource_ids = {resource["id"] for resource in search_result_dataset["resources"]}
    assert public_resource_id in search_result_resource_ids, (
        "The public resource must be present in the search results."
    )

    serialised_result = json.dumps(search_result_dataset)

    for value in searchable_dataset["restricted_values"]:
        assert value not in serialised_result, f"package_search exposed restricted resource metadata: {value!r}"
