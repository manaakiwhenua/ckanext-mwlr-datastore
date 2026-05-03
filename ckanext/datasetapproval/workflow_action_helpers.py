from ckanext.datasetapproval import models
from ckanext.datasetapproval.models import WorkflowAction, ReviewComment, WorkflowHistoryEntry
from .enums import review_outcome_mapping, WorkflowActionType, VOCAB_ENUMS
import logging

log = logging.getLogger(__name__)

def format_workflow_action_comment(historical_action : WorkflowHistoryEntry) -> str:
    '''
    Get the relevant comment for a given workflow action and format it for display
    '''
    if not historical_action or not hasattr(historical_action, 'action'):
        log.warning("Workflow action is missing or does not have an 'action' attribute")
        return '' 

    action_type : str = historical_action.action.get('workflow_action', '').lower()
    comment : ReviewComment | None = historical_action.comment
    display_comment : str = ''

    if action_type == WorkflowActionType.REJECT.value and historical_action.comment is not None:
        rejection_reason : str = comment.get('rejection_reason', '') or ''
        rejection_reason_comments : str = comment.get('rejection_reason_comments', '') or ''
        display_reason : str = getattr(VOCAB_ENUMS.rejection_reason, rejection_reason, '')        
        display_comment = f"Rejection reason: '{display_reason}'. {rejection_reason_comments.capitalize()}"
    elif action_type == WorkflowActionType.APPROVE.value and comment is not None:
        approval_type : str = getattr(VOCAB_ENUMS.approval_outcome, comment.get('approval_outcome', ''), '') or ''
        approval_condition_details : str = comment.get('approval_details', '') or ''
        approval_outcome_comments : str = comment.get('approval_outcome_comments', '') or ''

        display_comment = [approval_type.capitalize(), approval_outcome_comments.capitalize(), approval_condition_details.capitalize()]
        display_comment = '. '.join([c for c in display_comment if c != '']) 

    return display_comment

def map_workflow_action_to_decision_type(workflow_action : WorkflowHistoryEntry) -> str:
    '''
    Map a workflow action to a user readable decision type. E.g. if the workflow action is 'approve' then the decision type would be 'approved'. 
    '''

    if not workflow_action or not hasattr(workflow_action, 'action'):
        log.warning("Workflow action is missing or does not have an 'action' attribute")
        return ''

    try:
        workflow_action_type : WorkflowActionType = WorkflowActionType(workflow_action.action.get('workflow_action', '').lower())
    except ValueError:
        log.warning(f"Workflow action {workflow_action.action.get('workflow_action', '')} not found in WorkflowActionType enum")
        return ''

    return review_outcome_mapping.get(workflow_action_type, '').capitalize()