import pytest
import ckan.plugins.toolkit as tk
import ckan.plugins as plugins
from ckanext.bsi_restricted_resources.tests.access_scenario_helpers import (
    ALL_ACCESS_SCENARIOS,
    ACCESS_PARAMETERS,
    get_resource_data_that_should_be_masked,
)
import json
from ckan.tests import helpers
from ckanext.bsi_restricted_resources.types import (
    ResourceAccessLevel,
    UserType,
)

pytestmark = pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore bsi_restricted_resources tracking activity")


def check_activity_plugin_loaded():
    assert plugins.plugin_loaded("activity"), "Test setup failed: activity plugin is not loaded."


def get_unmasked_resource_data(resource):
    unmasked_resource_data = get_resource_data_that_should_be_masked(resource)
    assert unmasked_resource_data and all(unmasked_resource_data), (
        "Test setup failed: there is no unmasked resource data to check"
    )
    return unmasked_resource_data


def create_url_with_headers(user, logic_function, **kwargs):
    headers = {"Authorization": user["token"]} if user else {}
    url = tk.url_for("api.action", ver=3, logic_function=logic_function, **kwargs)
    return url, headers


@pytest.mark.parametrize(ACCESS_PARAMETERS, ALL_ACCESS_SCENARIOS)
def test_current_package_list_with_resources_masks_restricted_resources(app, access_scenario):

    check_activity_plugin_loaded()
    dataset = access_scenario["dataset"]
    resource = access_scenario["resource"]
    user = access_scenario["user"]
    user_is_sysadmin = True if user and user.get("sysadmin") else False
    dataset_is_public = not dataset.get("private")

    unmasked_resource_data = get_unmasked_resource_data(resource)

    resource_api_url, headers = create_url_with_headers(user, "current_package_list_with_resources")
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

    check_activity_plugin_loaded()
    unmasked_resource_data = get_unmasked_resource_data(access_scenario["resource"])
    resource_api_url, headers = create_url_with_headers(
        access_scenario["user"], "package_activity_list", id=access_scenario["dataset"]["id"]
    )
    response = app.get(resource_api_url, headers=headers)

    if access_scenario["user_has_dataset_access"]:
        assert response.status_code == 200
    else:
        assert response.status_code == 403
        return

    returned_resources = get_returned_resources_from_activity_list(
        response.json["result"], access_scenario["dataset"]["id"], access_scenario["resource"]["id"]
    )

    check_returned_resources_against_user_resource_access(
        returned_resources, unmasked_resource_data, access_scenario["user_has_resource_access"]
    )


@pytest.mark.parametrize(ACCESS_PARAMETERS, ALL_ACCESS_SCENARIOS)
def test_recently_changed_packages_activity_list_masks_restricted_resources(app, access_scenario):

    check_activity_plugin_loaded()
    unmasked_resource_data = get_unmasked_resource_data(access_scenario["resource"])

    resource_api_url, headers = create_url_with_headers(
        access_scenario["user"], "recently_changed_packages_activity_list"
    )
    response = app.get(resource_api_url, headers=headers)
    assert response.status_code == 200 and response.json["result"] is not None

    if access_scenario["user_has_dataset_access"]:
        assert len(response.json["result"]) > 0
    else:
        assert len(response.json["result"]) == 0
        return

    returned_resources = get_returned_resources_from_activity_list(
        response.json["result"], access_scenario["dataset"]["id"], access_scenario["resource"]["id"]
    )

    check_returned_resources_against_user_resource_access(
        returned_resources, unmasked_resource_data, access_scenario["user_has_resource_access"]
    )


@pytest.mark.parametrize(ACCESS_PARAMETERS, ALL_ACCESS_SCENARIOS)
def test_organization_activity_list_masks_restricted_resources(app, access_scenario):

    check_activity_plugin_loaded()
    unmasked_resource_data = get_unmasked_resource_data(access_scenario["resource"])
    organisation_id = access_scenario["dataset"]["owner_org"]

    resource_api_url, headers = create_url_with_headers(
        access_scenario["user"], "organization_activity_list", id=organisation_id
    )
    response = app.get(resource_api_url, headers=headers)
    assert response.status_code == 200 and response.json["result"] is not None

    dataset_is_private = access_scenario["dataset"]["private"]

    # Private datasets aren't visible on organisation_activity_lists
    if access_scenario["user_has_dataset_access"] and not dataset_is_private:
        assert len(response.json["result"]) > 0
    else:
        assert len(response.json["result"]) == 0
        return

    returned_resources = get_returned_resources_from_activity_list(
        response.json["result"], access_scenario["dataset"]["id"], access_scenario["resource"]["id"]
    )

    check_returned_resources_against_user_resource_access(
        returned_resources, unmasked_resource_data, access_scenario["user_has_resource_access"]
    )


@pytest.mark.parametrize(ACCESS_PARAMETERS, ALL_ACCESS_SCENARIOS)
def test_user_activity_list_masks_restricted_resources(app, access_scenario):

    check_activity_plugin_loaded()
    unmasked_resource_data = get_unmasked_resource_data(access_scenario["resource"])

    resource_api_url, headers = create_url_with_headers(
        access_scenario["user"], "user_activity_list", id=access_scenario["dataset_creator_user_id"]
    )
    response = app.get(resource_api_url, headers=headers)
    assert response.status_code == 200 and response.json["result"] is not None

    # If the user doesn't have access to the dataset, the searched user's activity list only be of type 'new user' and contain no resource data
    if not access_scenario["user_has_dataset_access"]:
        assert len(response.json["result"][0]["data"]) == 0
        return

    returned_resources = get_returned_resources_from_activity_list(
        response.json["result"], access_scenario["dataset"]["id"], access_scenario["resource"]["id"]
    )

    check_returned_resources_against_user_resource_access(
        returned_resources, unmasked_resource_data, access_scenario["user_has_resource_access"]
    )


