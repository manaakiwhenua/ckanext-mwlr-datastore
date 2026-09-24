from sqlalchemy import Column, UnicodeText, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from ckan.plugins import toolkit
import ckan.model.meta as meta
import datetime as dt
import uuid


class RestrictedResourceAccess(toolkit.BaseModel):
    __tablename__ = 'restricted_resource_access'
    __table_args__ = (UniqueConstraint('resource_id', 'user_id', name='uq_resource_user'),)

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False)
    resource_id = Column(UUID(as_uuid=True), ForeignKey('resource.id'), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False, index=True)
    granted_by_user_id = Column(UUID(as_uuid=True), ForeignKey('user.id'), nullable=False)
    created_at = Column(DateTime, default=dt.datetime.now(dt.timezone.utc), nullable=False)

    def as_dict(self):
        return {
            'id': self.id,
            'resource_id': self.resource_id,
            'user_id': self.user_id,
            'granted_by_user_id': self.granted_by_user_id,
            'created_at': self.created_at,
        }