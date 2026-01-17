"""
Natural language search service for conversational video archive querying.
Implements query understanding, vector search, and result ranking.
"""

import logging
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client.models import Filter, FieldCondition, MatchValue, Range

from app.models.search_query import SearchQuery
from app.models.frame import Frame
from app.models.frame_analysis import FrameAnalysis
from app.models.camera import Camera
from app.database import get_qdrant_client
from app.services.gemini_client import get_gemini_client
from app.config import settings

logger = logging.getLogger(__name__)


class SearchService:
    """Service for natural language video search."""

    def __init__(self):
        """Initialize search service."""
        self.gemini_client = get_gemini_client()
        self.qdrant_client = get_qdrant_client()

    async def search(
        self,
        db: AsyncSession,
        query: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        camera_ids: Optional[List[int]] = None,
        facility_zones: Optional[List[str]] = None,
        confidence_threshold: float = 0.40,
        result_limit: int = 20,
        operator_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute natural language search query.

        Args:
            db: Database session
            query: Natural language search query
            start_time: Optional start of time range
            end_time: Optional end of time range
            camera_ids: Optional camera ID filter
            facility_zones: Optional facility zone filter
            confidence_threshold: Minimum confidence for results
            result_limit: Maximum number of results
            operator_id: Optional operator identifier

        Returns:
            Search results with metadata
        """
        try:
            start_exec_time = time.time()
            logger.info(f"Executing search: {query[:100]}")

            # Step 1: Understand query using Gemini
            query_analysis_start = time.time()
            query_analysis = self.gemini_client.understand_search_query(
                query=query,
                context=await self._get_facility_context(db)
            )
            query_analysis_time = int((time.time() - query_analysis_start) * 1000)

            # Extract filters from query analysis
            filters = query_analysis.get("filters", {})
            if not start_time and filters.get("time_range", {}).get("start"):
                start_time = datetime.fromisoformat(filters["time_range"]["start"])
            if not end_time and filters.get("time_range", {}).get("end"):
                end_time = datetime.fromisoformat(filters["time_range"]["end"])

            # Step 2: Generate query embedding
            embedding_start = time.time()
            optimized_query_text = query_analysis.get("optimized_query_text", query)
            query_embedding = self.gemini_client.generate_query_embedding(optimized_query_text)
            embedding_time = int((time.time() - embedding_start) * 1000)

            # Step 3: Vector similarity search in Qdrant
            vector_search_start = time.time()
            candidates = await self._vector_search(
                query_embedding=query_embedding,
                start_time=start_time,
                end_time=end_time,
                camera_ids=camera_ids,
                facility_zones=facility_zones,
                limit=result_limit * settings.SEARCH_CANDIDATE_MULTIPLIER
            )
            vector_search_time = int((time.time() - vector_search_start) * 1000)

            # Step 4: Rank results using Gemini
            ranking_start = time.time()
            if candidates:
                ranked_results = self.gemini_client.rank_search_results(
                    query=query,
                    query_analysis=query_analysis,
                    candidates=candidates
                )
            else:
                ranked_results = []
            ranking_time = int((time.time() - ranking_start) * 1000)

            # Step 5: Filter by confidence and limit
            filtered_results = [
                r for r in ranked_results
                if r.get("confidence", {}).get("total", 0) >= confidence_threshold
            ][:result_limit]

            # Step 6: Enrich results with frame data
            enriched_results = await self._enrich_results(db, filtered_results)

            # Calculate execution metadata
            total_time = int((time.time() - start_exec_time) * 1000)
            cameras_searched = len(set(c.get("camera_id") for c in candidates)) if candidates else 0

            # Calculate time range coverage
            time_coverage_hours = None
            if start_time and end_time:
                time_coverage_hours = (end_time - start_time).total_seconds() / 3600

            # Store search query for analytics
            await self._store_search_query(
                db=db,
                query=query,
                query_analysis=query_analysis,
                results=enriched_results,
                execution_times={
                    "query_analysis": query_analysis_time,
                    "embedding": embedding_time,
                    "vector_search": vector_search_time,
                    "ranking": ranking_time,
                    "total": total_time,
                },
                cameras_searched=cameras_searched,
                frames_evaluated=len(candidates),
                time_coverage_hours=time_coverage_hours,
                operator_id=operator_id,
                start_time=start_time,
                end_time=end_time,
                confidence_threshold=confidence_threshold,
                result_limit=result_limit
            )

            # Generate response
            response = {
                "query_id": str(uuid.uuid4()),
                "query": query,
                "query_analysis": query_analysis,
                "results": enriched_results,
                "result_count": len(enriched_results),
                "cameras_searched": cameras_searched,
                "frames_evaluated": len(candidates),
                "time_range_coverage_hours": time_coverage_hours,
                "execution_time_ms": total_time,
                "suggestions": self._generate_suggestions(query_analysis, enriched_results),
                "direct_answer": self._generate_direct_answer(query, query_analysis, enriched_results),
            }

            logger.info(f"Search completed: {len(enriched_results)} results in {total_time}ms")
            return response

        except Exception as e:
            logger.error(f"Search error: {e}")
            raise

    async def _get_facility_context(self, db: AsyncSession) -> Dict[str, Any]:
        """Get facility context for query understanding."""
        try:
            # Get camera locations
            result = await db.execute(
                select(Camera).where(Camera.is_active == True)
            )
            cameras = result.scalars().all()

            zones = list(set(c.facility_zone for c in cameras if c.facility_zone))
            locations = list(set(c.location for c in cameras if c.location))

            return {
                "facility_zones": zones,
                "camera_locations": locations,
                "camera_count": len(cameras),
            }

        except Exception as e:
            logger.error(f"Error getting facility context: {e}")
            return {}

    async def _vector_search(
        self,
        query_embedding: List[float],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        camera_ids: Optional[List[int]],
        facility_zones: Optional[List[str]],
        limit: int
    ) -> List[Dict[str, Any]]:
        """Execute vector similarity search in Qdrant with filters."""
        try:
            # Build filter conditions
            filter_conditions = []

            if start_time:
                filter_conditions.append(
                    FieldCondition(
                        key="timestamp_unix",
                        range=Range(gte=int(start_time.timestamp()))
                    )
                )

            if end_time:
                filter_conditions.append(
                    FieldCondition(
                        key="timestamp_unix",
                        range=Range(lte=int(end_time.timestamp()))
                    )
                )

            if camera_ids:
                filter_conditions.append(
                    FieldCondition(
                        key="camera_id",
                        match=MatchValue(any=camera_ids)
                    )
                )

            if facility_zones:
                filter_conditions.append(
                    FieldCondition(
                        key="facility_zone",
                        match=MatchValue(any=facility_zones)
                    )
                )

            # Build filter
            search_filter = None
            if filter_conditions:
                search_filter = Filter(must=filter_conditions)

            # Execute search
            search_results = self.qdrant_client.search(
                collection_name=settings.QDRANT_COLLECTION,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=limit,
                with_payload=True
            )

            # Convert to dictionaries
            candidates = []
            for result in search_results:
                payload = result.payload
                payload["vector_score"] = result.score
                payload["frame_id"] = payload.get("frame_id")  # Database frame ID
                candidates.append(payload)

            logger.debug(f"Vector search returned {len(candidates)} candidates")
            return candidates

        except Exception as e:
            logger.error(f"Vector search error: {e}")
            return []

    async def _enrich_results(
        self,
        db: AsyncSession,
        ranked_results: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Enrich search results with full frame and camera data."""
        enriched = []

        for result in ranked_results:
            try:
                frame_id = result.get("frame_id")

                # Get frame and analysis
                frame_result = await db.execute(
                    select(Frame, FrameAnalysis, Camera)
                    .join(FrameAnalysis, Frame.id == FrameAnalysis.frame_id)
                    .join(Camera, Frame.camera_id == Camera.id)
                    .where(Frame.id == frame_id)
                )

                row = frame_result.one_or_none()
                if not row:
                    continue

                frame, analysis, camera = row

                enriched.append({
                    "frame_id": frame.id,
                    "frame": {
                        "frame_id": frame.frame_id,
                        "captured_at": frame.captured_at.isoformat(),
                        "frame_path": frame.frame_path,
                        "thumbnail_path": frame.thumbnail_path,
                        "motion_detected": frame.motion_detected,
                    },
                    "analysis": {
                        "scene_description": analysis.scene_description,
                        "activity_category": analysis.activity_category,
                        "activity_description": analysis.activity_description,
                        "person_count": analysis.person_count,
                        "person_profiles": analysis.person_profiles,
                        "objects_detected": analysis.objects_detected,
                        "threat_level": analysis.threat_level,
                    },
                    "camera": {
                        "id": camera.id,
                        "name": camera.name,
                        "location": camera.location,
                        "facility_zone": camera.facility_zone,
                    },
                    "confidence": result.get("confidence"),
                    "match_explanation": result.get("match_explanation"),
                    "matched_entities": result.get("matched_entities", []),
                    "relevance_highlights": result.get("relevance_highlights", []),
                })

            except Exception as e:
                logger.error(f"Error enriching result for frame {frame_id}: {e}")
                continue

        return enriched

    async def _store_search_query(
        self,
        db: AsyncSession,
        query: str,
        query_analysis: Dict[str, Any],
        results: List[Dict[str, Any]],
        execution_times: Dict[str, int],
        cameras_searched: int,
        frames_evaluated: int,
        time_coverage_hours: Optional[float],
        operator_id: Optional[str],
        start_time: Optional[datetime],
        end_time: Optional[datetime],
        confidence_threshold: float,
        result_limit: int
    ):
        """Store search query for analytics."""
        try:
            query_id = str(uuid.uuid4())

            search_query = SearchQuery(
                query_id=query_id,
                query_text=query,
                operator_id=operator_id,
                query_intent=query_analysis.get("intent_classification", {}).get("primary_intent"),
                extracted_entities=query_analysis.get("entity_extraction"),
                implicit_requirements=query_analysis.get("implicit_requirements"),
                semantic_expansion=query_analysis.get("semantic_expansion"),
                query_analysis_json=query_analysis,
                time_range_start=start_time,
                time_range_end=end_time,
                confidence_threshold=confidence_threshold,
                result_limit=result_limit,
                result_count=len(results),
                candidate_count=frames_evaluated,
                top_confidence=results[0].get("confidence", {}).get("total") if results else None,
                average_confidence=sum(r.get("confidence", {}).get("total", 0) for r in results) / len(results) if results else None,
                result_frame_ids=[r.get("frame_id") for r in results],
                query_processing_time_ms=execution_times.get("query_analysis"),
                embedding_generation_time_ms=execution_times.get("embedding"),
                vector_search_time_ms=execution_times.get("vector_search"),
                ranking_time_ms=execution_times.get("ranking"),
                total_execution_time_ms=execution_times.get("total"),
                cameras_searched=cameras_searched,
                frames_evaluated=frames_evaluated,
                time_range_coverage_hours=time_coverage_hours,
            )

            db.add(search_query)
            await db.commit()

        except Exception as e:
            logger.error(f"Error storing search query: {e}")
            # Don't raise - this is for analytics only

    def _generate_suggestions(
        self,
        query_analysis: Dict[str, Any],
        results: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate follow-up search suggestions."""
        suggestions = []

        # Based on result count
        if len(results) == 0:
            suggestions.append("Try broadening your search with less specific terms")
            suggestions.append("Adjust the time range to cover a wider period")
        elif len(results) > 15:
            suggestions.append("Try narrowing your search with more specific details")
            suggestions.append("Add time constraints to focus on a specific period")

        # Based on entities
        entities = query_analysis.get("entity_extraction", {})
        if entities.get("persons") and len(results) > 0:
            suggestions.append("Search for this person in other locations")
            suggestions.append("Find other activities involving this person")

        return suggestions[:3]

    def _generate_direct_answer(
        self,
        query: str,
        query_analysis: Dict[str, Any],
        results: List[Dict[str, Any]]
    ) -> Optional[str]:
        """Generate direct answer for certain query types."""
        if not results:
            return "No matching footage found for your query."

        intent = query_analysis.get("intent_classification", {}).get("primary_intent")

        if intent == "person_search" and len(results) > 0:
            result = results[0]
            camera = result.get("camera", {})
            frame = result.get("frame", {})
            return f"Person matching your description was seen at {camera.get('location')} on {frame.get('captured_at')}."

        elif intent == "activity_search" and len(results) > 0:
            count = len(results)
            return f"Found {count} instance{'s' if count > 1 else ''} of this activity."

        return None


# Global service instance
_search_service: Optional[SearchService] = None


def get_search_service() -> SearchService:
    """Get or create global search service instance."""
    global _search_service
    if _search_service is None:
        _search_service = SearchService()
    return _search_service
