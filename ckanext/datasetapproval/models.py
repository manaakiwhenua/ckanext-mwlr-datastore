from sqlalchemy import Column, UnicodeText, DateTime
from sqlalchemy.dialects.postgresql import UUID
from ckan.plugins import toolkit
import ckan.model.meta as meta
import datetime as dt
import uuid

class ReviewDecision(toolkit.BaseModel):
    __tablename__ = 'review_decision'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    dataset_id = Column(UnicodeText, nullable=False)
    review_date = Column(DateTime, default=dt.datetime.now(dt.timezone.utc))
    decision = Column(UnicodeText)  # 'approved' or 'rejected'
    reviewer_name = Column(UnicodeText)
    reviewer_email = Column(UnicodeText)
    reviewer_comments = Column(UnicodeText)
    submitted_by_user_id = Column(UnicodeText)


def save_reviewer_decision(dataset_id, reviewer_comments, reviewer_name, reviewer_email, decision):
    decision = ReviewDecision(
        dataset_id=dataset_id,
        reviewer_name=reviewer_name,
        reviewer_email=reviewer_email,  
        decision=decision,
        reviewer_comments=reviewer_comments,
        submitted_by_user_id=toolkit.c.userobj.id,
    )
    meta.Session.add(decision)
    meta.Session.commit()