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
from ckanext.bsi_restricted_resources.tests.access_scenarios import (
    ACCESS_SCENARIOS,
    ACCESS_PARAMETERS,
    access_scenario,
    PRIVATE_DATASET_READERS,
)

pytestmark = pytest.mark.ckan_config("ckan.plugins", "mwlr_datastore bsi_restricted_resources")


def get_user_context(resource):
    user = resource.get("user")
    user_context = {"user": ""}  # Default to anonymous user context

    if user and user.get("name"):
        user_context = {"user": user["name"]}

    return user_context


# access_scenario is a pytest fixture, and pytest parametrize passes access_scenario the named parameters it requires (in this case, user_type, dataset_is_private, resource_access_level, user_has_resource_access).


# ACCESS_PARAMETERS defines the names of the parameters, which are listed as values in each entry of ACCESS_SCENARIOS
@pytest.mark.parametrize(ACCESS_PARAMETERS, ACCESS_SCENARIOS)
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


@pytest.mark.parametrize(ACCESS_PARAMETERS, ACCESS_SCENARIOS)
def test_resource_masking_on_package_show(access_scenario, dataset_is_private, user_type):

    dataset_context = {"id": access_scenario["dataset"]["id"]}
    user_context = get_user_context(access_scenario)
    dataset_is_private_to_this_user = dataset_is_private and user_type not in PRIVATE_DATASET_READERS

    if dataset_is_private_to_this_user:
        with pytest.raises(tk.NotAuthorized):
            tk.get_action("package_show")(user_context.copy(), dataset_context)
        return

    dataset = tk.get_action("package_show")(user_context.copy(), dataset_context)
    resource = next(item for item in dataset["resources"] if item["id"] == access_scenario["resource"]["id"])

    if access_scenario["user_has_resource_access"]:
        for field in ("name", "description", "url"):
            assert resource[field] == access_scenario["resource"][field]
    else:
        assert resource["name"] == "Restricted resource"
        assert "description" not in resource
        assert "url" not in resource


# Previously having an issue where there was a bare 403 page without the Datastore layout
# Test that accessing a private resource page as an anonymous user returns a proper CKAN 403 page
@pytest.mark.parametrize(
    ACCESS_PARAMETERS,
    [pytest.param("anonymous", False, "restrict_to_creator", id="private-resource-in-public-dataset")],
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
        pytest.param("anonymous", False, "restrict_to_creator", id="anonymous-user-private-resource-in-public-dataset"),
        pytest.param(
            "dataset_creator", False, "restrict_to_creator", id="dataset-creator-private-resource-in-public-dataset"
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
    [("anonymous", False, "restrict_to_creator")],
)
def test_dataset_page_masks_restricted_resource(app, access_scenario):
    dataset = access_scenario["dataset"]
    dataset_page_url = tk.url_for("dataset.read", id=dataset["name"])
    response = app.get(dataset_page_url)

    assert response.status_code == 200
    assert "Resources" in response.text, "Dataset page should contain the Resources section"

    resource = access_scenario["resource"]
    resource_data = [resource["name"], resource["description"], resource["url"]]

    for value in resource_data:
        assert value not in response.text, f"Dataset HTML exposed restricted metadata: {value!r}"
