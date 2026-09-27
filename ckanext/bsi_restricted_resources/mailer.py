import logging
from ckan.lib.mailer import mail_recipient, MailerException

log = logging.getLogger(__name__)

def notify_dataset_owner_of_request(maintainer_email, package_id, package_title, dataset_url, requester, message):

    email_subject = f"Dataset access request for dataset {package_title}"
    email_lines = [
        f"User {requester['name']} ({requester['email']}) has requested access to the resources of the following dataset:", 
        f"Dataset: '{package_title}'", 
        f"Link: {dataset_url}."
    ]

    if message:
        email_lines.append(f"\n\nMessage from requester:\n{message}")

    email_body = "\n".join(email_lines)

    try:
        mail_recipient("Dataset owner", maintainer_email, email_subject, email_body)
    except MailerException as e:
        log.error(f"Failed to send access request email to {maintainer_email}: {e}")
        return {"success": False, "msg": "Failed to send access request email."}

    return {"success": True, "msg": "Access request email sent to dataset owner."}
