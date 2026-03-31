import logging
from datetime import datetime
from ckanext.datasetapproval import models

from ckan.plugins import toolkit
from .enums import VOCAB_ENUMS

log = logging.getLogger(__name__)

def _get_action(action, context_dict, data_dict):
    return toolkit.get_action(action)(context_dict, data_dict)

def get_org_from_package_name(package_name):
    """
    Returns the organisation id for a given package name

    :param package_name: package name
    :type package_name: string

    :returns: organisation id
    :rtype: string
    """
    pkg_dict = _get_action(
                'package_show', {'ignore_auth': True}, {'id': package_name})
    log.debug(f"Package dict for package {package_name}: {pkg_dict}")
    return pkg_dict.get('owner_org')

def is_admin(user, organisation=None):
    """
    Returns True if user is admin of given organisation.
    If office param is not provided checks if user is admin of any organisation

    :param user: user name
    :type user: string
    :param organisation: organisation id
    :type user: string

    :returns: True/False
    :rtype: boolean
    """
    user_orgs = _get_action(
                'organization_list_for_user', {'user': user}, {'user': user})
    if organisation is not None:
        return any([i.get('capacity') == 'admin' \
                and i.get('id') == organisation for i in user_orgs])
    return any([i.get('capacity') == 'admin' for i in user_orgs])


def get_vocab_group(group_name):
    # need to map the group name to the correct enum class then grab all enums as a dict with key and value
    enum_cls = getattr(VOCAB_ENUMS, group_name, None)
    if not enum_cls:
        log.warning(f"Vocabulary group {group_name} not found in VOCAB_ENUMS")
        return {}
    return {e.name: e.value for e in enum_cls}

def vocab_label(key, value):
    enum_cls = getattr(VOCAB_ENUMS, key, None)
    if not enum_cls:
        return value
    try:
        return enum_cls[value].value
    except KeyError:
        return value

def add_reviewal_details_to_pkg(pkg_dict, reviewer_name, reviewer_email, review_date = None):
    ## may need to change this in future but for now can leave if decided better to just store on a separate table
    ## TODO: remove this if decided we no longer want to store details on pkg
    pkg_dict['reviewer_name'] = reviewer_name
    pkg_dict['reviewer_email'] = reviewer_email
    if review_date is None:
        current_date = datetime.now()
        review_date = current_date.strftime("%Y-%m-%d")
    pkg_dict['review_date'] = review_date
    return pkg_dict

def get_reviewer_actions(dataset_id):
    '''
    Get all review actions for a given dataset
    '''
    actions = models.meta.Session.query(models.ReviewAction).filter_by(dataset_id=dataset_id).all()
    return actions
    