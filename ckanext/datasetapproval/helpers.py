from datetime import datetime
import logging
from ckan.plugins import toolkit
from .enums import VOCAB_ENUMS
from .models import ReviewRequest
from zoneinfo import ZoneInfo

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
    If organisation param is not provided checks if user is admin of ANY organisation

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

def convert_utc_to_local_time_string(utc_dt : datetime, tz_name='Pacific/Auckland') -> str:
    return utc_dt.astimezone(ZoneInfo(tz_name)).strftime('%Y-%m-%d %I:%M %p') + f' ({ZoneInfo(tz_name).key} time)'

def retrieve_data_management_email():
    return toolkit.config.get(u'ckan.datastore.data_management_email') or ""



def get_review_types_for_display(pkg_dict=None) -> list[ReviewRequest]:
    if not pkg_dict:
        return []
    
    review_type_enum = VOCAB_ENUMS.review_type
    additional_reviews_requested = []
    review_required_keys = [k for k in pkg_dict.keys() if k.endswith('_review_required') and pkg_dict.get(k) == True]

    for review_required_key in review_required_keys:
        review_type_key = review_required_key.replace('_review_required', '')
        review_type = review_type_enum[review_type_key].value if review_type_key in review_type_enum.__members__ else review_type_key.replace('_', ' ').title()
        review_request_comments = pkg_dict.get(f'{review_type_key}_review_notes', None)
        additional_reviews_requested.append(ReviewRequest(review_type=review_type, review_request_comments=review_request_comments))

    return additional_reviews_requested