def test_public_activity_stream_detail_is_off():
    """For activity_data_show and activity_diff, only those with edit access to the dataset can view the activity data, unless public_activity_stream_detail is specificallyturned on. This guards the resource metadata without additional masking. Here we'll check the public_activity_stream_detail is turned off."""
    import os

    public_activity_stream_detail_enabled = os.getenv("CKAN__AUTH__PUBLIC_ACTIVITY_STREAM_DETAIL", "false")
    assert public_activity_stream_detail_enabled.lower() == "false", (
        "If public_activity_stream_detail is enabled, resources may be visible to users without proper access"
    )


@pytest.mark.ckan_config("ckan.auth.public_activity_stream_detail", False)
@pytest.mark.parametrize(
    ACCESS_PARAMETERS,
    [
        pytest.param(
            UserType.MEMBER,
            False,
            ResourceAccessLevel.RESTRICT_TO_EDITORS,
            id="member-cannot-read-editor-restricted-activity-history",
        ),
    ],
)
@pytest.mark.parametrize(
    "endpoint",
    ["activity_data_show", "activity_diff"],
)
def test_activity_details_reject_non_editors(app, access_scenario, endpoint):

    # update the dataset to generate an activity for the activity_diff
    helpers.call_action(
        "package_patch",
        context={"user": access_scenario["dataset_creator_user_id"]},
        id=access_scenario["dataset"]["id"],
        title="Updated title",
    )

    activities = helpers.call_action(
        "package_activity_list",
        context={"user": access_scenario["dataset_creator_user_id"]},
        id=access_scenario["dataset"]["id"],
    )

    activity_id = activities[0]["id"]

    url, headers = create_url_with_headers(
        access_scenario["user"],
        endpoint,
        id=activity_id,
        object_type="package",
        include_data=True,
    )
    response = app.get(url, headers=headers)

    assert response.status_code == 403
    assert response.json["success"] is False
    for value in get_unmasked_resource_data(access_scenario["resource"]):
        assert value not in response.text


@pytest.mark.parametrize(
    "initial_level,current_level,expected_access",
    [
        pytest.param(
            ResourceAccessLevel.DATASET_ACCESS_LEVEL,
            ResourceAccessLevel.RESTRICT_TO_EDITORS,
            False,
            id="public-to-restricted",
        ),
        pytest.param(
            ResourceAccessLevel.RESTRICT_TO_EDITORS,
            ResourceAccessLevel.DATASET_ACCESS_LEVEL,
            True,
            id="restricted-to-public",
        ),
    ],
)
@pytest.mark.parametrize(
    ACCESS_PARAMETERS,
    [
        pytest.param(
            UserType.ANONYMOUS,
            False,
            ResourceAccessLevel.DATASET_ACCESS_LEVEL,
            id="anonymous-user-public-dataset-dataset-access-level-resource",
        ),
    ],
)
def test_history_uses_current_resource_permissions(app, access_scenario, initial_level, current_level, expected_access):
    resource = access_scenario["resource"]
    dataset_creator = {"user": access_scenario["dataset_creator_user_id"]}

    helpers.call_action(
        "resource_patch",
        context=dataset_creator.copy(),
        id=resource["id"],
        resource_access_level=initial_level,
    )
    activities = helpers.call_action(
        "package_activity_list",
        context=dataset_creator.copy(),
        id=access_scenario["dataset"]["id"],
    )
    old_activity = next(
        item
        for item in activities
        if any(
            candidate["id"] == resource["id"]
            for candidate in item.get("data", {}).get("package", {}).get("resources", [])
        )
    )

    helpers.call_action(
        "resource_patch",
        context=dataset_creator.copy(),
        id=resource["id"],
        resource_access_level=current_level,
    )

    url, headers = create_url_with_headers(
        access_scenario["user"],
        "package_activity_list",
        id=access_scenario["dataset"]["id"],
    )
    response = app.get(url, headers=headers)
    assert response.status_code == 200
    assert response.json["success"] is True

    returned_activity = next(item for item in response.json["result"] if item["id"] == old_activity["id"])
    returned_resources = get_returned_resources_from_activity_list(
        [returned_activity], access_scenario["dataset"]["id"], resource["id"]
    )
    check_returned_resources_against_user_resource_access(
        returned_resources, get_unmasked_resource_data(resource), expected_access
    )


def get_returned_resources_from_activity_list(activity_list, dataset_id, resource_id):
    activities = [
        item["data"]["package"]
        for item in activity_list
        if item and "package" in item.get("data", {}) and item["data"]["package"]["id"] == dataset_id
    ]

    returned_resources = [
        resource for dataset in activities for resource in dataset.get("resources", []) if resource["id"] == resource_id
    ]
    assert returned_resources, "At least one activity must contain the resource"
    return returned_resources


def check_returned_resources_against_user_resource_access(
    returned_resources, unmasked_resource_data, user_has_resource_access
):
    for returned_resource in returned_resources:
        serialised = json.dumps(returned_resource)
        resource_is_masked = returned_resource.get("resource_is_masked", False)
        for value in unmasked_resource_data:
            if user_has_resource_access:
                assert value in serialised
                assert resource_is_masked is False
            else:
                assert value not in serialised
                assert resource_is_masked is True
