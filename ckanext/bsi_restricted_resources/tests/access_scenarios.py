import pytest
from ckan.tests import factories
import ckan.plugins as plugins
import uuid
from ckanext.bsi_restricted_resources.logic.access_helpers import (
    USER_TYPES,
    RESOURCE_ACCESS_LEVEL_DICT,
    PRIVATE_DATASET_READERS,
)


def create_users():
    return {
        "anonymous": None,
        "logged_in_not_member": factories.UserWithToken(),
        "member": factories.UserWithToken(),
        "editor": factories.UserWithToken(),
        "admin": factories.UserWithToken(),
        "dataset_creator": factories.UserWithToken(),
        "sysadmin": factories.SysadminWithToken(),
    }


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
    for user_type in USER_TYPES
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

    users = create_users()

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
        name=f"Resource name for {resource_id}",
        description=f"Resource description for {resource_id}",
        url=f"https://example.invalid/protected-test-resource-{resource_id}.csv",
    )

    user_has_access_to_private_dataset = user_type in PRIVATE_DATASET_READERS
    user_expected_to_have_access = (
        not dataset_is_private or user_has_access_to_private_dataset
    ) and user_type in RESOURCE_ACCESS_LEVEL_DICT[resource_access_level]

    return {
        "user": users[user_type],
        "dataset_creator_user_id": users["dataset_creator"]["id"],
        "dataset": dataset,
        "resource": resource,
        "expected_to_have_access": user_expected_to_have_access,
    }
