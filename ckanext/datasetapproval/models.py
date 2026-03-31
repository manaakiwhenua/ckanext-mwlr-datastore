from sqlalchemy import Column, UnicodeText, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from ckan.plugins import toolkit
import ckan.model.meta as meta
import datetime as dt
import uuid
from ckanext.datasetapproval.enums import ReviewActionType, ReviewerType
import logging as log
log = log.getLogger(__name__)

class ReviewAction(toolkit.BaseModel):
    __tablename__ = 'review_action'
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    dataset_id = Column(UnicodeText, ForeignKey('package.id'), nullable=False, index=True)
    reviewer_action = Column(UnicodeText)  # 'approve' or 'reject'. Possibility of future actions like 'recommend for approval' or 'request changes'
    reviewer_name = Column(UnicodeText)
    reviewer_email = Column(UnicodeText)
    review_date = Column(DateTime)    
    reviewer_type = Column(UnicodeText) # 'for now this will just be 'reviewer' - allows for the possibility of different types of reviewers in the future
    submitted_date = Column(DateTime(timezone=True))
    submitted_by_user_id = Column(UnicodeText, ForeignKey('user.id'), nullable=False)

class ReviewComment(toolkit.BaseModel):
    __tablename__ = 'review_comments'
    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    review_action_id = Column(UnicodeText, ForeignKey('review_action.id'), nullable=False)
    dataset_id = Column(UnicodeText, ForeignKey('package.id'), nullable=False, index=True)
    compliance_status = Column(UnicodeText)
    rejection_reason = Column(UnicodeText)
    rejection_reason_comments = Column(UnicodeText)
    review_type = Column(UnicodeText)
    approval_type = Column(UnicodeText)
    resubmission_comments = Column(UnicodeText)
    approval_outcome = Column(UnicodeText)
    approval_outcome_comments = Column(UnicodeText)

def save_reviewer_action_and_comments(dataset_id, feedback : dict[str, any], review_action_type : ReviewActionType):
    try:        
        review_action = create_review_action(dataset_id, feedback, review_action_type)
        review_comment = create_review_comment(dataset_id, feedback, review_action.id)
        meta.Session.add(review_action)
        meta.Session.add(review_comment)
        meta.Session.commit()
    except Exception as e:
        log.error(f"Error saving reviewer actions and comments: {e}")
        meta.Session.rollback()

def create_review_action(dataset_id, feedback : dict[str, any], review_action_type : ReviewActionType):
    reviewer_name = feedback.get("feedback_name", "")
    reviewer_email = feedback.get("feedback_email", "")
    review_date = feedback.get("feedback_date", None)

    review_action = ReviewAction(
        id = uuid.uuid4(),
        dataset_id=dataset_id,
        reviewer_name=reviewer_name,
        reviewer_email=reviewer_email,  
        reviewer_action=review_action_type.value,
        reviewer_type = ReviewerType.REVIEWER.value,
        submitted_date=dt.datetime.now(dt.timezone.utc),
        submitted_by_user_id=toolkit.c.userobj.id,
        review_date=review_date
    )
    return review_action

def create_review_comment(dataset_id, feedback : dict[str, any], review_action_id):
    approval_outcome_comments = feedback.get("approval_outcome_comments", None)
    if approval_outcome_comments and approval_outcome_comments.isspace():
        approval_outcome_comments = None

    review_comment = ReviewComment(
        id = uuid.uuid4(),
        review_action_id = review_action_id,
        dataset_id = dataset_id,
        compliance_status = feedback.get("compliance_status", None),
        review_type = feedback.get("review_type", None),
        approval_type = feedback.get("approval_type", None),
        rejection_reason = feedback.get("rejection_reason", None),
        rejection_reason_comments = feedback.get("rejection_reason_comments", None),
        resubmission_comments = feedback.get("resubmission_comments", None),
        approval_outcome = feedback.get("approval_outcome", None),
        approval_outcome_comments = approval_outcome_comments
    )
    return review_comment