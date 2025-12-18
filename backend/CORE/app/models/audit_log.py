"""
Audit Log Model - Track all data changes for compliance and debugging.
Production-grade logging for LLM context and security.
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index, TypeDecorator
import uuid
import json
from datetime import datetime
from app.database import Base


class GUIDType(TypeDecorator):
    """Platform-independent GUID type."""
    impl = String(36)
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return str(value)
        return value
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return uuid.UUID(value) if isinstance(value, str) else value
        return value


class JSONType(TypeDecorator):
    """Platform-independent JSON type."""
    impl = Text
    cache_ok = True
    
    def process_bind_param(self, value, dialect):
        if value is not None:
            return json.dumps(value)
        return None
    
    def process_result_value(self, value, dialect):
        if value is not None:
            return json.loads(value)
        return None


class AuditLog(Base):
    """
    Audit log for tracking all data modifications.
    
    Use cases:
    - Security compliance (who changed what, when)
    - Debugging production issues
    - LLM context (understanding user behavior patterns)
    - Anomaly detection training data
    """
    __tablename__ = "audit_logs"
    
    id = Column(
        GUIDType(),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique audit log ID"
    )
    
    # Who performed the action
    actor_user_id = Column(
        GUIDType(),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User who performed the action (NULL for system actions)"
    )
    
    # What action was performed
    action = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Action type: create, update, delete, login, etc."
    )
    
    # Additional context (JSON)
    meta = Column(
        JSONType(),
        default=dict,
        nullable=False,
        comment="Additional metadata: {entity: 'transaction', entity_id: 'uuid', changes: {...}}"
    )
    
    # When
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="When the action occurred"
    )
    
    __table_args__ = (
        Index("idx_audit_user_action", actor_user_id, action),
        Index("idx_audit_created", created_at),
    )
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action})>"
    
    @classmethod
    def log(cls, db, action: str, user_id=None, **meta):
        """
        Convenience method to create audit log entry.
        
        Usage:
            AuditLog.log(db, "transaction.create", user_id=user.id, entity_id=str(txn.id))
        """
        entry = cls(
            actor_user_id=user_id,
            action=action,
            meta=meta
        )
        db.add(entry)
        return entry
