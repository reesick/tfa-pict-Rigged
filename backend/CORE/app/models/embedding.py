"""
Embedding Model - Vector storage for ML semantic search.
For Person 2 ML similarity and semantic search on transactions.
"""
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Index, TypeDecorator
import uuid
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


class Embedding(Base):
    """
    Stores vector embeddings for transactions.
    
    Person 2's ML system generates embeddings for:
    - Semantic search on transaction descriptions
    - Similar transaction grouping
    - Anomaly detection via vector distance
    
    Vector format: JSON array of 384 floats (sentence-transformers)
    """
    __tablename__ = "embeddings"
    
    id = Column(
        GUIDType(),
        primary_key=True,
        default=uuid.uuid4,
        comment="Unique embedding identifier"
    )
    
    transaction_id = Column(
        GUIDType(),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,  # One embedding per transaction
        index=True,
        comment="Transaction this embedding belongs to"
    )
    
    # Vector data
    vector = Column(
        Text,
        nullable=False,
        comment="JSON array of 384 floats (embedding vector)"
    )
    
    # Metadata
    model_version = Column(
        String(50),
        default="sentence-transformers/all-MiniLM-L6-v2",
        comment="ML model used to generate embedding"
    )
    
    # Timestamps
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False
    )
    
    __table_args__ = (
        Index("idx_embedding_transaction", transaction_id),
    )
    
    def __repr__(self):
        return f"<Embedding(id={self.id}, txn={self.transaction_id})>"
    
    def get_vector_list(self) -> list:
        """Parse vector from JSON string."""
        import json
        if self.vector:
            return json.loads(self.vector)
        return []
    
    def set_vector_list(self, vec: list):
        """Store vector as JSON string."""
        import json
        self.vector = json.dumps(vec)
