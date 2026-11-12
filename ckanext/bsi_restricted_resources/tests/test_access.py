"""
Test combinations of user permissions and resource access.

Run these tests with:
    ./bin/shell
    cd /srv/app/src_extensions/ckanext-mwlr-datastore
    pytest -v ckanext/bsi_restricted_resources/tests/test_access.py

Note that these tests clean the database, and you may need to compose restart to be able to login afterwards as local_admin.

./bin/restart

If you run into Solr indexing issues, you may need to rebuild the search index:

./bin/ckan search-index rebuild

(Hopefully this shouldn't happen due to 'clean_db' and 'clean_index' parameters in the access_scenario fixture used in the below tests.)

"""

import pytest
import ckan.plugins.toolkit as tk
from ckanext.bsi_restricted_resources.tests.access_scenario_helpers import (
    ALL_ACCESS_SCENARIOS,
    ACCESS_PARAMETERS,
    get_resource_data_that_should_be_masked,
)
from ckan.tests import helpers
from ckanext.bsi_restricted_resources.types import ResourceAccessLevel, UserType

pytestmark = pytest.mark.ckan_config(
    "ckan.plugins", "mwlr_datastore bsi_restricted_resources tracking"
)  # tracking needs to be included to pick up any issues from masking resources


def get_user_context(resource):
    user = resource.get("user")
    user_context = {"user": ""}  # Default to anonymous user context

    if user and user.get("name"):
        user_context = {"user": user["name"]}

    return user_context


# access_scenario is a pytest fixture in conftest.py, and pytest parametrize passes access_scenario the named parameters it requires (in this case, user_type, dataset_is_private, resource_access_level).
# ACCESS_PARAMETERS defines the names of the parameters, which are listed as values in each entry of ALL_ACCESS_SCENARIOS
@pytest.mark.parametrize(ACCESS_PARAMETERS, ALL_ACCESS_SCENARIOS)
def test_resource_access_on_resource_show(access_scenario):

    resource_context = {"id": access_scenario["resource"]["id"]}
    user_context = get_user_context(access_scenario)
    assert access_scenario["dataset"]["creator_user_id"] == access_scenario["dataset_creator_user_id"]

    if access_scenario["user_has_resource_access"]:
        result = tk.get_action("resource_show")(user_context, resource_context)
        assert result["id"] == resource_context["id"]
        assert result["name"] == access_scenario["resource"]["name"]
    else:
        with pytest.raises(tk.NotAuthorized):
            tk.get_action("resource_show")(user_context, resource_context)


@pytest.mark.parametrize(ACCESS_PARAMETERS, ALL_ACCESS_SCENARIOS)
def test_resource_masking_on_package_show(access_scenario):
    resource = access_scenario["resource"]
    resource_data = get_resource_data_that_should_be_masked(resource)
    dataset_context = {"id": access_scenario["dataset"]["id"]}
    user_context = get_user_context(access_scenario)

    if not access_scenario["user_has_dataset_access"]:
        with pytest.raises(tk.NotAuthorized):
            tk.get_action("package_show")(user_context.copy(), dataset_context)
        return

    dataset = tk.get_action("package_show")(user_context.copy(), dataset_context)
    result_resource = next(item for item in dataset["resources"] if item["id"] == access_scenario["resource"]["id"])

    if access_scenario["user_has_resource_access"]:
        for value in resource_data:
            assert value in result_resource.values()
    else:
        for value in resource_data:
            assert value not in result_resource.values()


# Previously having an issue where there was a bare 403 page without the Datastore layout
# Test that accessing a private resource page as an anonymous user returns a proper CKAN 403 page
@pytest.mark.parametrize(
    ACCESS_PARAMETERS,
    [
        pytest.param(
            UserType.ANONYMOUS, False, ResourceAccessLevel.RESTRICT_TO_EDITORS, id="private-resource-in-public-dataset"
        )
    ],
)
def test_private_resource_page_gives_CKAN_403_page(app, access_scenario):

    dataset = access_scenario["dataset"]
    user = access_scenario["user"]
    headers = {"Authorization": user["token"]} if user else {}
    resource = access_scenario["resource"]
    resource_page_url = tk.url_for(
        "dataset_resource.read",
        id=dataset["name"],
        resource_id=resource["id"],
    )

    response = app.get(resource_page_url, headers=headers)

    if access_scenario["user_has_resource_access"]:
        assert response.status_code == 200
    else:
        assert response.status_code == 403
        assert response.content_type == "text/html; charset=utf-8"
        assert "You are not authorised to access this resource." in response.text
        assert "Traceback (most recent call last)" not in response.text


# Test the contents of the calls. Test that accessing a private resource API as an anonymous user returns a JSON error response
@pytest.mark.parametrize(
    ACCESS_PARAMETERS,
    [
        pytest.param(
            UserType.ANONYMOUS,
            False,
            ResourceAccessLevel.RESTRICT_TO_EDITORS,
            id="anonymous-user-private-resource-in-public-dataset",
        ),
        pytest.param(
            UserType.DATASET_CREATOR,
            False,
            ResourceAccessLevel.RESTRICT_TO_EDITORS,
            id="dataset-creator-private-resource-in-public-dataset",
        ),
    ],
)
def test_private_resource_api_returns_json_error(app, access_scenario):

    resource = access_scenario["resource"]
    user = access_scenario["user"]
    headers = {"Authorization": user["token"]} if user else {}
    resource_api_url = tk.url_for("api.action", ver=3, logic_function="resource_show", id=resource["id"])
    response = app.get(resource_api_url, headers=headers)

    if access_scenario["user_has_resource_access"]:
        assert response.status_code == 200
        assert response.content_type == "application/json;charset=utf-8"
        return

    assert response.status_code == 403
    assert response.content_type == "application/json;charset=utf-8"

    payload = response.json

    assert payload["success"] is False
    assert isinstance(payload["error"], dict)


