import json
import pytest
import ckan.plugins.toolkit as tk
from ckanext.bsi_restricted_resources.tests.access_scenario_helpers import (
    ACCESS_PARAMETERS,
    ALL_ACCESS_SCENARIOS,
    get_resource_data_that_should_be_masked,
)

# Spatial_metadata is required due to the spatial_query.html snippet being included in the search
pytestmark = pytest.mark.ckan_config(
    "ckan.plugins",
    "mwlr_datastore bsi_restricted_resources spatial_metadata",
)


@pytest.mark.parametrize(ACCESS_PARAMETERS, ALL_ACCESS_SCENARIOS)
def test_ui_search_hides_restricted_resource_metadata(app, access_scenario):

    dataset = access_scenario["dataset"]
    headers = {"Authorization": access_scenario["user"]["token"]} if access_scenario["user"] else {}
    dataset_search_url = tk.url_for("dataset.search", q=f"id:{dataset['id']}")
    response = app.get(dataset_search_url, headers=headers)

    assert response.status_code == 200

    if access_scenario["user_has_dataset_access"]:
        assert dataset["name"] in response.text, "The public dataset must appear in the search results."
    else:
        assert dataset["name"] not in response.text, (
            "The private dataset must not appear in the search results for users without access."
        )

    if not access_scenario["user_has_resource_access"]:
        for resource in dataset["resources"]:
            resource_data = get_resource_data_that_should_be_masked(resource)
            for value in resource_data:
                assert value not in response.text, f"UI search exposed restricted resource metadata: {value!r}"


@pytest.mark.parametrize(ACCESS_PARAMETERS, ALL_ACCESS_SCENARIOS)
def test_package_search_hides_restricted_resource_metadata(app, access_scenario):

    package_search_url = tk.url_for(
        "api.action",
        ver=3,
        logic_function="package_search",
        q=f"id:{access_scenario['dataset']['id']}",
        include_private=True,
    )

    headers = {"Authorization": access_scenario["user"]["token"]} if access_scenario["user"] else {}
    response = app.get(package_search_url, headers=headers)

    resource = access_scenario["resource"]
    dataset_id = access_scenario["dataset"]["id"]
    user_has_resource_access = access_scenario["user_has_resource_access"]
    user_has_dataset_access = access_scenario["user_has_dataset_access"]

    assert response.status_code == 200
    payload = response.json
    assert payload["success"] is True

    # Users without access should not see private datasets in the search results.
    if not user_has_dataset_access:
        results = payload["result"]["results"]
        assert len(results) == 0, "The dataset must not be present in the search results for users without access."
        return

    results = payload["result"]["results"]
    assert len(results) == 1, "The dataset must be present in the search results."

    search_result_dataset = results[0]
    assert search_result_dataset["id"] == dataset_id

    search_result_resource_ids = {resource["id"] for resource in search_result_dataset["resources"]}
    assert resource["id"] in search_result_resource_ids, "The resource ids must be present in the search results."

    serialised_result = json.dumps(search_result_dataset)
    resource_data = get_resource_data_that_should_be_masked(resource)

    # Users with access should see private datasets and their resources in the search results.
    if user_has_resource_access:
        for value in resource_data:
            assert value in serialised_result, f"Users with access should see: {value!r}"
    # Users without access should see non-private datasets but not the restricted resource metadata.
    else:
        for value in resource_data:
            assert value not in serialised_result, f"package_search exposed restricted resource metadata: {value!r}"


@pytest.mark.parametrize(ACCESS_PARAMETERS, ALL_ACCESS_SCENARIOS)
def test_resource_search_masks_restricted_resource_metadata(app, access_scenario):

    resource = access_scenario["resource"]
    user_has_resource_access = access_scenario["user_has_resource_access"]
    user_has_dataset_access = access_scenario["user_has_dataset_access"]
    dataset_is_private = access_scenario["dataset"]["private"]

    resource_search_url = tk.url_for(
        "api.action",
        ver=3,
        logic_function="resource_search",
        query=f"name:{resource['name']}",
    )
    headers = {"Authorization": access_scenario["user"]["token"]} if access_scenario["user"] else {}
    response = app.get(resource_search_url, headers=headers)

    assert response.status_code == 200
    payload = response.json
    assert payload["success"] is True

    # Resource search prevents all resource access for resources in private datasets, even for users who would otherwise have access.
    if dataset_is_private:
        results = payload["result"]["results"]
        assert len(results) == 0, "The resource must not be present in the search results for private datasets."
        return

    if not user_has_dataset_access:
        results = payload["result"]["results"]
        assert len(results) == 0, "The resource must not be present in the search results for users without access."
        return

    results = payload["result"]["results"]
    assert len(results) == 1, "The resource must be present in the search results."
    search_result_resource = results[0]
    assert search_result_resource["id"] == resource["id"]

    serialised_result = json.dumps(search_result_resource)
    resource_data = get_resource_data_that_should_be_masked(resource)

    # Users with access should see resource metadata in the search results.
    if user_has_resource_access:
        for value in resource_data:
            assert value in serialised_result, f"Users with access should see: {value!r}"
    # Users without access should see non-private datasets but not the restricted resource metadata.
    else:
        for value in resource_data:
            assert value not in serialised_result, f"resource_search exposed restricted resource metadata: {value!r}"
