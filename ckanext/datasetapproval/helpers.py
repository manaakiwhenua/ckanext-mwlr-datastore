import logging
from datetime import datetime
from ckan.plugins import toolkit


log = logging.getLogger(__name__)

VOCABS = {
    "rejection_reason": {
        "data_quality": "Data quality issues",
        "documentation": "Incomplete or inadequate documentation",
        "legal": "Legal / contractual restrictions",
        "cultural": "Cultural / ethical concerns",
        "privacy": "Privacy / sensitivity issues",
        "ip": "IP / commercial risk",
        "sop": "Non-compliance with SOP",
        "other": "Other",
    },
    "resubmission": {
        "yes": "Yes",
        "no": "No",
    },
    "compliance_status": {
        "non_compliant": "Non-compliant",
        "compliant": "Compliant",
        "partial": "Partially compliant",
    },
    "approval_outcome": {
        "approved": "Approved",
        "conditional": "Conditional Approval"
    }
}


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
    return VOCABS.get(group_name, {})

def vocab_label(field, key):
    return VOCABS.get(field, {}).get(key, key)

def add_reviewal_details_to_pkg(pkg_dict, reviewer_name, reviewer_email, review_date = None):
    ## does the review type need to be added here? Or is this present on the dataset form
    pkg_dict['reviewer_name'] = reviewer_name
    pkg_dict['reviewer_email'] = reviewer_email
    if review_date is None:
        current_date = datetime.now()
        review_date = current_date.strftime("%Y-%m-%d")
    pkg_dict['review_date'] = review_date
    return pkg_dict

def add_approval_details_to_pkg(pkg_dict, approver_name, approver_email, approve_date = None):
    ## does approval type need to be added here? Or is this present on the dataset form
    pkg_dict['approver_name'] = approver_name
    pkg_dict['approver_email'] = approver_email
    if approve_date is None:
        current_date = datetime.now()
        approve_date = current_date.strftime("%Y-%m-%d")
    pkg_dict['approve_date'] = approve_date
    return pkg_dict
