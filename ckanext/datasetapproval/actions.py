import logging
import ckan.authz as authz
from ckanext.datasetapproval import models
from ckanext.datasetapproval.models import WorkflowAction, ReviewComment, WorkflowHistoryEntry
from ckan.lib.mailer import MailerException
import ckan.plugins.toolkit as tk
import ckan.plugins as p
import ckan.logic as logic
from ckan.lib.helpers import helper_functions as h
from .enums import ReviewType

from ckanext.datasetapproval.mailer import mail_package_review_request_to_admins 

log = logging.getLogger(__name__)

def is_user_editor_of_org(org_id, user_id):
    capacity = authz.users_role_for_group_or_org(org_id, user_id)
    return capacity == "editor"

def publishing_check(context, data_dict):
    admin_editing = context.get("admin_editing", False)
    submit_review = context.get("submit_review", False)
    bypass_review = context.get("bypass_review", False)
    user_id = (
        tk.current_user.id
        if tk.current_user and not tk.current_user.is_anonymous
        else None
    )
    org_id = data_dict.get("owner_org")

    ## if the dataset being created/updated is currently under review the status will be either "approved" or "rejected"
    if data_dict.get("currently_reviewing"):
        data_dict.pop("currently_reviewing")
        data_dict = set_visibility_on_approval_or_rejection(data_dict)      
    ## if the dataset is being created/updated by an admin then should bypass the review and move to "approved"
    elif admin_editing:
        data_dict["publishing_status"] = "approved"
        data_dict = set_visibility_on_approval_or_rejection(data_dict)
    ## if the dataset is being created/updated by an editor then status must be set to "in_review" unless they are saving as a draft or only changing visibility
    elif is_user_editor_of_org(org_id, user_id):
        # need this check here still to ensure it stays approved
        if bypass_review == True:
            data_dict = set_visibility_on_approval_or_rejection(data_dict)
        else:
            context.update({'send_request': submit_review})
            if submit_review:
                data_dict['publishing_status'] = "in_review"
            else:
                data_dict["private"] = "true"
                data_dict['publishing_status'] = "in_progress"
    return data_dict

def set_visibility_on_approval_or_rejection(data_dict):
    ## if approved, then the visibility is set to whatever the creator (editor) of the dataset chose
    if data_dict.get("publishing_status") == "approved":
        data_dict["private"] = data_dict.get("chosen_visibility", "true") == "true"
    ## if rejected, the visibility should be private
    elif data_dict.get("publishing_status") == "rejected":
        data_dict["private"] = "true"

    return data_dict

def _wrap_publish_review(up_func, context, data_dict, *, action_name):
    log.debug("%s: checking publishing status", action_name)
    publishing_check(context, data_dict)

    try:
        result = up_func(context, data_dict)
    except Exception:
        log.exception("%s: action failed", action_name)
        raise

    if context.get('send_request', False):
        try:
            mail_package_review_request_to_admins(context, data_dict)
            tk.h.flash_success(
                "Review request sent to collection admins. You will be notified by email of the review outcome."
            )
        except MailerException:
            log.exception("%s: mail send failed", action_name)
            tk.h.flash_error(
                "Unable to send review request to collection admins. Please contact the datastore administrator."
            )
    return result

@tk.side_effect_free
def workflow_actions_show(context, data_dict) -> list[WorkflowHistoryEntry]:
    """
    Get all reviewer actions and comments for a given dataset

    Parameters:
        context (dict): the CKAN action context, not used in this function but required as a parameter
        data_dict (dict): a dictionary containing the dataset ID and owner organization ID.E.g. {'id': '1234', 'owner_org': '5678'}
    """
    dataset_id = tk.get_or_bust(data_dict, "id")

    if not dataset_id or not isinstance(dataset_id, str):
        log.warning("Dataset ID is missing or invalid when trying to retrieve workflow actions")
        return []
    
    tk.check_access('workflow_history_show', context, data_dict)    
    actions : list[WorkflowAction] = WorkflowAction.get_actions_for_dataset(dataset_id)
    comments : list[ReviewComment] = ReviewComment.get_comments_for_dataset(dataset_id)

    # Workflow actions and comments combined into a single object, with the comments nested under the relevant workflow action
    workflow_actions_with_comments : list[WorkflowHistoryEntry] = []
    for action in actions:
        review_comment : ReviewComment | None = next((c for c in comments if c.workflow_action_id == action.id), None)
        workflow_actions_with_comments.append(WorkflowHistoryEntry(action, review_comment))
    return workflow_actions_with_comments
  
@tk.side_effect_free    
def latest_workflow_action_show(context, data_dict) -> WorkflowHistoryEntry | None:
    '''
    Get only the most recent workflow action for a given dataset. Doesn't require permissions check or workflow action comments.
    '''
    dataset_id = tk.get_or_bust(data_dict, "id")
    if not dataset_id or not isinstance(dataset_id, str):
        log.warning("Dataset ID is missing or invalid when trying to retrieve latest workflow action")
        return None
    workflow_action = WorkflowAction.get_latest_action_for_dataset(dataset_id)
    return WorkflowHistoryEntry(action=workflow_action, comment=None)

@tk.chained_action
@logic.side_effect_free
def package_show(up_func, context, data_dict):
    return up_func(context, data_dict)

@tk.chained_action
def package_create(up_func, context, data_dict):
    return _wrap_publish_review(up_func, context, data_dict, action_name="package_create")

@tk.chained_action
def package_update(up_func, context, data_dict):
    return _wrap_publish_review(up_func, context, data_dict, action_name="package_update")

@tk.chained_action
def package_patch(up_func, context, data_dict):
    return _wrap_publish_review(up_func, context, data_dict, action_name="package_patch")

@p.toolkit.chained_action   
def resource_create(up_func,context, data_dict):
    return _wrap_publish_review(up_func, context, data_dict, action_name="resource_create")

@p.toolkit.chained_action   
def resource_update(up_func,context, data_dict):
    return _wrap_publish_review(up_func, context, data_dict, action_name="resource_update")

@p.toolkit.side_effect_free
def check_user_admin(*args):
    user_id = tk.current_user.id
    org_id = tk.request.args.get("org_id")
    is_user_admin = h.is_admin(user_id, org_id)
    log.debug("check_user_admin: user_id=%r org_id=%r is_user_admin=%r", user_id, org_id, is_user_admin)
    return {"is_user_admin": is_user_admin}

@p.toolkit.side_effect_free
def retrieve_rejection_reasons(*args):
    review_type = tk.request.args.get("review_type")
    try:
        review_type_enum = ReviewType[review_type] if review_type else None
    except ValueError:
        review_type_enum = None
    rejection_reasons = h.get_vocab_group("rejection_reason")
    if review_type_enum == ReviewType.metadata_documentation:
        rejection_reasons.pop("data_quality", None)
    return rejection_reasons

@tk.side_effect_free
def retrieve_publishing_status(*args):
    package_id = tk.request.args.get("package_id")
    dataset_dict = tk.get_action('package_show') \
        ({u'ignore_auth': True}, {'id': package_id})
    tk.check_access('retrieve_publishing_status', {"user":tk.c.user}, dataset_dict)

    publishing_status = dataset_dict.get('publishing_status', None)
    if publishing_status is None:
        raise tk.ValidationError({
            'message': "publishing status not found on dataset."
        })
    
    return publishing_status