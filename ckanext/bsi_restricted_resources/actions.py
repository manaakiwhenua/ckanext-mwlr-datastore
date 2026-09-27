import ckan.plugins.toolkit as tk
import logging
from ckanext.bsi_restricted_resources.mailer import notify_dataset_owner_of_request

log = logging.getLogger(__name__)

def request_access_to_dataset_resources(context, data_dict):
    tk.check_access("request_access_to_dataset_resources", context, data_dict)

    package_id = tk.get_or_bust(data_dict, "package_id")
    package_title = data_dict.get("package_title", "")
    message = data_dict.get("message", "")
    requester = context["auth_user_obj"]
    maintainer_email = tk.get_action("package_show")(context, {"id": package_id})["maintainer_email"]

    if maintainer_email is None:
        return {"success": False, "msg": "Dataset maintainer email not found."}

    dataset_url = tk.url_for("package_show", id=package_id, _external=True)

    result = notify_dataset_owner_of_request(
        maintainer_email,
        package_id,
        package_title,
        dataset_url,
        requester,
        message
    )

    return result

def get_actions():
    return {
        "request_access_to_dataset_resources": request_access_to_dataset_resources,
    }
