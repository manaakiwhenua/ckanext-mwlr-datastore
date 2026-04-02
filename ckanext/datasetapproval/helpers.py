import logging
from datetime import datetime
from ckanext.datasetapproval import models

from ckan.plugins import toolkit
from .enums import VOCAB_ENUMS, review_outcome_mapping, WorkflowActionType

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

def get_workflow_actions(dataset_id):
    '''
    Get all review actions for a given dataset
    '''
    actions = models.meta.Session.query(models.WorkflowAction).filter_by(dataset_id=dataset_id).order_by(models.WorkflowAction.submitted_date.desc()).all()
    return actions

def map_workflow_action_to_decision_type(current_workflow_action : models.WorkflowAction):

    try:
        workflow_action_type = WorkflowActionType(current_workflow_action.workflow_action)
    except ValueError:
        log.warning(f"Workflow action {current_workflow_action.workflow_action} not found in WorkflowActionType enum")
        return ""

    return review_outcome_mapping[workflow_action_type]