import ckan.authz as authz
from ckanext.bsi_restricted_resources.types import (
    UserType,
    RESOURCE_ACCESS_LEVEL_DICT,
)


def resource_requires_request_to_access(dataset, resource, user):

    # User may be of type AnonymousUser, which requires us to use 'getattr', rather than directly accessing attributes
    user_id = getattr(user, "id", None)
    user_name = getattr(user, "name", None)
    user_is_sysadmin = getattr(user, "sysadmin", False)
    dataset_creator_user_id = dataset.get("creator_user_id")
    user_is_dataset_creator = user_id is not None and user_id == dataset_creator_user_id
    resource_access_level = resource.get("resource_access_level", "")

    # Sysadmins and dataset creators always have access without requiring a request
    if user_is_sysadmin or user_is_dataset_creator:
        return False

    if resource_access_level == "":
        return False  # No resource access level specified (most likely a legacy resource), dataset-level access applies

    users_who_have_access = RESOURCE_ACCESS_LEVEL_DICT.get(resource_access_level, frozenset())
    if resource_access_level != "" and len(users_who_have_access) == 0:
        return True  # This means an unrecognised resource access level (possibly a typo or new level not in the dict). Resource will require a request to access

    org_id = dataset.get("owner_org")
    user_role_in_this_org = authz.users_role_for_group_or_org(org_id, user_name)

    user_type = UserType.from_CKAN_role(user_role_in_this_org, user_id, dataset_creator_user_id)
    requires_request = user_type not in users_who_have_access
    return requires_request


def some_resources_are_restricted(resources) -> bool:
    if not isinstance(resources, list):
        return False
    return any(resource.get("resource_is_masked") for resource in resources)


def get_access_helpers():
    return {
        "some_resources_are_restricted": some_resources_are_restricted,
        "resource_requires_request_to_access": resource_requires_request_to_access,
    }
