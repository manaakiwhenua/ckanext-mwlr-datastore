import ckan.plugins.toolkit as tk
import logging

log = logging.getLogger(__name__)

def resource_requires_request_to_access(resource):
    resource_access_level = resource.get("resource_access_level", "")
    requires_request = resource_access_level == "by_request"
    return requires_request

def get_access_helpers():
    return {
    "resource_requires_request_to_access": resource_requires_request_to_access,
}
