import pytest
import ckan.plugins.toolkit as tk
from ckanext.bsi_restricted_resources.tests.access_scenario_helpers import (
    ACCESS_PARAMETERS,
)
from ckanext.bsi_restricted_resources.types import UserType

pytestmark = pytest.mark.ckan_config(
    "ckan.plugins",
    "mwlr_datastore bsi_restricted_resources tracking",
)

# Leave out the restricted resource scheming file to test legacy behaviour without scheming enforcement of the default 'resource_access_level' field


# Test that a resource with an unknown access level is not treated as restricted (existing resources should still be accessible)
@pytest.mark.parametrize(
    ACCESS_PARAMETERS,
    [pytest.param(UserType.ANONYMOUS, False, "", id="anonymous-user-empty-access-level-resource-in-public-dataset")],
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
