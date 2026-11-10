import pytest
from ckanext.bsi_restricted_resources.logic.access_helpers import ALL_USER_TYPES, RESOURCE_ACCESS_LEVEL_DICT


# Parameters name each of the values in ALL_ACCESS_SCENARIOS, when passing ALL_ACCESS_SCENARIOS to a test function via pytest.mark.parametrize
ACCESS_PARAMETERS = "user_type, dataset_is_private, resource_access_level"
ALL_ACCESS_SCENARIOS = [
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


def get_resource_data_that_should_be_masked(resource):
    return [resource["description"], resource["url"]]
