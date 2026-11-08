import json
import pytest
import ckan.plugins.toolkit as tk
import ckan.plugins as plugins
from ckan.tests import factories
from uuid import uuid4

# Spatial_metadata is required due to the spatial_query.html snippet being included in the search
pytestmark = pytest.mark.ckan_config(
    "ckan.plugins",
    "mwlr_datastore bsi_restricted_resources spatial_metadata",
)


@pytest.fixture
def searchable_dataset(with_plugins, clean_db, clean_index):
    assert plugins.plugin_loaded("bsi_restricted_resources")

    organisation = factories.Organization()
    dataset = factories.Dataset(
        private=False,
        owner_org=organisation["id"],
    )

    public_resource = factories.Resource(
        package_id=dataset["id"],
        name="public_resource",
        resource_access_level="dataset_access_level",
    )

    private_resource_name_id = uuid4().hex

    private_resource_name = f"restricted_name_{private_resource_name_id}"
    private_resource_description = f"restricted_description_{private_resource_name_id}"
    private_resource_url = f"https://example.invalid/restricted_file_{private_resource_name_id}.csv"

    private_resource = factories.Resource(
        package_id=dataset["id"],
        name=private_resource_name,
        description=private_resource_description,
        url=private_resource_url,
        resource_access_level="restrict_to_creator",
    )

    searchable_dataset_dictionary = {
        "dataset_id": dataset["id"],
        "dataset_name": dataset["name"],
        "public_resource": public_resource,
        "private_resource": private_resource,
        "restricted_values": [
            private_resource_name,
            private_resource_description,
            private_resource_url,
        ],
    }

    return searchable_dataset_dictionary


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


def test_resource_search_masks_restricted_resource_metadata(app, searchable_dataset):
    resource_search_url = tk.url_for(
        "api.action",
        ver=3,
        logic_function="resource_search",
        query=f"name:{searchable_dataset['private_resource']['name']}",
    )
    response = app.get(resource_search_url)

    assert response.status_code == 200
    payload = response.json
    assert payload["success"] is True

    results = payload["result"]["results"]
    assert len(results) == 1, "The private resource must be present in the search results."

    search_result_private_resource = results[0]
    assert search_result_private_resource["id"] == searchable_dataset["private_resource"]["id"]

    serialised_result = json.dumps(search_result_private_resource)

    for value in searchable_dataset["restricted_values"]:
        assert value not in serialised_result, f"resource_search exposed restricted resource metadata: {value!r}"
