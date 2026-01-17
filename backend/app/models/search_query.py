"""
Search query model for tracking natural language searches and analytics.
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, Index
from sqlalchemy.sql import func

from app.database import Base


class SearchQuery(Base):
    """Natural language search queries and results."""

    __tablename__ = "search_queries"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Query identification
    query_id = Column(String(100), nullable=False, unique=True, index=True)

    # Query content
    query_text = Column(Text, nullable=False)
    query_language = Column(String(10), default="en")

    # User information (for future authentication)
    operator_id = Column(String(255), nullable=True, index=True)
    operator_name = Column(String(255), nullable=True)
    session_id = Column(String(100), nullable=True)

    # Query analysis
    query_intent = Column(String(100), nullable=True)  # person_search, activity_search, object_search, etc.
    extracted_entities = Column(JSON, nullable=True)  # Persons, locations, objects, times, actions
    implicit_requirements = Column(JSON, nullable=True)
    semantic_expansion = Column(JSON, nullable=True)  # Synonyms and related terms
    query_analysis_json = Column(JSON, nullable=True)  # Full query understanding result

    # Search parameters
    time_range_start = Column(DateTime(timezone=True), nullable=True)
    time_range_end = Column(DateTime(timezone=True), nullable=True)
    camera_filters = Column(JSON, nullable=True)  # Array of camera IDs or locations
    confidence_threshold = Column(Float, nullable=True)
    result_limit = Column(Integer, default=20)

    # Results summary
    result_count = Column(Integer, default=0)
    candidate_count = Column(Integer, nullable=True)  # Before ranking
    top_confidence = Column(Float, nullable=True)
    average_confidence = Column(Float, nullable=True)
    result_frame_ids = Column(JSON, nullable=True)  # Array of returned frame IDs

    # Performance metrics
    query_processing_time_ms = Column(Integer, nullable=True)
    embedding_generation_time_ms = Column(Integer, nullable=True)
    vector_search_time_ms = Column(Integer, nullable=True)
    ranking_time_ms = Column(Integer, nullable=True)
    total_execution_time_ms = Column(Integer, nullable=True)

    # Execution details
    cameras_searched = Column(Integer, nullable=True)
    frames_evaluated = Column(Integer, nullable=True)
    time_range_coverage_hours = Column(Float, nullable=True)

    # User feedback (for future improvement)
    user_rating = Column(Integer, nullable=True)  # 1-5 stars
    feedback_notes = Column(Text, nullable=True)
    clicked_results = Column(JSON, nullable=True)  # Array of clicked frame IDs
    refined_query = Column(Text, nullable=True)  # If user refined the query

    # Timestamps
    executed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Indexes for analytics
    __table_args__ = (
        Index("idx_query_temporal_intent", "executed_at", "query_intent"),
        Index("idx_query_operator_time", "operator_id", "executed_at"),
    )

    def __repr__(self):
        return f"<SearchQuery(id={self.id}, query_text='{self.query_text[:50]}...', results={self.result_count})>"
