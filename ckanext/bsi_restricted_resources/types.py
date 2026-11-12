from typing import Dict, FrozenSet
from enum import StrEnum
import ckan.plugins.toolkit as tk
import logging

log = logging.getLogger(__name__)

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
    RESTRICT_TO_AUTHENTICATED_USERS = "restrict_to_authenticated_users"

    def label(self) -> str:
        """
        Human-readable label for this access level
        """
        match self:
            case ResourceAccessLevel.DATASET_ACCESS_LEVEL:
                return tk._('Dataset access level')
            case ResourceAccessLevel.RESTRICT_TO_EDITORS:
                return tk._('Restrict to dataset editors')
            case ResourceAccessLevel.RESTRICT_TO_AUTHENTICATED_USERS:
                return tk._('Only authenticated users')
        raise tk.ValidationError()

# Specify which users have access for each resource access level
RESOURCE_ACCESS_LEVEL_DICT: Dict[ResourceAccessLevel, FrozenSet[UserType]] = {
    ResourceAccessLevel.DATASET_ACCESS_LEVEL: frozenset({reader for reader in UserType}),
    ResourceAccessLevel.RESTRICT_TO_EDITORS: frozenset(
        {UserType.DATASET_CREATOR, UserType.ADMIN, UserType.EDITOR, UserType.SYSADMIN}
    ),
    # Everyone that is authenticated
    ResourceAccessLevel.RESTRICT_TO_AUTHENTICATED_USERS: frozenset(
        frozenset({reader for reader in UserType if reader != UserType.ANONYMOUS}),
    )
    # Add other scenarios here, e.g. "restrict_to_group"
}
