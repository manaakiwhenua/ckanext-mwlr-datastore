import logging

from ckan import model
from ckan.common import config
from ckan.plugins import toolkit
from ckan.lib.mailer import mail_user
from ckan.lib.base import render
from ckan.logic.action.get import member_list as core_member_list

log = logging.getLogger(__name__)


def mail_package_review_request_to_admins(context, data_dict, _type='new'):
    members = core_member_list(
        context=context,
        data_dict={'id': data_dict.get('owner_org')}
    )
    org_admin = [i[0] for i in members if i[2] == 'Admin']

    sysadmins = model.Session.query(model.User.id).filter(
            model.User.state != model.State.DELETED,
            model.User.sysadmin == True
            ).all()
    # Merged org admin and sysadmin so that sysadmin also gets the email. 
    admins = list(set( org_admin + [admin[0] for admin in sysadmins]))
    for admin_id in admins :
        user = model.User.get(admin_id)
        if user.email:
            subj = _compose_email_subj_for_admins(_type)
            body = _compose_email_body_for_admins(context, data_dict, user, _type)
            try:
                mail_user(user, subj, body)
            except Exception as e:
                log.error(f'[email] Failed to send dataset review request email to {user.name}: {e}')
            else:
                log.debug('[email] Dataset review request email sent to {0}'.format(user.name))



def mail_package_approve_reject_notification_to_editors(package_id, publishing_status, rejection_reason=None):
    package_dict = toolkit.get_action('package_show' )({'ignore_auth': True}, {'id':package_id })
    editor = model.User.get(package_dict.get('creator_user_id'))
    if editor.email:
        subj = _compose_email_subj_for_editors(publishing_status)
        body = _compose_email_body_for_editors(editor, package_dict, publishing_status, rejection_reason)
        try:
            mail_user(editor, subj, body)
        except Exception as e:
            log.error(f'[email] Failed to send dataset approved/rejected notification email to {editor.name}: {e}')
        else:
            log.debug('[email] Dataset approved/rejected notification email sent to {0}'.format(editor.name))


def _compose_email_subj_for_admins(_type):
    return ' A {0} dataset is requested for review.'.format(_type)


def _compose_email_subj_for_editors(state):
    if state == 'approved':
        return 'Dataset request has been reviewed and approved by the administrator.'
    else: 
        return 'Your dataset request has been reviewed by the administrator.'


def _get_publisher_name(context, id):
    try:
        user_dict = toolkit.get_action('user_show')(context, {'id': id})
        return user_dict.get('display_name')
    except toolkit.ObjectNotFound as e:
        return 'None'

def _compose_email_body_for_admins(context, data_dict, user, _type):
    pkg_link = toolkit.url_for('dataset.read', id=data_dict['name'], qualified=True)
    admin_name = user.fullname or user.name
    site_title = config.get('ckan.site_title')
    site_url = config.get('ckan.site_url')
    package_title = data_dict.get('title')
    package_description = data_dict.get('notes', '')
    package_url = pkg_link
    publisher_name = _get_publisher_name(context, data_dict.get('creator_user_id'))

    email_body = f'''
    Dear {admin_name},

    {'An'if _type == 'updated' else 'A'} {_type} dataset has been submitted for review by {publisher_name}:

    '{package_title}'

    {package_description}

    To approve or reject the request, please visit the following page (while logged in as an admin):

    {package_url}

    --
    Message sent by {site_title} ({site_url})
    This is an automated message. Please do not reply to this email.
    '''
    return email_body


def _compose_email_body_for_editors(user, package_dict, state, rejection_reason=None):
    pkg_link = toolkit.url_for('dataset.read', id=package_dict['name'], qualified=True)
    editor_name = user.fullname or user.name
    site_title = config.get('ckan.site_title')
    site_url = config.get('ckan.site_url')
    package_title = package_dict.get('title')
    package_url = pkg_link

    approval_paragraph = f"Your dataset '{package_title}' has been approved and published."
    rejection_paragraph = (
        f"Your dataset '{package_title}' has been reviewed and rejected by the reviewer. "
        f"Please see the following feedback. You can update the dataset and resubmit it for further review.\n\n"
        f"Feedback:\n'{rejection_reason}'"
    )
    
    email_body = (
        f"Dear {editor_name.title()},\n\n"
        f"{approval_paragraph if state == 'approved' else rejection_paragraph}\n\n"
        f"To view your dataset, please visit the following page:\n\n"
        f"{package_url}\n\n"
        f"--\n"
        f"Message sent by {site_title} ({site_url})\n"
        f"This is an automated message. Please do not reply to this email. If you have any questions, please contact the site administrator."
    )
    return email_body