# Test that the dataset UI page masks restricted resource metadata
@pytest.mark.parametrize(
    ACCESS_PARAMETERS,
    [
        pytest.param(
            UserType.ANONYMOUS,
            False,
            ResourceAccessLevel.RESTRICT_TO_EDITORS,
            id="anonymous-user-private-resource-in-public-dataset",
        )
    ],
)
def test_dataset_page_masks_restricted_resource(app, access_scenario):
    dataset = access_scenario["dataset"]
    dataset_page_url = tk.url_for("dataset.read", id=dataset["name"])
    response = app.get(dataset_page_url)

    assert response.status_code == 200
    assert "Resources" in response.text, "Dataset page should contain the Resources section"

    resource = access_scenario["resource"]
    resource_data = get_resource_data_that_should_be_masked(resource)

    for value in resource_data:
        assert value not in response.text, f"Dataset HTML exposed restricted metadata: {value!r}"


# Test that a resource with an unknown access level is not treated as restricted (existing resources should still be accessible)
@pytest.mark.parametrize(
    ACCESS_PARAMETERS,
    [
        pytest.param(
            UserType.ANONYMOUS,
            False,
            "",
            id="anonymous-user-empty-resource-access-level-resource-in-public-dataset",
        )
    ],
)
def test_resource_with_empty_resource_access_level_is_unrestricted(app, access_scenario):
    resource = access_scenario["resource"]
    user = access_scenario["user"]
    headers = {"Authorization": user["token"]} if user else {}
    resource_page_url = tk.url_for(
        "dataset_resource.read",
        id=resource["package_id"],
        resource_id=resource["id"],
    )

    response = app.get(resource_page_url, headers=headers)
    assert response.status_code == 200


# Test that a resource with an unknown but not empty access level is restricted (an unknown access level may be a typo or not added to the RESOURCE_ACCESS_LEVEL_DICT)
@pytest.mark.parametrize(
    ACCESS_PARAMETERS,
    [
        pytest.param(
            UserType.ANONYMOUS,
            False,
            "unknown_access_level",
            id="anonymous-user-unknown-access-level-resource-in-public-dataset",
        )
    ],
)
def test_resource_with_unknown_access_level_is_restricted(app, access_scenario):
    resource = access_scenario["resource"]
    user = access_scenario["user"]
    headers = {"Authorization": user["token"]} if user else {}
    resource_page_url = tk.url_for(
        "dataset_resource.read",
        id=resource["package_id"],
        resource_id=resource["id"],
    )

    response = app.get(resource_page_url, headers=headers)
    assert response.status_code == 403


# Test that a deleted dataset is still restricted
@pytest.mark.parametrize(
    ACCESS_PARAMETERS,
    [
        pytest.param(
            UserType.ANONYMOUS,
            False,
            ResourceAccessLevel.RESTRICT_TO_EDITORS,
            id="anonymous-user-restricted-resource-in-deleted-dataset",
        ),
        pytest.param(
            UserType.SYSADMIN,
            False,
            ResourceAccessLevel.RESTRICT_TO_EDITORS,
            id="admin-user-restricted-resource-in-deleted-dataset",
        ),
    ],
)
def test_deleted_dataset_still_restricts_resource_access(app, access_scenario):
    resource = access_scenario["resource"]
    user = access_scenario["user"]
    headers = {"Authorization": user["token"]} if user else {}

    helpers.call_action("package_delete", id=access_scenario["dataset"]["id"])

    resource_api_url = tk.url_for("api.action", ver=3, logic_function="resource_show", id=resource["id"])
    response = app.get(resource_api_url, headers=headers)

    if access_scenario["user_has_resource_access"]:
        assert response.status_code == 200
    else:
        assert response.status_code == 403


# Test that members can't resource_patch restricted resources
@pytest.mark.parametrize(
    ACCESS_PARAMETERS,
    [
        pytest.param(
            UserType.MEMBER,
            False,
            ResourceAccessLevel.RESTRICT_TO_EDITORS,
            id="member-cannot-patch-restricted-resource",
        ),
        pytest.param(
            UserType.EDITOR,
            True,
            ResourceAccessLevel.RESTRICT_TO_EDITORS,
            id="editor-can-patch-restricted-resource",
        ),
    ],
)
def test_only_editor_level_access_can_patch_restricted_resource(app, access_scenario):
    resource = access_scenario["resource"]
    user = access_scenario["user"]
    headers = {"Authorization": user["token"]} if user else {}

    url = tk.url_for("api.action", ver=3, logic_function="resource_patch")
    # Try to update a restricted resource's access level to the dataset access level
    response = app.post(
        url,
        headers=headers,
        json={"id": resource["id"], "resource_access_level": ResourceAccessLevel.DATASET_ACCESS_LEVEL},
    )

    if access_scenario["user_has_resource_access"]:
        assert response.status_code == 200
    else:
        assert response.status_code == 403
