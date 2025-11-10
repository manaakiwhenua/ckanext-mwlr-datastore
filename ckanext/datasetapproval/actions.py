import logging
import ckan.authz as authz

from ckan.lib.mailer import MailerException
from ckan.plugins import toolkit
import ckan.plugins as p
import ckan.logic as logic

from ckanext.datasetapproval.mailer import mail_package_review_request_to_admins

log = logging.getLogger(__name__)

def is_unowned_dataset(owner_org):
    return (
        not owner_org
        and authz.check_config_permission("create_dataset_if_not_in_organization")
        and authz.check_config_permission("create_unowned_dataset")
    )


def is_user_editor_of_org(org_id, user_id):
    capacity = authz.users_role_for_group_or_org(org_id, user_id)
    return capacity == "editor"


def is_user_admin_of_org(org_id, user_id):
    capacity = authz.users_role_for_group_or_org(org_id, user_id)
    return capacity == "admin"

def publishing_check(context, data_dict):
    log.debug("publishing_check called")
    log.debug(f"checking context {context}")
    user_id = (
        toolkit.current_user.id
        if toolkit.current_user and not toolkit.current_user.is_anonymous
        else None
    )
    org_id = data_dict.get("owner_org")

    is_user_editor = is_user_editor_of_org(org_id, user_id)
    is_user_admin = is_user_admin_of_org(org_id, user_id)
    is_sysadmin = hasattr(toolkit.current_user, "sysadmin") and toolkit.current_user.sysadmin

    admin_editing = context.get("admin_editing", False)
    save_as_draft = context.get("save_as_draft", False)
    log.debug(f"checking key publishing status {data_dict.get('publishing_status')}")
    log.debug(f"admin editing {admin_editing}")
    log.debug(f"saving as draft {save_as_draft}")
    log.debug(f"current reviewing status: {data_dict.get('currently_reviewing')}")
    log.debug(f"is user editor: {is_user_editor}, is user admin: {is_user_admin}, is sysadmin: {is_sysadmin}")
    if data_dict.get("currently_reviewing"):
        log.debug("removing currently_reviewing flag from data_dict")
        data_dict.pop("currently_reviewing")
        if data_dict.get("publishing_status") == "approved":
            data_dict["state"] = "active"
        elif data_dict.get("publishing_status") == "rejected":
            data_dict["state"] = "draft"
    elif admin_editing:
        #if it is an admin and the dataset is being updated (not created)
        old_data_dict = toolkit.get_action("package_show")(
            context, {"id": data_dict.get("id")}
        )
        if (is_user_admin or is_sysadmin) and old_data_dict.get("publishing_status") == "in_review":
            data_dict["publishing_status"] = old_data_dict.get("publishing_status")
        else:
            data_dict['publishing_status'] = "approved"
            data_dict["state"] = "active"
    elif (is_user_editor or is_unowned_dataset(org_id)):
        if save_as_draft:
            log.debug("saving as draft")
            #mail_package_review_request_to_admins(context, data_dict)
            data_dict['publishing_status'] = "draft"
            data_dict["state"] = "draft"
        else:
            data_dict['publishing_status'] = "in_review"
            data_dict["state"] = "draft"
    return data_dict


@toolkit.chained_action
@logic.side_effect_free
def package_show(up_func, context, data_dict):
    toolkit.check_access('package_show_with_approval', context, data_dict)
    return up_func(context, data_dict)

@toolkit.chained_action
@logic.side_effect_free
def package_create(up_func, context, data_dict):
    log.debug("package_create called")
    log.debug(f"data_dict before publishing_check: {data_dict}")
    publishing_check(context, data_dict)
    result = up_func(context, data_dict)
    log.debug(f"data_dict after publishing_check: {data_dict}")
    return result


@toolkit.chained_action
@logic.side_effect_free
def package_update(up_func, context, data_dict):
    log.debug("package_update called")
    log.debug(f"package_update data_dict before publishing_check: {data_dict}")
    publishing_check(context, data_dict)
    result = up_func(context, data_dict)
    log.debug(f"package_update data_dict after publishing_check: {data_dict}")
    return result


@toolkit.chained_action
@logic.side_effect_free
def package_patch(up_func, context, data_dict):
    log.debug("package_patch called")
    log.debug(f"package_patch data_dict before publishing_check: {data_dict}")
    publishing_check(context, data_dict)
    result = up_func(context, data_dict)
    log.debug(f"package_patch data_dict after publishing_check: {data_dict}")
    return result