import logging

import ckan.plugins.toolkit as tk
from flask import has_request_context, request
import ckan.lib.base as base

log = logging.getLogger(__name__)


"""
Resource_view_list action wrapper to handle restricted resources.
We wrap CKAN's original resource_view_list action to add exception handling
for restricted resources on the dataset read page and the resource read page.
"""


@tk.chained_action
@tk.side_effect_free
def resource_view_list(next_action, context, data_dict):

    try:
        # Call the next action in the chain (CKAN's original resource_view_list). This triggers our auth.resource_show logic and raises a NotAuthorized for restricted resources.
        return next_action(context, data_dict)

    except tk.NotAuthorized:
        # If this wasn't an HTTP request (e.g., called from the CLI), we can't access request.endpoint, so just raise the exception
        if not has_request_context():
            raise

        dataset_view_page = "dataset.read"
        resource_view_page = "dataset_resource.read"

        if request.endpoint == dataset_view_page:
            log.debug(
                "Omitting restricted preview from dataset page: restricted resource=%s",
                data_dict.get("id"),
            )
            return []

        if request.endpoint == resource_view_page:
            # raise an HTTP 403 Forbidden error for restricted resources - shows an '403 Forbidden' page to the user
            base.abort(
                403,
                tk._("You are not authorised to access this resource."),
            )

        raise


def get_actions():
    return {
        "resource_view_list": resource_view_list,
    }
