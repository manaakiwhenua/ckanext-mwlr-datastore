from sqlalchemy import Column, UnicodeText, DateTime, ForeignKey, UniqueConstraint
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, insert
from ckan.plugins import toolkit
import uuid
from sqlalchemy.sql import func
import ckan.model.meta as meta
from typing import List


class RestrictedResourceAccess(toolkit.BaseModel):
    __tablename__ = "restricted_resource_access"
    __table_args__ = (UniqueConstraint("resource_id", "user_id", name="uq_resource_user"),)

    id = Column(UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid.uuid4)
    resource_id = Column(UnicodeText, ForeignKey("resource.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UnicodeText, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)
    granted_by_user_id = Column(
        UnicodeText, ForeignKey("user.id"), nullable=False
    )  # No CASCADE. We don't want to be able to delete any users who granted access, so we have the records for audit purposes
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)

    @classmethod
    def find_resource_access(cls, resource_id: str) -> List[RestrictedResourceAccess]:
        items = meta.Session.execute(
            sa.select(cls).where(cls.resource_id == resource_id)
        )
        return [e[0] for e in items]

    @classmethod
    def create(cls, items: List[dict]):
        """
        Create restricted_resource_access records for a given list of items.
        :param items:
        :return:
        """
        return meta.Session.execute(
            sa.insert(cls.__table__),
            items,
        )

    @classmethod
    def update_resource_access(cls, resource_id: str, user_ids: List[str], granted_by_user_id: str):
        """
        Update restricted_resource_access records for a given resource_id so
        that all user_ids have been granted access.

        Any restricted_resource_access for resource_id where the user_id is not in user_ids
        gets deleted.

        Newly created records will use the granted_by_user_id param, for existing records,
        granted_by_user_id will not be modified.
        :param resource_id:
        :param user_ids:
        :param granted_by_user_id:
        :return:
        """
        user_ids = set(user_ids)
        table = cls.__table__
        meta.Session.execute(
            sa.delete(table).where(
                table.c.resource_id == resource_id,
                table.c.user_id.notin_(user_ids),
            )
        )
        if user_ids:
            statement = insert(table).values([
                {
                    "resource_id": resource_id,
                    "user_id": user_id,
                    "granted_by_user_id": granted_by_user_id,
                }
                for user_id in user_ids
            ])
            meta.Session.execute(
                statement.on_conflict_do_nothing(constraint="uq_resource_user")
            )

    @classmethod
    def delete_resource_access(cls, resource_id: str):
        """
        Delete all restricted_resource_access records for a given resource_id
        :param resource_id:
        :return:
        """
        meta.Session.execute(
            sa.delete(cls.__table__).where(cls.__table__.c.resource_id == resource_id)
        )

    def as_dict(self):
        return {
            "id": str(self.id),
            "resource_id": self.resource_id,
            "user_id": self.user_id,
            "granted_by_user_id": self.granted_by_user_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
