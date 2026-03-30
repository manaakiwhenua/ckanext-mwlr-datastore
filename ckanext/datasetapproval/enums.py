from enum import Enum

VOCABS = {
    "rejection_reason": {
        "data_quality": "Data quality issues",
        "documentation": "Incomplete or inadequate documentation",
        "legal": "Legal / contractual restrictions",
        "cultural": "Cultural / ethical concerns",
        "privacy": "Privacy / sensitivity issues",
        "ip": "IP / commercial risk",
        "sop": "Non-compliance with SOP",
        "other": "Other",
    },
    "compliance_status": {
        "non_compliant": "Non-compliant",
        "compliant": "Compliant",
        "partial": "Partially compliant",
    },
    "approval_outcome": {
        "approved": "Approved",
        "conditional": "Conditional Approval"
    }
}

class ReviewDecisionType(Enum):
    APPROVE = 'approve'
    REJECT = 'reject'

# Mapping of reviewer decisions to the publishing status of the dataset after review
review_outcome_mapping = {
        ReviewDecisionType.REJECT: 'rejected',
        ReviewDecisionType.APPROVE: 'approved'
    }