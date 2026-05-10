from sqlalchemy import Column, UnicodeText, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from ckan.plugins import toolkit
import ckan.model.meta as meta
import datetime as dt
import uuid
from ckanext.datasetapproval.enums import ReviewType, WorkflowActionType, ReviewerType
import logging as log
log = log.getLogger(__name__)

class WorkflowAction(toolkit.BaseModel):
    __tablename__ = 'workflow_action'
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    dataset_id = Column(UnicodeText, ForeignKey('package.id'), nullable=False, index=True)
    workflow_action = Column(UnicodeText)  # 'approve' or 'reject'. Possibility of future actions like 'recommend for approval' or 'request changes'
    reviewer_name = Column(UnicodeText)
    reviewer_email = Column(UnicodeText)
    review_date = Column(DateTime)    
    reviewer_type = Column(UnicodeText) # 'for now this will just be 'reviewer' - allows for the possibility of different types of reviewers in the future
    submitted_date = Column(DateTime(timezone=True))
    submitted_by_user_id = Column(UnicodeText, ForeignKey('user.id'), nullable=False)

    def as_dict(self):
        return {
            'id': str(self.id),
            'dataset_id': self.dataset_id,
            'workflow_action': self.workflow_action,
            'reviewer_name': self.reviewer_name,
            'reviewer_email': self.reviewer_email,
            'review_date': self.review_date,
            'reviewer_type': self.reviewer_type,
            'submitted_date': self.submitted_date,
            'submitted_by_user_id': self.submitted_by_user_id,
        }
    
    @classmethod
    def get_actions_for_dataset(cls, dataset_id: str) -> list['WorkflowAction']:
        try: 
            actions = meta.Session.query(cls).filter_by(dataset_id=dataset_id).order_by(WorkflowAction.submitted_date.desc()).all()
            return actions
        except Exception as e:
            log.error(f"Error retrieving workflow actions for dataset {dataset_id}: {e}")
            return []
        
    @classmethod
    def get_latest_action_for_dataset(cls, dataset_id: str) -> 'WorkflowAction':
        try:         
            action = meta.Session.query(cls).filter_by(dataset_id=dataset_id).order_by(WorkflowAction.submitted_date.desc()).first()
            return action
        except Exception as e:
            log.error(f"No workflow history, or error retrieving latest workflow action for dataset {dataset_id}: {e}")
            return None

class ReviewComment(toolkit.BaseModel):
    __tablename__ = 'review_comments'
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    workflow_action_id = Column(UUID(as_uuid=True), ForeignKey('workflow_action.id'), nullable=False)
    dataset_id = Column(UnicodeText, ForeignKey('package.id'), nullable=False, index=True)
    rejection_reasons = Column(UnicodeText)
    rejection_reason_comments = Column(UnicodeText)
    review_types = Column(UnicodeText)
    resubmission_comments = Column(UnicodeText)
    approval_outcome = Column(UnicodeText)
    approval_outcome_comments = Column(UnicodeText)
    approval_conditions_comments = Column(UnicodeText)
    condition_expiry_date = Column(DateTime)

    def as_dict(self):
        return {
            'id': str(self.id),
            'workflow_action_id': str(self.workflow_action_id),
            'dataset_id': self.dataset_id,
            'rejection_reasons': self.rejection_reasons.strip("{}").split(",") if isinstance(self.rejection_reasons, str) else [],
            'rejection_reason_comments': self.rejection_reason_comments,
            'review_types': self.review_types.strip("{}").split(",") if isinstance(self.review_types, str) else [],
            'resubmission_comments': self.resubmission_comments,
            'approval_outcome': self.approval_outcome,
            'approval_outcome_comments': self.approval_outcome_comments,
            'approval_conditions_comments': self.approval_conditions_comments,
            'condition_expiry_date': self.condition_expiry_date,
        }
    
    @classmethod
    def get_comments_for_dataset(cls, dataset_id: str) -> list['ReviewComment']:
        try:
            comments = meta.Session.query(cls).filter_by(dataset_id=dataset_id).all()
            return comments
        except Exception as e:
            log.error(f"Error retrieving review comments for dataset {dataset_id}: {e}")
            return []

class WorkflowHistoryEntry:
    def __init__(self, action: WorkflowAction, comment: ReviewComment | None):       
# This is a helper class to combine workflow actions and their associated comments for easier retrieval and display in the UI. SQLAlchemy models need to be converted to dictionaries before they can be used in html templates
        self.action = action.as_dict() if action else None
        self.comment = comment.as_dict() if comment else None

class ReviewRequest:
    review_type : ReviewType
    review_request_comments : str | None
    def __init__(self, review_type: ReviewType, review_request_comments: str | None = None):
        self.review_type = review_type
        self.review_request_comments = review_request_comments          

def save_workflow_action_and_comments(dataset_id, feedback : dict[str, any], workflow_action_type : WorkflowActionType):
    try:        
        workflow_action = create_workflow_action(dataset_id, feedback, workflow_action_type)
        review_comment = create_review_comment(dataset_id, feedback, workflow_action.id)
        meta.Session.add(workflow_action)
        meta.Session.flush()  # Generate the workflow_action.id for the review_comment foreign key
        meta.Session.add(review_comment)
        meta.Session.commit()
    except Exception as e:
        log.error(f"Error saving reviewer actions and comments: {e}")
        meta.Session.rollback()

def create_workflow_action(dataset_id, feedback : dict[str, any], workflow_action_type : WorkflowActionType):
    reviewer_name = feedback.get("feedback_name", "")
    reviewer_email = feedback.get("feedback_email", "")
    review_date = feedback.get("feedback_date", None)

    workflow_action = WorkflowAction(
        id = uuid.uuid4(),
        dataset_id=dataset_id,
        reviewer_name=reviewer_name,
        reviewer_email=reviewer_email,  
        workflow_action=workflow_action_type.value,
        reviewer_type = ReviewerType.REVIEWER.value,
        submitted_date= dt.datetime.now(dt.timezone.utc),
        submitted_by_user_id=toolkit.c.userobj.id,
        review_date=review_date
    )
    return workflow_action

def create_review_comment(dataset_id, feedback : dict[str, any], workflow_action_id):
    approval_outcome_comments = feedback.get("approval_outcome_comments", None)
    approval_conditions_comments = feedback.get("approval_conditions_comments", None)
    entered_date = feedback.get("condition_expiry_date", None)
    if approval_outcome_comments and approval_outcome_comments.isspace():
        approval_outcome_comments = None
    if approval_conditions_comments and approval_conditions_comments.isspace():
        approval_conditions_comments = None
    condition_expiry_date = entered_date or None

    review_comment = ReviewComment(
        id = uuid.uuid4(),
        workflow_action_id = workflow_action_id,
        dataset_id = dataset_id,
        review_types = feedback.get("review_types", None),
        rejection_reasons = feedback.get("rejection_reasons", None),
        rejection_reason_comments = feedback.get("rejection_reason_comments", None),
        resubmission_comments = feedback.get("resubmission_comments", None),
        approval_outcome = feedback.get("approval_outcome", None),
        approval_outcome_comments = approval_outcome_comments,
        approval_conditions_comments = approval_conditions_comments,
        condition_expiry_date = condition_expiry_date

    )
    return review_comment