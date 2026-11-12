from typing import Dict, FrozenSet
from enum import StrEnum


class UserType(StrEnum):
    ANONYMOUS = "anonymous"
    LOGGED_IN_NOT_MEMBER = "logged_in_not_member"
    MEMBER = "member"
    EDITOR = "editor"
    DATASET_CREATOR = "dataset_creator"
    ADMIN = "admin"
    SYSADMIN = "sysadmin"

    @classmethod
    def from_CKAN_role(
        cls, ckan_role: str | None, user_id: str | None = None, dataset_creator_user_id: str | None = None
    ) -> "UserType":
        if ckan_role is None and user_id is None:
            return cls.ANONYMOUS
        if ckan_role is None and user_id is not None:
            return cls.LOGGED_IN_NOT_MEMBER
        if ckan_role is not None and user_id is not None and user_id == dataset_creator_user_id:
            return cls.DATASET_CREATOR
        try:
            return cls(ckan_role)
        except ValueError:
            if user_id is not None:
                return cls.LOGGED_IN_NOT_MEMBER
            return cls.ANONYMOUS  # unknown value, default to anonymous


# Users who have access to private datasets (CKAN gives these roles access to private datasets by default)
class PrivateDatasetReaders(StrEnum):
    MEMBER = UserType.MEMBER
    EDITOR = UserType.EDITOR
    DATASET_CREATOR = UserType.DATASET_CREATOR
    ADMIN = UserType.ADMIN
    SYSADMIN = UserType.SYSADMIN


class ResourceAccessLevel(StrEnum):
    DATASET_ACCESS_LEVEL = "dataset_access_level"
    RESTRICT_TO_EDITORS = "restrict_to_editors"


# Specify which users have access for each resource access level
RESOURCE_ACCESS_LEVEL_DICT: Dict[ResourceAccessLevel, FrozenSet[UserType]] = {
    ResourceAccessLevel.DATASET_ACCESS_LEVEL: frozenset({reader for reader in UserType}),
    ResourceAccessLevel.RESTRICT_TO_EDITORS: frozenset(
        {UserType.DATASET_CREATOR, UserType.ADMIN, UserType.EDITOR, UserType.SYSADMIN}
    ),
    # Add other scenarios here, e.g. "restrict_to_group"
}
