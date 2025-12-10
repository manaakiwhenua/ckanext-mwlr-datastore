import logging

from ckan.plugins import toolkit


log = logging.getLogger(__name__)


def _get_action(action, context_dict, data_dict):
    return toolkit.get_action(action)(context_dict, data_dict)

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
