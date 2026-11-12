import pytest
from ckan.tests import factories
import ckan.plugins as plugins
import uuid
from ckanext.bsi_restricted_resources.types import (
    PrivateDatasetReaders,
    ResourceAccessLevel,
    UserType,
    RESOURCE_ACCESS_LEVEL_DICT,
)


def create_users(user_types):
    users = {}
    for user_type in user_types:
        if user_type != UserType.ANONYMOUS and user_type != UserType.SYSADMIN:
            users[user_type] = (
                factories.UserWithToken()
            )  # most users are regular CKAN users, with their roles further defined in the organisation setup below
        if user_type == UserType.SYSADMIN:
            users[user_type] = factories.SysadminWithToken()
        if user_type == UserType.ANONYMOUS:
            users[user_type] = None

    return users


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

    users = create_users(UserType.__members__.values())

    organisation = factories.Organization(
        users=[
            {
                "name": users[UserType.EDITOR]["name"],
                "capacity": "editor",  # CKAN capacities, not our defined user types
            },
            {
                "name": users[UserType.MEMBER]["name"],
                "capacity": "member",
            },
            {
                "name": users[UserType.ADMIN]["name"],
                "capacity": "admin",
            },
            {
                "name": users[UserType.DATASET_CREATOR]["name"],
                "capacity": "editor",
            },
        ],
    )

    dataset = factories.Dataset(
        private=dataset_is_private,
        owner_org=organisation["id"],
        user=users[UserType.DATASET_CREATOR],
    )
    resource_id = f"resource_{uuid.uuid4()}"
    resource = factories.Resource(
        package_id=dataset["id"],
        resource_id=resource_id,
        resource_access_level=resource_access_level,
        name=f"Resource_name_for_{resource_id}",
        description=f"Resource_description_for_{resource_id}",
        url=f"https://example.invalid/protected-test-resource-{resource_id}.csv",
    )

    user_has_dataset_access = user_type in PrivateDatasetReaders.__members__.values() or not dataset_is_private
    users_who_can_access_resource = RESOURCE_ACCESS_LEVEL_DICT.get(resource_access_level, set())
    user_has_resource_access = user_has_dataset_access and user_type in users_who_can_access_resource

    return {
        "user": users[user_type],
        "dataset_creator_user_id": users[UserType.DATASET_CREATOR]["id"],
        "dataset": dataset,
        "resource": resource,
        "user_has_resource_access": user_has_resource_access,
        "user_has_dataset_access": user_has_dataset_access,
    }


@pytest.fixture
def resource_restricted_to_selected_users():
    def factory(users, dataset_is_private: bool, organisation = None):
        organisation = organisation if organisation is not None else factories.Organization()
        dataset = factories.Dataset(
            private=dataset_is_private,
            owner_org=organisation["id"],
            user=factories.UserWithToken(),
        )
        resource_id = f"resource_{uuid.uuid4()}"
        resource = factories.Resource(
            package_id=dataset["id"],
            resource_id=resource_id,
            resource_access_level=ResourceAccessLevel.RESTRICT_TO_SELECTED_USERS,
            name=f"Resource_name_for_{resource_id}",
            description=f"Resource_description_for_{resource_id}",
            url=f"https://example.invalid/protected-test-resource-{resource_id}.csv",
            resource_access_users=[
                { "resource_grant_user_id": user["id"] for user in users }
            ]
        )
        return resource
    return factory
