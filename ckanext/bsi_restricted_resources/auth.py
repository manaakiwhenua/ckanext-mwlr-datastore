import ckan.plugins.toolkit as tk
from ckan.logic.auth import get_resource_object

from ckanext.bsi_restricted_resources.logic.access_helpers import (
    resource_requires_request_to_access,
)

# Auth functions have the same names as the actions they are authorizing


@tk.chained_auth_function
@tk.auth_allow_anonymous_access
def resource_show(next_auth, context, data_dict):

    # Use CKAN's next_auth to check if the user has access to the dataset first, before checking access to the resource itself
    result = next_auth(context, data_dict)
    if not result["success"]:
        return result

    resource = get_resource_object(context, data_dict)
    dataset = resource.package

    if resource_requires_request_to_access(
        dataset.as_dict(),
        resource.as_dict(),
        context.get("auth_user_obj"),
    ):
        return {
            "success": False,
            "msg": tk._("You are not authorised to access this resource."),
        }

    return result


def get_auth_functions():
    return {
        "resource_show": resource_show,
    }
