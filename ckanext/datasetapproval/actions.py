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
    admin_editing = context.get("admin_editing", False)
    save_as_draft = context.get("save_as_draft", False)

    if data_dict.get("currently_reviewing"):
        data_dict.pop("currently_reviewing")
        if data_dict.get("publishing_status") == "approved":
            data_dict["private"] = data_dict.get("chosen_visibility", "true") == "true"
        elif data_dict.get("publishing_status") == "rejected":
            data_dict["private"] = "true"
    elif admin_editing:
        #if it is an admin and the dataset is being updated (not created)
        old_data_dict = toolkit.get_action("package_show")(
            context, {"id": data_dict.get("id")}
        )
        data_dict["publishing_status"] = old_data_dict.get("publishing_status")
        data_dict["chosen_visibility"] = data_dict.get("private", "true")
    else:
        if save_as_draft:
            #mail_package_review_request_to_admins(context, data_dict)
            data_dict['publishing_status'] = "draft"
        else:
            data_dict['publishing_status'] = "in_review"
    return data_dict


@toolkit.chained_action
@logic.side_effect_free
def package_show(up_func, context, data_dict):
    toolkit.check_access('package_show_with_approval', context, data_dict)
    return up_func(context, data_dict)

@toolkit.chained_action
@logic.side_effect_free
def package_create(up_func, context, data_dict):
    ## log.debug(f"data_dict before publishing_check (package_create): {data_dict}")
    publishing_check(context, data_dict)
    result = up_func(context, data_dict)
    ## log.debug(f"data_dict after publishing_check (package_create): {data_dict}")
    return result


@toolkit.chained_action
@logic.side_effect_free
def package_update(up_func, context, data_dict):
    ## log.debug(f"data_dict before publishing_check (package_update ): {data_dict}")
    publishing_check(context, data_dict)
    result = up_func(context, data_dict)
    ## log.debug(f"data_dict after publishing_check (package_update ): {data_dict}")
    return result


@toolkit.chained_action
@logic.side_effect_free
def package_patch(up_func, context, data_dict):
    ## log.debug(f"data_dict before publishing_check (package_patch): {data_dict}")
    publishing_check(context, data_dict)
    result = up_func(context, data_dict)
    ## log.debug(f"data_dict after publishing_check (package_patch): {data_dict}")
    return result