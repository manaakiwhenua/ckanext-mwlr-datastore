import ckan.authz as authz

ALL_USER_TYPES = frozenset(
    ("anonymous", "logged_in_not_member", "member", "editor", "dataset_creator", "admin", "sysadmin")
)

RESOURCE_ACCESS_LEVEL_DICT = {
    "dataset_access_level": ALL_USER_TYPES,
    "restrict_to_editors": frozenset({"dataset_creator", "admin", "editor", "sysadmin"}),
    # Add other scenarios here, e.g. "restrict_to_organisation"
}

# Users types who can access private datasets (a separate list than those who can access restricted resources)
PRIVATE_DATASET_READERS = ALL_USER_TYPES - frozenset({"anonymous", "logged_in_not_member"})


def resource_requires_request_to_access(dataset, resource, user):

    # User may be of type AnonymousUser, which requires us to use 'getattr', rather than directly accessing attributes
    user_id = getattr(user, "id", None)
    user_name = getattr(user, "name", None)
    user_is_sysadmin = getattr(user, "sysadmin", False)
    user_is_dataset_creator = user_id is not None and user_id == dataset.get("creator_user_id")

    resource_access_level = resource.get("resource_access_level", "")
    users_who_have_access = RESOURCE_ACCESS_LEVEL_DICT.get(resource_access_level, frozenset())

    if len(users_who_have_access) == 0:
        return False  # Existing resources have no recognized access level, so won't be restricted

    # Sysadmins and dataset creators always have access without requiring a request
    if user_is_sysadmin or user_is_dataset_creator:
        return False

    org_id = dataset.get("owner_org")
    user_role_in_this_org = authz.users_role_for_group_or_org(org_id, user_name)

    if user_role_in_this_org is None:
        user_type = "anonymous" if not user_id else "logged_in_not_member"
    else:
        user_type = user_role_in_this_org

    requires_request = user_type not in users_who_have_access
    return requires_request


def get_access_helpers():
    return {
        "resource_requires_request_to_access": resource_requires_request_to_access,
    }
