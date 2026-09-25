from sqlalchemy import Column, UnicodeText, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from ckan.plugins import toolkit
import uuid
from sqlalchemy.sql import func


class RestrictedResourceAccess(toolkit.BaseModel):
    __tablename__ = 'restricted_resource_access'
    __table_args__ = (UniqueConstraint('resource_id', 'user_id', name='uq_resource_user'),)

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    resource_id = Column(UnicodeText, ForeignKey('resource.id', ondelete='CASCADE'), nullable=False)
    user_id = Column(UnicodeText, ForeignKey('user.id', ondelete='CASCADE'), nullable=False, index=True)
    granted_by_user_id = Column(UnicodeText, ForeignKey('user.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    def as_dict(self):
        return {
            'id': str(self.id),
            'resource_id': self.resource_id,
            'user_id': self.user_id,
            'granted_by_user_id': self.granted_by_user_id,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }