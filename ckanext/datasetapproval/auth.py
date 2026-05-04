
from ckan import model
import ckan.authz as authz
from ckan.logic.auth import get_package_object
import ckan.plugins.toolkit as tk
import logging

log = logging.getLogger(__name__)


# Auth functions have the same names as the actions they are authorizing

def workflow_history_show(context, data_dict) -> dict:
    '''
    Check if the user is logged in and an admin of the dataset's owning organization, or a sysadmin

    Returns:
        dict: A dictionary with a 'success' key indicating whether the user is authorized to view the workflow history.
    '''
    owner_org = tk.get_or_bust(data_dict, "owner_org")
    user_name = context.get('user')
    user_obj = model.User.get(user_name) if user_name else None
    is_sysadmin = user_obj and user_obj.sysadmin
    permission = user_name and authz.users_role_for_group_or_org(owner_org, user_name) == 'admin'  
        
    if not permission and not is_sysadmin:
        return {"success": False}
    else:
        return {"success": True}
    

def get_auth_functions():
    return {
        "workflow_history_show": workflow_history_show
    }