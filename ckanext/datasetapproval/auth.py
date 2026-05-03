
from ckan import model
import ckan.authz as authz
from ckan.logic.auth import get_package_object
import ckan.plugins.toolkit as tk
import logging

log = logging.getLogger(__name__)

def check_user_sysadmin_or_org_admin(owner_org=None, user_name=None):
    '''
    Check if the user is logged in and an admin of the dataset's owning organization, or a sysadmin
    '''
    user_obj = model.User.get(user_name) if user_name else None
    is_sysadmin = user_obj and user_obj.sysadmin
    permission = user_name and authz.users_role_for_group_or_org(owner_org, user_name) == 'admin'  
    
    if not permission and not is_sysadmin:
        raise tk.abort(404, 'Dataset not found or you have no permission to view it')