import ckan.plugins.toolkit as tk
from ckan.logic.auth import get_resource_object

from ckanext.bsi_restricted_resources.logic.access_helpers import (
    resource_requires_request_to_access,
)


@tk.chained_auth_function
@tk.auth_allow_anonymous_access
def resource_show(next_auth, context, data_dict):

    # Use CKAN's next_auth to check if the user has access to the dataset first
    result = next_auth(context, data_dict)
    if not result["success"]:
        return result

    resource = get_resource_object(context, data_dict)

    # If the resource is public, return success
    if not resource_requires_request_to_access(resource.as_dict()):
        return result

    try:
        tk.check_access(
            "package_update",
            context,
            {"id": resource.package_id},
        )
    except tk.NotAuthorized:
        return {
            "success": False,
            "msg": tk._("You are not authorised to access this resource."),
        }

    return result


def get_auth_functions():
    return {
        "resource_show": resource_show,
    }
