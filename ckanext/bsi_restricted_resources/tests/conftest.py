import pytest
from ckan.tests import factories
import ckan.plugins as plugins
import uuid
from ckanext.bsi_restricted_resources.types import (
    PrivateDatasetReaders,
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
    activity_db,
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
        resources=[
            {
                "description": f"Resource_description_{uuid.uuid4()}",
                "name": f"Resource_name_{uuid.uuid4()}",
                "url": f"https://example.invalid/restricted-resource-{uuid.uuid4()}.csv",
                "resource_access_level": resource_access_level,
                "author": users[UserType.DATASET_CREATOR]["name"],
                "maintainer": users[UserType.DATASET_CREATOR]["name"],
                "maintainer_email": f"{users[UserType.DATASET_CREATOR]['name']}@example.invalid",
                "publication_year": 2024,
            }
        ],
    )

    user_has_dataset_access = user_type in PrivateDatasetReaders.__members__.values() or not dataset_is_private
    users_who_can_access_resource = RESOURCE_ACCESS_LEVEL_DICT.get(resource_access_level, set())
    user_has_resource_access = user_has_dataset_access and user_type in users_who_can_access_resource

    return {
        "user": users[user_type],
        "dataset_creator_user_id": users[UserType.DATASET_CREATOR]["id"],
        "dataset": dataset,
        "resource": dataset["resources"][0],
        "user_has_resource_access": user_has_resource_access,
        "user_has_dataset_access": user_has_dataset_access,
    }


# Test_activity_list requires db migration for the activity plugin
@pytest.fixture
def activity_db(with_plugins, clean_db, migrate_db_for):
    if plugins.plugin_loaded("activity"):
        migrate_db_for("activity")
