import pytest
from ckan.tests import factories
import ckan.plugins as plugins
import uuid
from ckanext.bsi_restricted_resources.logic.access_helpers import (
    ALL_USER_TYPES,
    RESOURCE_ACCESS_LEVEL_DICT,
    PRIVATE_DATASET_READERS,
)


def create_users(user_types):
    users = {}
    for user_type in user_types:
        if user_type != "anonymous" and user_type != "sysadmin":
            users[user_type] = factories.UserWithToken()
        if user_type == "sysadmin":
            users[user_type] = factories.SysadminWithToken()
        if user_type == "anonymous":
            users[user_type] = None

    return users


# Parameters name each of the values in ACCESS_SCENARIOS, when passing ACCESS_SCENARIOS to a test function via pytest.mark.parametrize
ACCESS_PARAMETERS = "user_type, dataset_is_private, resource_access_level"
ACCESS_SCENARIOS = [
    pytest.param(
        user_type,
        dataset_is_private,
        resource_access_level,
        # id for the test case - only used by parametrize for readability of test output
        id=(
            f"{user_type}-user-{'private' if dataset_is_private else 'public'}-dataset-{resource_access_level}-resource"
        ),
    )
    for resource_access_level in RESOURCE_ACCESS_LEVEL_DICT.keys()
    for dataset_is_private in (False, True)
    for user_type in ALL_USER_TYPES
]


@pytest.fixture
def access_scenario(
    user_type,
    dataset_is_private,
    resource_access_level,
    with_plugins,
    clean_db,
    clean_index,
):
    assert plugins.plugin_loaded("bsi_restricted_resources"), (
        "Test setup failed: bsi_restricted_resources is not loaded."
    )

    users = create_users(ALL_USER_TYPES)

    organisation = factories.Organization(
        users=[
            {
                "name": users["editor"]["name"],
                "capacity": "editor",
            },
            {
                "name": users["member"]["name"],
                "capacity": "member",
            },
            {
                "name": users["admin"]["name"],
                "capacity": "admin",
            },
            {
                "name": users["dataset_creator"]["name"],
                "capacity": "editor",
            },
        ],
    )

    dataset = factories.Dataset(
        private=dataset_is_private,
        owner_org=organisation["id"],
        user=users["dataset_creator"],
    )
    resource_id = f"resource-{uuid.uuid4()}"
    resource = factories.Resource(
        package_id=dataset["id"],
        resource_id=resource_id,
        resource_access_level=resource_access_level,
        name=f"Resource_name_for_{resource_id}",
        description=f"Resource_description_for_{resource_id}",
        url=f"https://example.invalid/protected-test-resource-{resource_id}.csv",
    )

    user_has_dataset_access = user_type in PRIVATE_DATASET_READERS or not dataset_is_private
    users_who_can_access_resource = RESOURCE_ACCESS_LEVEL_DICT.get(resource_access_level, set())
    user_has_resource_access = user_has_dataset_access and user_type in users_who_can_access_resource

    return {
        "user": users[user_type],
        "dataset_creator_user_id": users["dataset_creator"]["id"],
        "dataset": dataset,
        "resource": resource,
        "user_has_resource_access": user_has_resource_access,
        "user_has_dataset_access": user_has_dataset_access,
    }
