"""
Audit log model for comprehensive system activity tracking.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, Index
from sqlalchemy.sql import func

from app.database import Base


class AuditLog(Base):
    """Immutable audit log for all system operations and user actions."""

    __tablename__ = "audit_logs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Log identification
    log_id = Column(String(100), nullable=False, unique=True, index=True)

    # Event classification
    event_type = Column(String(100), nullable=False, index=True)  # user_action, system_event, security_event, etc.
    event_category = Column(String(100), nullable=True, index=True)
    event_name = Column(String(255), nullable=False, index=True)
    event_description = Column(Text, nullable=True)

    # Actor information
    actor_type = Column(String(50), nullable=False)  # user, system, service, api
    actor_id = Column(String(255), nullable=True, index=True)
    actor_name = Column(String(255), nullable=True)
    actor_ip = Column(String(50), nullable=True)
    actor_user_agent = Column(Text, nullable=True)

    # Target information
    target_type = Column(String(100), nullable=True)  # camera, frame, track, signature, etc.
    target_id = Column(String(255), nullable=True, index=True)
    target_name = Column(String(255), nullable=True)

    # Event details
    action = Column(String(100), nullable=False, index=True)  # create, read, update, delete, execute, etc.
    status = Column(String(50), nullable=False, index=True)  # success, failure, warning
    result = Column(String(255), nullable=True)

    # Context and data
    event_data = Column(JSON, nullable=True)  # Detailed event information
    previous_state = Column(JSON, nullable=True)  # For update operations
    new_state = Column(JSON, nullable=True)  # For update operations
    metadata = Column(JSON, nullable=True)  # Additional context

    # Security tracking
    session_id = Column(String(100), nullable=True, index=True)
    request_id = Column(String(100), nullable=True)
    is_security_relevant = Column(Boolean, default=False, index=True)
    severity = Column(String(50), nullable=True)  # critical, high, medium, low, info

    # Error information (if applicable)
    error_message = Column(Text, nullable=True)
    error_code = Column(String(100), nullable=True)
    stack_trace = Column(Text, nullable=True)

    # Timestamps (immutable)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Indexes for common queries
    __table_args__ = (
        Index("idx_audit_temporal_type", "timestamp", "event_type"),
        Index("idx_audit_actor_action", "actor_id", "action", "timestamp"),
        Index("idx_audit_security", "is_security_relevant", "severity", "timestamp"),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, event='{self.event_name}', actor='{self.actor_id}', timestamp={self.timestamp})>"
