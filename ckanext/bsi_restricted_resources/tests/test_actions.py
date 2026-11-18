import pytest
import ckan.plugins as plugins
from ckan.tests import helpers, factories
from ckanext.bsi_restricted_resources.types import ResourceAccessLevel
from ckanext.bsi_restricted_resources.models import RestrictedResourceAccess


def resource_for_users(resource, resource_access_level: ResourceAccessLevel, users: list):
    return {
        "id": resource["id"],
        "resource_access_level": resource_access_level,
        "resource_access_users": [{"resource_grant_user_id": user["id"]} for user in users]
    }


@pytest.fixture
def actions_test_setup(migrate_db_for):
    migrate_db_for("bsi_restricted_resources")
    assert plugins.plugin_loaded("bsi_restricted_resources"), (
        "Test setup failed: bsi_restricted_resources is not loaded."
    )


@pytest.mark.ckan_config("ckan.plugins", "bsi_restricted_resources")
@pytest.mark.usefixtures("with_plugins", "clean_db", "actions_test_setup")
def test_restricted_resource_access_create():
    user = factories.User()
    current_user = factories.User()
    context = {"user": current_user["name"], "ignore_auth": True}
    resource = factories.Resource()
    data_dict = resource_for_users(resource, ResourceAccessLevel.RESTRICT_TO_SELECTED_USERS, [user])
    helpers.call_action("restricted_resource_access_create", context=context, **data_dict)

    resource_access = RestrictedResourceAccess.find_resource_access(resource["id"])
    assert len(resource_access) == 1
    resource_access = resource_access[0]
    assert resource_access.resource_id == resource["id"]
    assert resource_access.user_id == user["id"]
    assert resource_access.granted_by_user_id == current_user["id"]


@pytest.mark.ckan_config("ckan.plugins", "bsi_restricted_resources")
@pytest.mark.usefixtures("with_plugins", "clean_db", "actions_test_setup")
def test_restricted_resource_access_update():
    users = [factories.User(), factories.User(), factories.User()]
    current_user = factories.User()
    context = {"user": current_user["name"], "ignore_auth": True}
    resource = factories.Resource()
    data_dict = resource_for_users(resource, ResourceAccessLevel.RESTRICT_TO_SELECTED_USERS, [users[0]])
    helpers.call_action("restricted_resource_access_create", context=context, **data_dict)
    data_dict = resource_for_users(resource, ResourceAccessLevel.RESTRICT_TO_SELECTED_USERS, users)
    helpers.call_action("restricted_resource_access_update", context=context, **data_dict)
    resource_access = RestrictedResourceAccess.find_resource_access(resource["id"])
    user_ids = {user["id"] for user in users}
    assert len(resource_access) == len(users)
    for grant in resource_access:
        assert grant.resource_id == resource["id"]
        assert grant.user_id in user_ids
        assert grant.granted_by_user_id == current_user["id"]

    data_dict = resource_for_users(resource, ResourceAccessLevel.RESTRICT_TO_SELECTED_USERS, [users[1]])
    helpers.call_action("restricted_resource_access_update", context=context, **data_dict)
    resource_access = RestrictedResourceAccess.find_resource_access(resource["id"])
    assert len(resource_access) == 1
    grant = resource_access[0]
    assert grant.resource_id == resource["id"]
    assert grant.user_id == users[1]["id"]
    assert grant.granted_by_user_id == current_user["id"]

    new_user = factories.User()
    data_dict = resource_for_users(resource, ResourceAccessLevel.RESTRICT_TO_SELECTED_USERS, [users[1], new_user])
    helpers.call_action("restricted_resource_access_update", context=context, **data_dict)
    resource_access = RestrictedResourceAccess.find_resource_access(resource["id"])
    assert len(resource_access) == 2
    user_ids = {user["id"] for user in [users[1], new_user]}
    for grant in resource_access:
        assert grant.resource_id == resource["id"]
        assert grant.user_id in user_ids
        assert grant.granted_by_user_id == current_user["id"]

    data_dict = resource_for_users(resource, ResourceAccessLevel.RESTRICT_TO_SELECTED_USERS, [])
    helpers.call_action("restricted_resource_access_update", context=context, **data_dict)
    resource_access = RestrictedResourceAccess.find_resource_access(resource["id"])
    assert len(resource_access) == 0


@pytest.mark.ckan_config("ckan.plugins", "bsi_restricted_resources")
@pytest.mark.usefixtures("with_plugins", "clean_db", "actions_test_setup")
def test_restricted_resource_access_delete():
    users = [factories.User(), factories.User(), factories.User()]
    current_user = factories.User()
    context = {"user": current_user["name"], "ignore_auth": True}
    resource = factories.Resource()
    data_dict = resource_for_users(resource, ResourceAccessLevel.RESTRICT_TO_SELECTED_USERS, users)
    helpers.call_action("restricted_resource_access_create", context=context, **data_dict)
    resource_access = RestrictedResourceAccess.find_resource_access(resource["id"])
    assert len(resource_access) == len(users)
    helpers.call_action("resource_delete", context=context, id=resource["id"])
    resource_access = RestrictedResourceAccess.find_resource_access(resource["id"])
    assert len(resource_access) == 0
