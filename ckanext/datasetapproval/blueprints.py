import logging
from functools import partial

from flask import Blueprint

from ckan import model
from ckan.lib import base
from ckan.plugins import toolkit
import ckan.lib.base as base
from ckan.views.user import _extra_template_variables
import ckan.lib.helpers as h
from ckan.lib.helpers import helper_functions as helpers
from ckan.authz import users_role_for_group_or_org
from ckan.lib.mailer import MailerException
from ckanext.datasetapproval.mailer import mail_package_approve_reject_notification_to_editors, _compose_email_body_for_editors
from ckan.views.dataset import url_with_params
from typing import Union
from ckan.types import Response

log = logging.getLogger(__name__)


approveBlueprint = Blueprint('approval', __name__,)


def _pager_url(params_nopage, package_type, q=None, page=None):
    params = list(params_nopage)
    params.append((u'page', page))
    return search_url(params, package_type)


def search_url(params, package_type=None):
    url = h.url_for('approval.dataset_review', id=toolkit.c.user)
    return url_with_params(url, params)


def approve(id):
    feedback = toolkit.request.form.to_dict()
    context: Context = {
        u'user': toolkit.c.user,
        u'auth_user_obj': toolkit.c.userobj,
        u'for_view': True
    }
    pkg = toolkit.get_action('package_show')(
            context,
            {'id': id}
        )
    body = _compose_email_body_for_editors(context, pkg, "approved", feedback)
    log.debug(f"APPROVAL FEEDBACK BODY: {body}")
    return _make_action(id, 'approve', feedback=feedback)

def reject(id):
    ## need to update this here
    ## update the package_extras with reviewer details
    ## update the package_extras with approval details
    ## update the package extras with publication date (if approved and heading towards being made public)
    ## store in the db (somewhere)
    feedback = toolkit.request.form.to_dict()
    ## update the package here with the reviewer details
    context: Context = {
        u'user': toolkit.c.user,
        u'auth_user_obj': toolkit.c.userobj,
        u'for_view': True
    }
    pkg = toolkit.get_action('package_show')(
            context,
            {'id': id}
        )
    ## add the reviewer and approver details to the dataset metadata
    pkg = helpers.add_reviewal_details_to_pkg(pkg, feedback.get("reviewer_name", ""), feedback.get("reviewer_email", ""))
    body = _compose_email_body_for_editors(context, pkg, "rejected", feedback)
    log.debug(f"REJECTION FEEDBACK BODY: {body}")
    toolkit.get_action('package_update')(
        context,
        pkg
    )
    return _make_action(id, 'reject', feedback=feedback)


def pending_datasets(id: str) -> Union[Response, str]:
    if toolkit.request.endpoint.endswith('dataset_review'):
        review_context = "admin_review"
    else:
        review_context = "editor_requests"
    context: Context = {
        u'user': toolkit.c.user,
        u'auth_user_obj': toolkit.c.userobj,
        u'for_view': True
    }
    data_dict: dict[str, Any] = {
        u'id': id,
        u'user_obj': toolkit.c.userobj,
        u'include_datasets': True,
        u'include_num_followers': True
    }

    extra_vars = _extra_template_variables(context, data_dict)

    params_nopage = [(k, v) for k, v in toolkit.request.args.items(multi=True)
                     if k != u'page']
    limit = 20
    page = h.get_page_number(toolkit.request.args)
    pager_url = partial(_pager_url, params_nopage, 'dataset')

    if review_context == "admin_review":
        fq_string = f'NOT creator_user_id:{toolkit.c.userobj.id} AND publishing_status:in_review'
    else:
        fq_string = f'creator_user_id:{toolkit.c.userobj.id} AND publishing_status:in_review'
    
    search_dict = {
        'rows': limit,
        'start': limit * (page - 1),
        'fq': fq_string,
        'include_private': True
        }

    in_review_datasets = toolkit.get_action('package_search')(context,
                                               data_dict=search_dict)
    
    extra_vars['user_dict'].update({
        'datasets' : in_review_datasets['results'],
        'total_count': in_review_datasets['count']
        })
    
    extra_vars[u'page'] = h.Page(
        collection = in_review_datasets['results'],
        page = page,
        url = pager_url,
        item_count = in_review_datasets['count'],
        items_per_page = limit
    )
    extra_vars[u'page'].items = in_review_datasets['results']
    return base.render(f'user/{review_context}.html', extra_vars)


def _raise_not_authz_or_not_pending(id):
    dataset_dict = toolkit.get_action('package_show') \
                    ({u'ignore_auth': True}, {'id': id})
    permission = users_role_for_group_or_org(dataset_dict.get('owner_org'), toolkit.c.userobj.name)
    is_pending = dataset_dict.get('publishing_status') == 'in_review'

    if is_pending and (toolkit.c.userobj.sysadmin or permission == 'admin'):
        return 
    else :
        raise toolkit.abort(404, 'Dataset "{}" not found'.format(id))

def _make_action(package_id, action='reject', feedback=None):
    states = {
        'reject': 'rejected',
        'approve': 'approved'
    }
    # grab the old dict
    set_private = action == 'reject'
    context = {
        'model': model,
        'user': toolkit.c.user,
        'ignore_auth': True,
        'feedback': feedback
    }
    # check access and state
    _raise_not_authz_or_not_pending(package_id)
    pkg = toolkit.get_action('package_show')(
            context,
            {'id': package_id}
        )
    try:
        pkg['publishing_status'] = states[action]
        if set_private:
            pkg['private'] = True
        toolkit.get_action('package_update')(
            context,
            pkg
        )
    except Exception as e:
        log.error('Error approving dataset %s: %s', package_id, str(e))
        h.flash_error("Unable to update publishing status of dataset. Ensure that the dataset metadata is valid via the \"Manage\" button.")
        return h.redirect_to(u'{}.read'.format('dataset'),
                             id=package_id)
    try:
        mail_package_approve_reject_notification_to_editors(package_id, pkg.get("publishing_status"),  feedback)
        toolkit.h.flash_success("Review response sent to dataset creator.")
    except MailerException as e:
        log.error(f"Failed to send review request email: {e}")
        toolkit.h.flash_error("Unable to send review response email to dataset creator. Please contact the datastore administrator.")
    return toolkit.redirect_to(controller='dataset', action='read', id=package_id)

approveBlueprint.add_url_rule('/dataset-publish/<id>/approve', view_func=approve)
approveBlueprint.add_url_rule('/dataset-publish/<id>/reject', view_func=reject, methods=['POST'])
approveBlueprint.add_url_rule(u'/user/<id>/dataset_review', view_func=pending_datasets, endpoint='dataset_review')
approveBlueprint.add_url_rule(u'/user/<id>/my_requests', view_func=pending_datasets, endpoint='my_requests')
