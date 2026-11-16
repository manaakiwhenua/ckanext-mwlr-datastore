import pytest
import ckan.plugins.toolkit as tk
import ckan.plugins as plugins
from ckan.tests import helpers, factories
from ckanext.bsi_restricted_resources.types import ResourceAccessLevel
from ckanext.bsi_restricted_resources.models import RestrictedResourceAccess


@pytest.mark.ckan_config("ckan.plugins", "bsi_restricted_resources")
@pytest.mark.usefixtures("with_plugins", "clean_db")
def test_restricted_resource_access_create(migrate_db_for):
    migrate_db_for("bsi_restricted_resources")
    assert plugins.plugin_loaded("bsi_restricted_resources"), (
        "Test setup failed: bsi_restricted_resources is not loaded."
    )

    resource = factories.Resource()

    user = factories.User()

    current_user = factories.User()
    context = {
        "user": current_user["name"], "ignore_auth": True
    }
    data_dict = {
        "id": resource["id"],
        "resource_access_level": ResourceAccessLevel.RESTRICT_TO_SELECTED_USERS,
        "resource_access_users": [
            {
                "resource_grant_user_id": user["id"],
            }
        ]
    }

    helpers.call_action("restricted_resource_access_create", context=context, **data_dict)

    resource_access = RestrictedResourceAccess.find_resource_access(resource["id"])
    assert len(resource_access) == 1
    resource_access = resource_access[0]
    assert resource_access.resource_id == resource["id"]
    assert resource_access.user_id == user["id"]
    assert resource_access.granted_by_user_id == current_user["id"]