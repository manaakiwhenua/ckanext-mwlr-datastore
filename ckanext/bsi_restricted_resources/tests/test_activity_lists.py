import pytest
import ckan.plugins.toolkit as tk
import ckan.plugins as plugins
from ckanext.bsi_restricted_resources.tests.access_scenario_helpers import (
    ALL_ACCESS_SCENARIOS,
    ACCESS_PARAMETERS,
    get_resource_data_that_should_be_masked,
)
import json

# These tests require the 'activity' plugin to be enabled
pytestmark = pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore bsi_restricted_resources tracking activity")

# Failing API endpoints that need addressing
# recently_changed_packages_activity_list
# organization_activity_list


@pytest.mark.parametrize(ACCESS_PARAMETERS, ALL_ACCESS_SCENARIOS)
def test_current_package_list_with_resources_masks_restricted_resources(app, access_scenario):

    assert plugins.plugin_loaded("activity"), "Test setup failed: activity plugin is not loaded."

    dataset = access_scenario["dataset"]
    resource = access_scenario["resource"]
    user = access_scenario["user"]
    user_is_sysadmin = True if user and user.get("sysadmin") else False
    dataset_is_public = not dataset.get("private")

    unmasked_resource_data = get_resource_data_that_should_be_masked(resource)
    assert any(unmasked_resource_data), "Test setup failed: there is no unmasked resource data to check"

    headers = {"Authorization": user["token"]} if user else {}
    resource_api_url = tk.url_for("api.action", ver=3, logic_function="current_package_list_with_resources")
    response = app.get(resource_api_url, headers=headers)
    assert response.status_code == 200

    result = response.json["result"]
    result_dataset = next((dataset_item for dataset_item in result if dataset_item["id"] == dataset["id"]), None)

    # From my manual UI testing, only sysadmins can access private datasets on the 'current_package_list_with_resources' endpoint. Do an early return if the dataset is not expected in the result.
    dataset_expected_in_result = user_is_sysadmin or dataset_is_public
    assert (result_dataset is not None) == dataset_expected_in_result

    if result_dataset is None:
        return

    returned_resource = next((r for r in result_dataset["resources"] if r["id"] == resource["id"]), None)
    assert returned_resource is not None, "The resource must be listed, even when masked"

    serialised_result = json.dumps(result_dataset)

    if user_is_sysadmin or (access_scenario["user_has_resource_access"] and dataset_is_public):
        for value in unmasked_resource_data:
            assert not returned_resource.get("resource_is_masked")
            assert value in serialised_result
    else:
        for value in unmasked_resource_data:
            assert returned_resource.get("resource_is_masked") is True
            assert value not in serialised_result


@pytest.mark.parametrize(ACCESS_PARAMETERS, ALL_ACCESS_SCENARIOS)
def test_package_activity_list_masks_restricted_resources(app, access_scenario):

    assert plugins.plugin_loaded("activity"), "Test setup failed: activity plugin is not loaded."

    unmasked_resource_data = get_resource_data_that_should_be_masked(access_scenario["resource"])
    assert any(unmasked_resource_data), "Test setup failed: there is no unmasked resource data to check"

    headers = {"Authorization": access_scenario["user"]["token"]} if access_scenario["user"] else {}
    resource_api_url = tk.url_for(
        "api.action", ver=3, logic_function="package_activity_list", id=access_scenario["dataset"]["id"]
    )
    response = app.get(resource_api_url, headers=headers)

    if access_scenario["user_has_dataset_access"]:
        assert response.status_code == 200
    else:
        assert response.status_code == 403
        return

    # A dataset can have multiple activities, including 'new package' and 'changed package' activities
    activity_list = response.json["result"]
    activities = [
        item["data"]["package"]
        for item in activity_list
        if item
        and "package" in item.get("data", {})
        and item["data"]["package"]["id"] == access_scenario["dataset"]["id"]
    ]

    returned_resources = [
        resource
        for dataset in activities
        for resource in dataset.get("resources", [])
        if resource["id"] == access_scenario["resource"]["id"]
    ]

    assert returned_resources, "At least one activity must contain the resource"

    for returned_resource in returned_resources:
        serialised = json.dumps(returned_resource)
        for value in unmasked_resource_data:
            if access_scenario["user_has_resource_access"]:
                assert value in serialised
            else:
                assert value not in serialised
