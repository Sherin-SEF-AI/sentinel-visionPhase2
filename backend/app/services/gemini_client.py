"""
Gemini AI client for vision analysis, threat detection, and natural language processing.
Implements all prompts and reasoning capabilities for the security intelligence platform.
"""

import logging
import time
import base64
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
import json

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.config import settings

logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)


class GeminiClient:
    """
    Client for Gemini AI models handling all vision and language tasks.
    """

    def __init__(self):
        """Initialize Gemini client with model configurations."""
        # Configure models
        self.pro_model = genai.GenerativeModel(
            model_name=settings.GEMINI_3_PRO_MODEL,
            generation_config={
                "temperature": 0.4,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )

        self.flash_model = genai.GenerativeModel(
            model_name=settings.GEMINI_FLASH_MODEL,
            generation_config={
                "temperature": 0.4,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
            },
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )

    # ==================== FRAME ANALYSIS ====================

    def analyze_frame(self, image_path: str, camera_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze a video frame using Gemini Flash for comprehensive scene understanding.

        Args:
            image_path: Path to the frame image
            camera_info: Optional camera context information

        Returns:
            Comprehensive analysis result as structured JSON
        """
        try:
            start_time = time.time()

            # Load image
            with open(image_path, "rb") as f:
                image_data = f.read()

            # Prepare prompt
            prompt = self._get_frame_analysis_prompt(camera_info)

            # Call Gemini API
            image_part = {
                "mime_type": "image/jpeg",
                "data": base64.b64encode(image_data).decode()
            }

            response = self.flash_model.generate_content(
                [prompt, image_part],
                request_options={"timeout": 30}
            )

            processing_time = int((time.time() - start_time) * 1000)

            # Parse response
            result = self._parse_json_response(response.text)
            result["processing_time_ms"] = processing_time
            result["model_version"] = settings.GEMINI_FLASH_MODEL

            logger.info(f"Frame analysis completed in {processing_time}ms")
            return result

        except Exception as e:
            logger.error(f"Frame analysis error: {e}")
            raise

    def _get_frame_analysis_prompt(self, camera_info: Optional[Dict[str, Any]] = None) -> str:
        """Generate comprehensive frame analysis prompt."""
        context = ""
        if camera_info:
            context = f"""
Camera Context:
- Location: {camera_info.get('location', 'Unknown')}
- Zone: {camera_info.get('facility_zone', 'Unknown')}
- Access Level: {camera_info.get('access_level', 'Public')}
"""

        return f"""You are an expert security analyst performing comprehensive video surveillance frame analysis. Analyze this frame and provide detailed structured information.

{context}

Provide your analysis in the following JSON structure:

{{
  "scene_description": "Detailed description of the overall scene",
  "location_context": {{
    "location_type": "entrance|exit|hallway|parking_lot|office|storage|loading_dock|perimeter|stairwell|elevator|lobby|outdoor|indoor",
    "access_level": "public|restricted|secure|high_security",
    "environmental_conditions": {{
      "lighting": "bright|normal|dim|dark",
      "weather": "clear|rainy|foggy|snowy|night" (if outdoor),
      "visibility": "excellent|good|fair|poor"
    }}
  }},
  "activity_classification": {{
    "primary_activity": "normal_transit|loitering|loading|meeting|maintenance|delivery|security_patrol|unauthorized_access|suspicious_behavior|emergency",
    "activity_description": "Detailed description of what is happening",
    "activity_level": "high|medium|low",
    "confidence": 0.0-1.0
  }},
  "persons_detected": [
    {{
      "person_id": 1,
      "appearance": {{
        "clothing_upper": "Detailed description of upper body clothing with colors and style",
        "clothing_lower": "Detailed description of lower body clothing",
        "dominant_colors": ["color1", "color2"],
        "physical_characteristics": "Height estimate, build, posture, gait",
        "distinctive_features": ["Feature1", "Feature2"],
        "accessories": ["item1", "item2"],
        "carried_objects": ["object1", "object2"]
      }},
      "position": {{
        "location": "Description of position in frame",
        "action": "walking|standing|running|sitting|bending|reaching|climbing|carrying",
        "direction": "towards_camera|away_from_camera|left_to_right|right_to_left|stationary"
      }},
      "behavior_analysis": {{
        "posture": "normal|suspicious|hurried|cautious|aggressive",
        "attention": "focused|distracted|looking_around|avoiding_camera",
        "interaction": "alone|with_others|following|leading"
      }}
    }}
  ],
  "objects_detected": [
    {{
      "object_type": "Type of object",
      "description": "Detailed description",
      "location": "Position in scene",
      "relevance": "security_relevant|normal|suspicious",
      "confidence": 0.0-1.0
    }}
  ],
  "vehicles_detected": [
    {{
      "vehicle_type": "car|truck|van|motorcycle|bicycle",
      "description": "Color, make/model if identifiable",
      "license_plate_visible": true|false,
      "location": "Position and orientation",
      "status": "parked|moving|loading|unloading"
    }}
  ],
  "threat_assessment": {{
    "threat_level": "none|low|medium|high|critical",
    "threat_indicators": ["Indicator1", "Indicator2"],
    "suspicious_elements": ["Element1", "Element2"],
    "confidence": 0.0-1.0,
    "reasoning": "Explanation of threat assessment"
  }},
  "searchable_phrases": [
    "Natural language phrase 1 describing searchable aspects",
    "Natural language phrase 2",
    "Natural language phrase 3"
  ],
  "metadata": {{
    "person_count": 0,
    "vehicle_count": 0,
    "object_count": 0,
    "scene_complexity": "simple|moderate|complex",
    "analysis_confidence": 0.0-1.0
  }}
}}

IMPORTANT: Return ONLY valid JSON. No explanatory text before or after."""

    def generate_embedding_text(self, analysis: Dict[str, Any]) -> str:
        """
        Generate optimized text for embedding generation from frame analysis.

        Args:
            analysis: Frame analysis result

        Returns:
            Optimized natural language text for embedding
        """
        parts = []

        # Scene description
        if "scene_description" in analysis:
            parts.append(analysis["scene_description"])

        # Activity
        if "activity_classification" in analysis:
            activity = analysis["activity_classification"]
            parts.append(f"Activity: {activity.get('activity_description', '')}")

        # Persons
        if "persons_detected" in analysis and analysis["persons_detected"]:
            for person in analysis["persons_detected"]:
                appearance = person.get("appearance", {})
                person_desc = f"Person wearing {appearance.get('clothing_upper', '')} and {appearance.get('clothing_lower', '')}"
                if appearance.get("carried_objects"):
                    person_desc += f", carrying {', '.join(appearance['carried_objects'])}"
                if person.get("position", {}).get("action"):
                    person_desc += f", {person['position']['action']}"
                parts.append(person_desc)

        # Objects
        if "objects_detected" in analysis and analysis["objects_detected"]:
            objects = [obj.get("description", obj.get("object_type", "")) for obj in analysis["objects_detected"]]
            if objects:
                parts.append(f"Objects: {', '.join(objects)}")

        # Vehicles
        if "vehicles_detected" in analysis and analysis["vehicles_detected"]:
            vehicles = [v.get("description", v.get("vehicle_type", "")) for v in analysis["vehicles_detected"]]
            if vehicles:
                parts.append(f"Vehicles: {', '.join(vehicles)}")

        # Location context
        if "location_context" in analysis:
            loc = analysis["location_context"]
            parts.append(f"Location type: {loc.get('location_type', '')}")

        # Searchable phrases
        if "searchable_phrases" in analysis:
            parts.extend(analysis["searchable_phrases"])

        return " ".join(parts)

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector using Gemini embedding model.

        Args:
            text: Text to embed

        Returns:
            768-dimensional embedding vector
        """
        try:
            result = genai.embed_content(
                model=f"models/{settings.GEMINI_EMBEDDING_MODEL}",
                content=text,
                task_type="RETRIEVAL_DOCUMENT"
            )
            return result["embedding"]

        except Exception as e:
            logger.error(f"Embedding generation error: {e}")
            raise

    def generate_query_embedding(self, query: str) -> List[float]:
        """
        Generate embedding vector for search query.

        Args:
            query: Search query text

        Returns:
            768-dimensional embedding vector
        """
        try:
            result = genai.embed_content(
                model=f"models/{settings.GEMINI_EMBEDDING_MODEL}",
                content=query,
                task_type="RETRIEVAL_QUERY"
            )
            return result["embedding"]

        except Exception as e:
            logger.error(f"Query embedding generation error: {e}")
            raise

    # ==================== PERSON TRACKING ====================

    def match_person_tracks(
        self,
        current_persons: List[Dict[str, Any]],
        active_tracks: List[Dict[str, Any]],
        camera_info: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Match detected persons to existing tracks using appearance and spatiotemporal analysis.

        Args:
            current_persons: Person detections from current frame
            active_tracks: Currently active person tracks
            camera_info: Current camera information

        Returns:
            List of match results with track assignments
        """
        try:
            prompt = self._get_person_tracking_prompt(current_persons, active_tracks, camera_info)

            response = self.pro_model.generate_content(
                prompt,
                request_options={"timeout": 30}
            )

            result = self._parse_json_response(response.text)
            return result.get("matches", [])

        except Exception as e:
            logger.error(f"Person tracking error: {e}")
            raise

    def _get_person_tracking_prompt(
        self,
        current_persons: List[Dict[str, Any]],
        active_tracks: List[Dict[str, Any]],
        camera_info: Dict[str, Any]
    ) -> str:
        """Generate person tracking matching prompt."""
        return f"""You are an expert in cross-frame person tracking for video surveillance. Your task is to match newly detected persons to existing tracks based on appearance consistency and spatiotemporal feasibility.

Current Camera: {camera_info.get('name', 'Unknown')}
Location: {camera_info.get('location', 'Unknown')}
Zone: {camera_info.get('facility_zone', 'Unknown')}

Current Frame Detections:
{json.dumps(current_persons, indent=2)}

Active Tracks (last 5 minutes):
{json.dumps(active_tracks, indent=2)}

For each current detection, determine if it matches an existing track. Consider:

1. APPEARANCE MATCHING (weight: 0.40):
   - Clothing consistency (upper and lower garments)
   - Color matching
   - Physical characteristics
   - Distinctive features
   - Carried objects

2. SPATIOTEMPORAL FEASIBILITY (weight: 0.30):
   - Time since last seen (recent = more likely)
   - Camera transition logic (are cameras adjacent/connected?)
   - Movement speed feasibility
   - Direction consistency

3. CONTEXTUAL CONSISTENCY (weight: 0.20):
   - Behavior pattern consistency
   - Zone transition logic
   - Activity alignment

4. DISTINCTIVENESS (weight: 0.10):
   - Unique features that increase confidence
   - Common vs distinctive appearance

Provide matches in this JSON structure:

{{
  "matches": [
    {{
      "person_id": 1,
      "matched": true|false,
      "track_id": "track_id or null if new",
      "confidence": 0.0-1.0,
      "match_factors": {{
        "appearance_score": 0.0-1.0,
        "spatiotemporal_score": 0.0-1.0,
        "contextual_score": 0.0-1.0,
        "distinctiveness_score": 0.0-1.0
      }},
      "reasoning": "Explanation of match decision",
      "ambiguous": true|false,
      "alternative_matches": ["track_id1", "track_id2"] (if ambiguous)
    }}
  ]
}}

MATCHING RULES:
- Confidence >= 0.60: Accept match
- 0.40 <= Confidence < 0.60: Flag as ambiguous
- Confidence < 0.40: Create new track
- Clothing changes are rare but possible after extended time
- Physical characteristics should remain consistent

Return ONLY valid JSON."""

    # ==================== THREAT DETECTION ====================

    def evaluate_threat_signatures(
        self,
        frame_analysis: Dict[str, Any],
        signatures: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Evaluate frame against threat signature library.

        Args:
            frame_analysis: Complete frame analysis result
            signatures: List of threat signatures to evaluate
            context: Additional contextual information

        Returns:
            List of matched signatures with confidence scores
        """
        try:
            prompt = self._get_threat_evaluation_prompt(frame_analysis, signatures, context)

            response = self.pro_model.generate_content(
                prompt,
                request_options={"timeout": 30}
            )

            result = self._parse_json_response(response.text)
            return result.get("matches", [])

        except Exception as e:
            logger.error(f"Threat evaluation error: {e}")
            raise

    def _get_threat_evaluation_prompt(
        self,
        frame_analysis: Dict[str, Any],
        signatures: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate threat signature evaluation prompt."""
        context_str = json.dumps(context, indent=2) if context else "None"

        return f"""You are an expert security analyst evaluating surveillance footage for threat signatures. Analyze this frame against the threat signature library and identify matches.

Frame Analysis:
{json.dumps(frame_analysis, indent=2)}

Additional Context:
{context_str}

Threat Signatures to Evaluate:
{json.dumps(signatures[:20], indent=2)}  # Limit to top 20 for context size

For each signature, evaluate if the frame matches the trigger conditions. Consider:

1. SEMANTIC RELEVANCE (weight: 0.35):
   - Does the frame content semantically match the signature description?
   - Are the key threat indicators present?

2. ENTITY MATCH QUALITY (weight: 0.30):
   - Are the specific entities mentioned in the signature present?
   - Quality and clarity of entity detection

3. TEMPORAL CONTEXT (weight: 0.20):
   - Time of day relevance
   - Duration of behavior
   - Sequence of events

4. VISUAL EVIDENCE QUALITY (weight: 0.15):
   - Frame quality and visibility
   - Confidence in visual analysis
   - Ambiguity level

Provide results in this JSON structure:

{{
  "matches": [
    {{
      "signature_id": "signature_id",
      "signature_name": "Signature name",
      "matched": true,
      "confidence": 0.0-1.0,
      "confidence_factors": {{
        "semantic_relevance": 0.0-1.0,
        "entity_match": 0.0-1.0,
        "temporal_context": 0.0-1.0,
        "visual_evidence": 0.0-1.0
      }},
      "evidence_summary": "What in the frame triggered this signature",
      "severity": "critical|high|medium|low",
      "recommended_actions": ["Action1", "Action2"],
      "contextual_reclassification": {{
        "apply": true|false,
        "new_severity": "severity level",
        "reasoning": "Why severity should change based on context"
      }}
    }}
  ],
  "no_threats_detected": true|false
}}

EVALUATION RULES:
- Only return signatures with confidence >= 0.50
- Consider contextual reclassification rules
- Differentiate between similar signatures
- Provide clear evidence for each match

Return ONLY valid JSON."""

    def create_custom_signature(self, description: str, severity: str, category: str) -> Dict[str, Any]:
        """
        Create a custom threat signature from natural language description.

        Args:
            description: Natural language description of the threat
            severity: Severity level
            category: Threat category

        Returns:
            Structured signature definition
        """
        try:
            prompt = f"""You are an expert in creating threat detection signatures for security systems. Convert this natural language threat description into a formal signature specification.

Description: {description}
Severity: {severity}
Category: {category}

Create a comprehensive signature specification with:

1. TRIGGER CONDITIONS: What specific elements must be present to trigger this signature
2. DIFFERENTIATION RULES: How to differentiate this from similar threats
3. CONTEXTUAL RULES: How context affects the threat level
4. CONFIDENCE THRESHOLDS: Minimum confidence required
5. RECOMMENDED ACTIONS: What operators should do when detected

Provide the signature in this JSON structure:

{{
  "signature_definition": {{
    "name": "Short descriptive name",
    "description": "Detailed description",
    "trigger_conditions": {{
      "required_entities": ["entity1", "entity2"],
      "required_activities": ["activity1", "activity2"],
      "required_context": {{
        "location_types": ["type1", "type2"],
        "time_constraints": "Description of time constraints if any"
      }},
      "visual_indicators": ["indicator1", "indicator2"]
    }},
    "differentiation_rules": {{
      "similar_signatures": ["signature1", "signature2"],
      "key_differentiators": ["What makes this unique"]
    }},
    "contextual_rules": [
      {{
        "condition": "Context condition",
        "action": "increase|decrease severity",
        "new_severity": "severity level",
        "reasoning": "Why this context matters"
      }}
    ],
    "confidence_threshold": 0.60,
    "temporal_window_seconds": 300,
    "recommended_actions": ["Action1", "Action2", "Action3"]
  }}
}}

Return ONLY valid JSON."""

            response = self.pro_model.generate_content(
                prompt,
                request_options={"timeout": 30}
            )

            result = self._parse_json_response(response.text)
            return result.get("signature_definition", {})

        except Exception as e:
            logger.error(f"Custom signature creation error: {e}")
            raise

    # ==================== NATURAL LANGUAGE SEARCH ====================

    def understand_search_query(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Understand and decompose natural language search query.

        Args:
            query: User's natural language query
            context: Optional context (facility layout, camera locations, etc.)

        Returns:
            Structured query analysis
        """
        try:
            prompt = self._get_query_understanding_prompt(query, context)

            response = self.pro_model.generate_content(
                prompt,
                request_options={"timeout": 30}
            )

            result = self._parse_json_response(response.text)
            return result

        except Exception as e:
            logger.error(f"Query understanding error: {e}")
            raise

    def _get_query_understanding_prompt(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """Generate query understanding prompt."""
        context_str = json.dumps(context, indent=2) if context else "None"

        return f"""You are an expert in understanding natural language queries for video surveillance search. Analyze this query and extract structured search parameters.

Query: "{query}"

Facility Context:
{context_str}

Decompose the query into structured components:

{{
  "intent_classification": {{
    "primary_intent": "person_search|object_search|activity_search|location_search|time_based_search|incident_search",
    "sub_intents": ["sub_intent1", "sub_intent2"]
  }},
  "entity_extraction": {{
    "persons": [
      {{
        "appearance": "Description of person appearance",
        "clothing": "Clothing description",
        "accessories": ["item1", "item2"],
        "carried_objects": ["object1", "object2"],
        "physical_traits": "Physical characteristics"
      }}
    ],
    "objects": ["object1", "object2"],
    "vehicles": [
      {{
        "type": "car|truck|van|etc",
        "description": "Color, make, model if mentioned"
      }}
    ],
    "locations": [
      {{
        "area": "Location description",
        "zone": "Facility zone if identifiable",
        "entrance_exit": "specific entrance/exit if mentioned"
      }}
    ],
    "temporal_references": {{
      "absolute_time": "YYYY-MM-DD HH:MM:SS or null",
      "relative_time": "Description of relative time if used",
      "time_of_day": "morning|afternoon|evening|night|null",
      "date_references": "today|yesterday|last_week|etc"
    }},
    "actions": ["action1", "action2"],
    "activities": ["activity1", "activity2"]
  }},
  "implicit_requirements": [
    "Requirement 1 implied by the query",
    "Requirement 2"
  ],
  "semantic_expansion": {{
    "synonyms": {{
      "term1": ["synonym1", "synonym2"],
      "term2": ["synonym1", "synonym2"]
    }},
    "related_concepts": ["concept1", "concept2"]
  }},
  "filters": {{
    "time_range": {{
      "start": "ISO timestamp or null",
      "end": "ISO timestamp or null"
    }},
    "locations": ["location1", "location2"],
    "confidence_threshold": 0.40
  }},
  "search_strategy": {{
    "approach": "exact_match|semantic_search|temporal_pattern|spatial_pattern",
    "ranking_priorities": ["priority1", "priority2"],
    "expected_result_count": "estimate: single|few|many"
  }},
  "optimized_query_text": "Reformulated query optimized for embedding search"
}}

IMPORTANT RULES:
- Extract all entities mentioned or implied
- Infer implicit requirements (e.g., "left" implies person was present before)
- Generate semantic expansions for better recall
- Provide optimized query text that captures all search intent
- Handle temporal references correctly (convert relative to absolute when possible)

Return ONLY valid JSON."""

    def rank_search_results(
        self,
        query: str,
        query_analysis: Dict[str, Any],
        candidates: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Rank search result candidates using multi-factor analysis.

        Args:
            query: Original search query
            query_analysis: Query understanding result
            candidates: List of candidate results from vector search

        Returns:
            Ranked results with confidence scores and explanations
        """
        try:
            prompt = self._get_ranking_prompt(query, query_analysis, candidates)

            response = self.pro_model.generate_content(
                prompt,
                request_options={"timeout": 30}
            )

            result = self._parse_json_response(response.text)
            return result.get("ranked_results", [])

        except Exception as e:
            logger.error(f"Result ranking error: {e}")
            raise

    def _get_ranking_prompt(
        self,
        query: str,
        query_analysis: Dict[str, Any],
        candidates: List[Dict[str, Any]]
    ) -> str:
        """Generate result ranking prompt."""
        return f"""You are an expert in ranking search results for video surveillance queries. Evaluate and rank these candidate results based on relevance to the query.

Original Query: "{query}"

Query Analysis:
{json.dumps(query_analysis, indent=2)}

Candidate Results:
{json.dumps(candidates[:10], indent=2)}  # Limit to top 10 for context

Rank each result using these factors:

1. SEMANTIC RELEVANCE (weight: 0.35):
   - How well does the result match the query semantics?
   - Are the key entities present?

2. ENTITY MATCH QUALITY (weight: 0.30):
   - Precision of entity matches (appearance, objects, etc.)
   - Completeness of matches

3. TEMPORAL RELEVANCE (weight: 0.15):
   - Time proximity to requested timeframe
   - Temporal context alignment

4. CONTEXTUAL COHERENCE (weight: 0.15):
   - Location appropriateness
   - Activity context alignment

5. VISUAL EVIDENCE QUALITY (weight: 0.05):
   - Frame quality and clarity
   - Analysis confidence

Provide ranked results in this JSON structure:

{{
  "ranked_results": [
    {{
      "frame_id": "frame_id",
      "rank": 1,
      "confidence": {{
        "total": 0.0-1.0,
        "semantic_relevance": 0.0-1.0,
        "entity_match": 0.0-1.0,
        "temporal_relevance": 0.0-1.0,
        "contextual_coherence": 0.0-1.0,
        "visual_quality": 0.0-1.0
      }},
      "match_explanation": "Clear explanation of why this result matches",
      "matched_entities": ["entity1", "entity2"],
      "relevance_highlights": ["highlight1", "highlight2"]
    }}
  ]
}}

RANKING RULES:
- Only include results with total confidence >= 0.40
- Order by total confidence score (highest first)
- Provide clear explanations for each match
- Consider query-specific weight adjustments

Return ONLY valid JSON."""

    # ==================== UTILITY METHODS ====================

    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse JSON response from Gemini, handling common formatting issues.

        Args:
            response_text: Raw response text from Gemini

        Returns:
            Parsed JSON dictionary
        """
        try:
            # Remove markdown code blocks if present
            text = response_text.strip()
            if text.startswith("```json"):
                text = text[7:]
            if text.startswith("```"):
                text = text[3:]
            if text.endswith("```"):
                text = text[:-3]
            text = text.strip()

            # Parse JSON
            return json.loads(text)

        except json.JSONDecodeError as e:
            logger.error(f"JSON parsing error: {e}\nResponse: {response_text}")
            raise ValueError(f"Failed to parse Gemini response as JSON: {e}")


# Global client instance
_gemini_client: Optional[GeminiClient] = None


def get_gemini_client() -> GeminiClient:
    """Get or create global Gemini client instance."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client
