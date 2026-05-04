
import logging
from ckan.logic.auth import get_package_object
from ckan.plugins import toolkit as tk

log = logging.getLogger(__name__)

@tk.auth_allow_anonymous_access
def retrieve_publishing_status(context, data_dict):
    return {"success": True}
    