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
        display_reasons = format_rejection_reasons(comment.get('rejection_reasons', '') or '')
        rejection_reason_comments : str = comment.get('rejection_reason_comments', '') or ''
        display_comment = f"Rejection reasons: '{display_reasons}'. {rejection_reason_comments.capitalize()}"
    elif action_type == WorkflowActionType.APPROVE.value and comment is not None:
        approval_outcome : str = getattr(VOCAB_ENUMS.approval_outcome, comment.get('approval_outcome', ''), '') or ''
        approval_outcome_comments : str = comment.get('approval_outcome_comments', '') or ''
        approval_conditions_comments : str = comment.get('approval_conditions_comments', '') or ''
        
        display_comment = [approval_outcome.capitalize(), approval_outcome_comments.capitalize(), approval_conditions_comments.capitalize()]
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

def format_rejection_reasons(raw_rejection_reason: str | list[str]) -> str:
    if not raw_rejection_reason:
        return ""

    # handle being passed through either as a string or list of strings
    if isinstance(raw_rejection_reason, str):
        rejection_reasons = raw_rejection_reason.strip("{}").split(",")
    else:
        rejection_reasons = raw_rejection_reason

    reason_list = []
    for rejection_reason in rejection_reasons:
        enumerated_reason = getattr(VOCAB_ENUMS.rejection_reasons, rejection_reason, '')
        reason_list.append(enumerated_reason.value if enumerated_reason else rejection_reason)
    display_reasons = ", ".join(reason_list)
    return display_reasons or ''

def map_workflow_action_to_review_types(workflow_action : WorkflowHistoryEntry) -> str:
    if workflow_action.comment is None:
        return ''
    
    review_types_for_display = []
    review_types = workflow_action.comment.get('review_types', '')

    for review_type in review_types:
        enumerated_review_type = getattr(VOCAB_ENUMS.review_types, review_type, None)
        if enumerated_review_type:
            review_types_for_display.append(enumerated_review_type.value)

    return ", ".join(review_types_for_display) if review_types_for_display else ''

def get_helpers():
    return {
        'format_workflow_action_comment': format_workflow_action_comment,
        'map_workflow_action_to_decision_type': map_workflow_action_to_decision_type,
        'map_workflow_action_to_review_types': map_workflow_action_to_review_types,
    }