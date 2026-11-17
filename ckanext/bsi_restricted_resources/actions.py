import logging
import ckan.plugins.toolkit as tk
from ckan.model import User
from flask import has_request_context, request
import ckan.lib.base as base
from ckanext.bsi_restricted_resources.types import ResourceAccessLevel
from ckanext.bsi_restricted_resources.models import RestrictedResourceAccess
import ckan.model.meta as meta

log = logging.getLogger(__name__)


@tk.chained_action
@tk.side_effect_free
def resource_view_list(next_action, context, data_dict):
    """
    Resource_view_list action wrapper to handle restricted resources.
    We wrap CKAN's original resource_view_list action to add exception handling
    for restricted resources on the dataset read page and the resource read page.

    Based partly on EnviDat's resource_view_list handling https://github.com/EnviDat/ckanext-restricted/blob/011c7af86e634d130c7fa7800eaa9beab165b822/ckanext/restricted/action.py#L69
    """

    try:
        # Call the next action in the chain (CKAN's original resource_view_list). This triggers our auth.resource_show logic and raises a NotAuthorized for restricted resources.
        return next_action(context, data_dict)

    except tk.NotAuthorized:
        # Request might be outside of an HTTP request context (e.g., called from the CLI), so we need to check if request.endpoint is available.
        request_endpoint = request.endpoint if has_request_context() else None

        dataset_view_page = "dataset.read"
        resource_view_page = "dataset_resource.read"

        if request_endpoint == dataset_view_page:
            return []  # no preview for this restricted resource, allows the dataset page to render without errors

        if request_endpoint == resource_view_page:
            # raise an HTTP 403 Forbidden error for restricted resources - shows an '403 Forbidden' page to the user
            base.abort(
                403,
                tk._("You are not authorised to access this resource."),
            )

        raise


@tk.chained_action
@tk.side_effect_free
def package_search(next_action, context, data_dict):

    search_result = next_action(context, data_dict)
    masked_search_results = [mask_dataset_resources(context, dataset) for dataset in search_result["results"]]

    return {
        **search_result,
        "results": masked_search_results,
    }


@tk.chained_action
@tk.side_effect_free
def resource_search(next_action, context, data_dict):

    search_result = next_action(context, data_dict)
    masked_search_results = [mask_resource_if_restricted(context, resource) for resource in search_result["results"]]

    return {
        **search_result,
        "results": masked_search_results,
    }


@tk.chained_action
@tk.side_effect_free
def package_show(next_action, context, data_dict):

    dataset = next_action(context, data_dict)
    masked_dataset = mask_dataset_resources(context, dataset)
    return masked_dataset


def mask_dataset_resources(context, dataset):

    processed_resources = []

    for resource in dataset["resources"]:
        processed_resources.append(mask_resource_if_restricted(context, resource))

    return {
        **dataset,
        "resources": processed_resources,
    }


def mask_resource_if_restricted(context, resource):

    masked_resource = {
        "id": resource["id"],
        "package_id": resource["package_id"],
        "name": resource["name"],
        "format": resource.get("format", ""),
        "resource_is_masked": True,
        "tracking_summary": resource.get("tracking_summary", ""),
    }

    # If the resource is set to the dataset access level (e.g. public if the dataset is public, private if the dataset is private), or if the resource access level is empty (e.g. older resources), don't mask it. The dataset and standard CKAN handle access control at the dataset level
    if (
        resource.get("resource_access_level") == ResourceAccessLevel.DATASET_ACCESS_LEVEL
        or resource.get("resource_access_level", "") == ""
    ):
        return resource

    # This could cause a performance issue - we're doing an access check for each resource individually, which may be expensive for large datasets. May need to replace in future with bulk access checks
    try:
        tk.check_access(
            "resource_show",
            context.copy(),
            {"id": resource["id"]},
        )
        return resource
    except tk.NotAuthorized:
        return masked_resource


def restricted_resource_access_create(context, data_dict):
    """
    Create restricted_resource_access records for a newly created resource
    :param context:
    :param data_dict:
    :return:
    """
    tk.check_access("restricted_resource_access_create", context, data_dict)
    resource_access_level = data_dict.get("resource_access_level")
    if resource_access_level != ResourceAccessLevel.RESTRICT_TO_SELECTED_USERS:
        # nothing to create
        return

    users = data_dict.get("resource_access_users", [])
    if len(users) == 0:
        # nothing to create
        return

    current_user = tk.current_user or User.get(context["user"])
    items = [{ "user_id": user["resource_grant_user_id"], "granted_by_user_id": current_user.id, "resource_id": data_dict["id"] } for user in users]
    log.info("Restricted resource access create: %s" % items)
    RestrictedResourceAccess.create(items)
    meta.Session.commit()


def restricted_resource_access_update(context, data_dict):
    """
    Update restricted_resource_access records for a resource
    :param context:
    :param data_dict:
    :return:
    """
    tk.check_access("restricted_resource_access_update", context, data_dict)

    resource_access_level = data_dict.get("resource_access_level")
    if resource_access_level != ResourceAccessLevel.RESTRICT_TO_SELECTED_USERS:
        # nothing to create
        return

    users = data_dict.get("resource_access_users", [])
    user_ids = [user["resource_grant_user_id"] for user in users]
    current_user = tk.current_user or User.get(context["user"])
    RestrictedResourceAccess.update_resource_access(data_dict["id"], user_ids, current_user.id)
    meta.Session.commit()


def restricted_resource_access_delete(context, data_dict):
    """
    Deletes all restricted_resource_access associated with a resource

    :param context:
    :param data_dict: expects { "id": str } where "id" is the id of the resource
    :return:
    """
    tk.check_access("restricted_resource_access_delete", context, data_dict)
    id = data_dict.get("id")
    if id is None:
        return
    RestrictedResourceAccess.delete_resource_access(id)
    meta.Session.commit()


def get_actions():
    return {
        "resource_view_list": resource_view_list,
        "package_search": package_search,
        "package_show": package_show,
        "resource_search": resource_search,
        "restricted_resource_access_create": restricted_resource_access_create,
        "restricted_resource_access_update": restricted_resource_access_update,
        "restricted_resource_access_delete": restricted_resource_access_delete,
    }
