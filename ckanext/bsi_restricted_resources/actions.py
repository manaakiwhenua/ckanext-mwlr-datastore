import logging
import ckan.plugins.toolkit as tk
from ckan import model
from flask import has_request_context, request
import ckan.lib.base as base
from ckanext.bsi_restricted_resources.types import ResourceAccessLevel

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


@tk.chained_action
@tk.side_effect_free
def current_package_list_with_resources(next_action, context, data_dict):

    dataset_list = next_action(context, data_dict)
    masked_search_results = [mask_dataset_resources(context, dataset) for dataset in dataset_list]
    return masked_search_results


@tk.chained_action
@tk.side_effect_free
def package_activity_list(next_action, context, data_dict):

    activity_list = next_action(context, data_dict)
    return mask_activity_list(context, activity_list)


@tk.chained_action
@tk.side_effect_free
def recently_changed_packages_activity_list(next_action, context, data_dict):

    activity_list = next_action(context, data_dict)
    return mask_activity_list(context, activity_list)


@tk.chained_action
@tk.side_effect_free
def organization_activity_list(next_action, context, data_dict):

    activity_list = next_action(context, data_dict)
    return mask_activity_list(context, activity_list)


@tk.chained_action
@tk.side_effect_free
def user_activity_list(next_action, context, data_dict):

    activity_list = next_action(context, data_dict)
    return mask_activity_list(context, activity_list)


def mask_activity_list(context, activity_list):

    masked_activities = []
    for activity in activity_list:
        dataset = activity.get("data", {}).get("package")
        if dataset is None:
            masked_activities.append(activity)  # no dataset in activity, leave as is
            continue
        masked_activities.append(
            {**activity, "data": {**activity["data"], "package": mask_historical_dataset(context, dataset)}}
        )

    return masked_activities


def mask_dataset_resources(context, dataset):

    processed_resources = []

    for resource in dataset["resources"]:
        processed_resources.append(mask_resource_if_restricted(context, resource))

    return {
        **dataset,
        "resources": processed_resources,
    }


def mask_resource(resource):
    return {
        "id": resource["id"],
        "package_id": resource["package_id"],
        "name": resource["name"],
        "format": resource.get("format", ""),
        "resource_is_masked": True,
        "tracking_summary": resource.get("tracking_summary", ""),
    }


def mask_resource_if_restricted(context, resource):

    masked_resource = mask_resource(resource)

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


def mask_historical_resource(context, dataset, historical_resource):
    # Because we're checking the history of a resource, we need to check if the resource currently exists and if the user has access to it. If it doesn't currently exist (has been hard-deleted for some reason), mask the historical snapshot by default, because we can't check the permissions with resource_show.
    current_resource = model.Resource.get(historical_resource["id"])
    if current_resource is None:
        return mask_resource(historical_resource)

    access_context = context.copy()
    try:
        tk.check_access("resource_show", access_context, {"id": historical_resource["id"]})
        return historical_resource
    except tk.NotAuthorized:
        return mask_resource(historical_resource)


def mask_historical_dataset(context, dataset):
    return {
        **dataset,
        "resources": [mask_historical_resource(context, dataset, resource) for resource in dataset["resources"]],
    }


def get_actions():
    return {
        "resource_view_list": resource_view_list,
        "package_search": package_search,
        "package_show": package_show,
        "resource_search": resource_search,
        "current_package_list_with_resources": current_package_list_with_resources,
        "package_activity_list": package_activity_list,
        "recently_changed_packages_activity_list": recently_changed_packages_activity_list,
        "organization_activity_list": organization_activity_list,
        "user_activity_list": user_activity_list,
    }
