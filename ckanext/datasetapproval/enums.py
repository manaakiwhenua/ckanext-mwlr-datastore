from enum import Enum

class RejectionReason(str, Enum):
    data_quality = "Data quality issues"
    documentation = "Incomplete or inadequate documentation"
    legal = "Legal / contractual restrictions"
    cultural = "Cultural / ethical concerns"
    privacy = "Privacy / sensitivity issues"
    ip = "IP / commercial risk"
    sop = "Non-compliance with SOP"
    other = "Other"

class ApprovalOutcome(str, Enum):
    approved = "Approved"
    conditional = "Approved with conditions"

class ComplianceStatus(str, Enum):
    non_compliant = "Non-compliant"
    compliant = "Compliant"
    partial = "Partially compliant"

class ReviewType(str, Enum):
    metadata_documentation = "Metadata and Documentation Only Review"
    scientific_technical = "Scientific and Technical Review"

class ApprovalType(str, Enum):
    minimal = "Minimal Approval (\"Sign-off only\")"
    compliance = "Approver Compliance Check"

class VOCAB_ENUMS:
    rejection_reason = RejectionReason
    approval_outcome = ApprovalOutcome
    compliance_status = ComplianceStatus
    review_type = ReviewType
    approval_type = ApprovalType