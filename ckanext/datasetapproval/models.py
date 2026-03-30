import json

from sqlalchemy import Column, UnicodeText, DateTime
from sqlalchemy.dialects.postgresql import UUID
from ckan.plugins import toolkit
import ckan.model.meta as meta
import datetime as dt
import uuid
from ckanext.datasetapproval.enums import ReviewDecisionType
import logging as log
log = log.getLogger(__name__)

class ReviewDecision(toolkit.BaseModel):
    __tablename__ = 'review_decision'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UnicodeText, nullable=False)
    timestamp = Column(DateTime, default=dt.datetime.now(dt.timezone.utc))
    decision = Column(UnicodeText)  # 'approve' or 'reject'
    reviewer_name = Column(UnicodeText)
    reviewer_email = Column(UnicodeText)
    review_date = Column(DateTime)
    compliance_status = Column(UnicodeText)  # 'compliant', 'non_compliant', 'partial'
    reviewer_comments = Column(UnicodeText)
    submitted_by_user_id = Column(UnicodeText)

def save_reviewer_decision(dataset_id, feedback : dict[str, any], decision_type : ReviewDecisionType):
    try:
        # make a feedback blob out of the feedback dict
        reviewer_feedback_json = json.dumps(feedback)
        reviewer_name = feedback.get("reviewer_name", "") or feedback.get("approver_name", "")
        reviewer_email = feedback.get("reviewer_email", "") or feedback.get("approver_email", "")
        review_date = feedback.get("review_date", None) or feedback.get("approve_date", None) or dt.datetime.now(dt.timezone.utc)

        review_decision = ReviewDecision(
            dataset_id=dataset_id,
            reviewer_name=reviewer_name,
            reviewer_email=reviewer_email,  
            decision=decision_type.value,
            compliance_status=feedback.get("compliance_status", ""),
            reviewer_comments=reviewer_feedback_json,
            submitted_by_user_id=toolkit.c.userobj.id,
            review_date=review_date
        )
        meta.Session.add(review_decision)
        meta.Session.commit()
    except Exception as e:
        log.error(f"Error saving reviewer decision: {e}")
        meta.Session.rollback()