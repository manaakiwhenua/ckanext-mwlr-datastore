import logging
import ckan.authz as authz

from ckan.lib.mailer import MailerException
import ckan.plugins.toolkit as tk
import ckan.plugins as p
import ckan.logic as logic

from ckanext.datasetapproval.mailer import mail_package_review_request_to_admins 

log = logging.getLogger(__name__)

def is_user_editor_of_org(org_id, user_id):
    capacity = authz.users_role_for_group_or_org(org_id, user_id)
    return capacity == "editor"

def publishing_check(context, data_dict):
    admin_editing = context.get("admin_editing", False)
    submit_review = context.get("submit_review", False)
    user_id = (
        tk.current_user.id
        if tk.current_user and not tk.current_user.is_anonymous
        else None
    )
    org_id = data_dict.get("owner_org")

    ## if the dataset being created/updated is currently under review the status will be either "approved" or "rejected"
    if data_dict.get("currently_reviewing"):
        data_dict.pop("currently_reviewing")
        rejection_reason = context.get("rejection_reason", None)
        data_dict = set_visibility_on_approval_or_rejection(data_dict)      
    ## if the dataset is being updated by an admin then should bypass the approval state
    elif admin_editing and data_dict.get("id"):
        old_data_dict = tk.get_action("package_show")(
            context, {"id": data_dict.get("id")}
        )
        ## if the dataset is currently in review, should remain in review and visibility should be whatever the admin has set it to
        if old_data_dict.get("publishing_status") == "in_review":
            data_dict["publishing_status"] = old_data_dict.get("publishing_status")
        data_dict["chosen_visibility"] = data_dict.get("private", "true")
    ## if the dataset is being created/updated by an editor then status must be set to "in_review" unless they are saving as a draft
    elif is_user_editor_of_org(org_id, user_id):
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
                "Review request sent to collection reviewers. You will be notified by email of approval or rejection."
            )
        except MailerException:
            log.exception("%s: mail send failed", action_name)
            tk.h.flash_error(
                "Unable to send review request to collection reviewers. Please contact an administrator."
            )
    return result

@tk.chained_action
def package_show(up_func, context, data_dict):
    tk.check_access('package_show_with_approval', context, data_dict)
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