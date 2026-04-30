from ckanext.datasetapproval import models
from ckanext.datasetapproval.models import WorkflowAction, ReviewComment, WorkflowHistoryEntry
from .enums import review_outcome_mapping, WorkflowActionType
import logging

log = logging.getLogger(__name__)

def get_workflow_actions(dataset_id: str) -> list[WorkflowHistoryEntry]:
    '''
    Get all review actions and comments for a given dataset
    '''
    if not dataset_id or not isinstance(dataset_id, str):
        log.warning("Dataset ID is missing or invalid when trying to retrieve workflow actions")
        return []
    
    actions : list[WorkflowAction] = retrieve_workflow_actions(dataset_id)
    comments : list[ReviewComment] = retrieve_workflow_comments(dataset_id)

    # Workflow actions and comments combined into a single object, with the comments nested under the relevant workflow action
    workflow_actions_with_comments : list[WorkflowHistoryEntry] = []
    for action in actions:
        review_comment : ReviewComment | None = next((c for c in comments if c.workflow_action_id == action.id), None)
        workflow_actions_with_comments.append(WorkflowHistoryEntry(action, review_comment))

    return workflow_actions_with_comments

def retrieve_workflow_actions(dataset_id: str) -> list[WorkflowAction]:
    try: 
        actions = models.meta.Session.query(WorkflowAction).filter_by(dataset_id=dataset_id).order_by(WorkflowAction.submitted_date.desc()).all()
        return actions
    except Exception as e:
        log.error(f"Error retrieving workflow actions for dataset {dataset_id}: {e}")
        return []

def retrieve_workflow_comments(dataset_id: str) -> list[ReviewComment]:
    try:
        comments = models.meta.Session.query(ReviewComment).filter_by(dataset_id=dataset_id).all()
        return comments
    except Exception as e:
        log.error(f"Error retrieving workflow comments for dataset {dataset_id}: {e}")
        return []

def get_workflow_action_comment(historical_action : WorkflowHistoryEntry) -> str:
    '''
    Get the relevant comment for a given workflow action, and format it for display
    '''
    if not historical_action or not hasattr(historical_action, 'action'):
        log.warning("Workflow action is missing or does not have an 'action' attribute")
        return '' 

    action_type : str = getattr(historical_action.action, 'workflow_action', '').lower()
    comment : ReviewComment | None = getattr(historical_action, 'comment', None)
    display_comment : str = ''

    if action_type == WorkflowActionType.REJECT.value and comment is not None:
        reason : str = getattr(comment, 'rejection_reason', '') or ''
        reason_comments : str = getattr(comment, 'rejection_reason_comments', '') or ''
        display_comment = f"Rejection reason: '{reason.capitalize()}'. {reason_comments.capitalize()}"
    elif action_type == WorkflowActionType.APPROVE.value and comment is not None:
        display_comment : str = getattr(comment, 'approval_outcome_comments', '') or ''
        display_comment = display_comment.capitalize()

    return display_comment

def map_workflow_action_to_decision_type(workflow_action : WorkflowHistoryEntry) -> str:
    '''
    Map a workflow action to a user readable decision type. E.g. if the workflow action is 'approve' then the decision type would be 'approved'. 
    '''

    if not workflow_action or not hasattr(workflow_action, 'action'):
        log.warning("Workflow action is missing or does not have an 'action' attribute")
        return ''

    try:
        workflow_action_type : WorkflowActionType = WorkflowActionType(getattr(workflow_action.action, 'workflow_action', ''))
    except ValueError:
        log.warning(f"Workflow action {getattr(workflow_action.action, 'workflow_action', '')} not found in WorkflowActionType enum")
        return ''

    return review_outcome_mapping.get(workflow_action_type, '').capitalize()