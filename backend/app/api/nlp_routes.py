"""
FastAPI routes for NLP operations.

Provides endpoints for:
- Contradiction detection
- Argument mining
- Stance detection
- Fact-checking
- Entity extraction
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import logging
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.nlp import (
    ContradictionDetector,
    ArgumentMiner,
    StanceDetector,
    FactChecker,
    EntityExtractor
)
from research_agent.graph_database import GraphDatabase

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/nlp", tags=["NLP"])

# Global instances (should be dependency-injected in production)
graph_db = GraphDatabase()


# ============================================================================
# Request/Response Models
# ============================================================================

class ClaimPair(BaseModel):
    """Pair of claims for contradiction detection."""
    claim1: Dict[str, Any]
    claim2: Dict[str, Any]


class ClaimList(BaseModel):
    """List of claims."""
    claims: List[Dict[str, Any]]
    min_confidence: Optional[float] = Field(default=70.0, ge=0, le=100)


class DocumentText(BaseModel):
    """Document text for analysis."""
    text: str
    doc_id: Optional[str] = None


class ClaimDocument(BaseModel):
    """Claim and document for stance detection."""
    claim: Dict[str, Any]
    document: Dict[str, Any]
    context: Optional[str] = None


class ClaimDocuments(BaseModel):
    """Claim and multiple documents for stance analysis."""
    claim: Dict[str, Any]
    documents: List[Dict[str, Any]]


class SingleClaim(BaseModel):
    """Single claim for analysis."""
    claim: Dict[str, Any]


# ============================================================================
# Contradiction Detection Endpoints
# ============================================================================

@router.post("/detect-contradictions")
async def detect_contradictions(request: ClaimPair):
    """
    Detect if two claims contradict each other.

    Returns contradiction analysis with confidence score and explanation.
    """
    try:
        detector = ContradictionDetector()
        result = await detector.detect_contradiction(
            claim1=request.claim1,
            claim2=request.claim2
        )

        return {
            "success": True,
            "result": {
                "is_contradiction": result.is_contradiction,
                "contradiction_type": result.contradiction_type.value,
                "confidence": result.confidence,
                "explanation": result.explanation,
                "keywords": result.keywords
            }
        }

    except Exception as e:
        logger.error(f"Contradiction detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-contradictions-batch")
async def detect_contradictions_batch(
    request: ClaimList,
    background_tasks: BackgroundTasks
):
    """
    Detect contradictions among multiple claims.

    Performs pairwise comparison and returns all contradictions above
    the confidence threshold.
    """
    try:
        detector = ContradictionDetector()
        results = await detector.detect_contradictions_batch(
            claims=request.claims,
            min_confidence=request.min_confidence
        )

        # Create relationships in graph (background task)
        background_tasks.add_task(
            detector.create_contradiction_relationships,
            graph_db,
            results
        )

        return {
            "success": True,
            "count": len(results),
            "contradictions": [
                {
                    "claim1_id": r.claim1_id,
                    "claim2_id": r.claim2_id,
                    "contradiction_type": r.contradiction_type.value,
                    "confidence": r.confidence,
                    "explanation": r.explanation,
                    "keywords": r.keywords
                }
                for r in results
            ]
        }

    except Exception as e:
        logger.error(f"Batch contradiction detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Argument Mining Endpoints
# ============================================================================

@router.post("/mine-arguments")
async def mine_arguments(request: DocumentText):
    """
    Extract argument structures from text.

    Identifies premises, conclusions, and argumentation schemes.
    """
    try:
        miner = ArgumentMiner()
        arguments = await miner.extract_argument_structure(
            text=request.text,
            doc_id=request.doc_id
        )

        return {
            "success": True,
            "count": len(arguments),
            "arguments": [
                {
                    "id": arg.id,
                    "premises": [
                        {
                            "id": p.id,
                            "text": p.text,
                            "confidence": p.confidence,
                            "keywords": p.keywords
                        }
                        for p in arg.premises
                    ],
                    "conclusion": {
                        "id": arg.conclusion.id,
                        "text": arg.conclusion.text,
                        "confidence": arg.conclusion.confidence,
                        "keywords": arg.conclusion.keywords
                    },
                    "scheme": arg.scheme.value,
                    "confidence": arg.confidence,
                    "indicators": arg.indicators
                }
                for arg in arguments
            ]
        }

    except Exception as e:
        logger.error(f"Argument mining failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mine-arguments-full")
async def mine_arguments_full(
    request: DocumentText,
    background_tasks: BackgroundTasks
):
    """
    Extract arguments and their relations, create graph.

    Full argument mining pipeline including relation detection.
    """
    try:
        miner = ArgumentMiner()

        # Extract arguments
        arguments = await miner.extract_argument_structure(
            text=request.text,
            doc_id=request.doc_id
        )

        # Extract relations
        relations = await miner.detect_argument_relations(arguments)

        # Create graph (background task)
        background_tasks.add_task(
            miner.create_argument_graph,
            graph_db,
            arguments,
            relations
        )

        return {
            "success": True,
            "arguments_count": len(arguments),
            "relations_count": len(relations),
            "arguments": [
                {
                    "id": arg.id,
                    "scheme": arg.scheme.value,
                    "confidence": arg.confidence,
                    "premise_count": len(arg.premises),
                    "conclusion": arg.conclusion.text
                }
                for arg in arguments
            ],
            "relations": [
                {
                    "from": rel.from_arg_id,
                    "to": rel.to_arg_id,
                    "type": rel.relation_type.value,
                    "confidence": rel.confidence,
                    "explanation": rel.explanation
                }
                for rel in relations
            ]
        }

    except Exception as e:
        logger.error(f"Full argument mining failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Stance Detection Endpoints
# ============================================================================

@router.post("/detect-stance")
async def detect_stance(request: ClaimDocument):
    """
    Detect author stance toward a claim in a document.

    Returns stance classification with confidence and supporting quotes.
    """
    try:
        detector = StanceDetector()
        result = await detector.detect_stance(
            claim=request.claim,
            document=request.document,
            context=request.context
        )

        return {
            "success": True,
            "result": {
                "claim_id": result.claim_id,
                "doc_id": result.doc_id,
                "stance": result.stance.value,
                "confidence": result.confidence,
                "supporting_quotes": result.supporting_quotes,
                "explanation": result.explanation,
                "sentiment_score": result.sentiment_score
            }
        }

    except Exception as e:
        logger.error(f"Stance detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/detect-stances-batch")
async def detect_stances_batch(
    request: ClaimDocuments,
    background_tasks: BackgroundTasks
):
    """
    Detect stances for a claim across multiple documents.

    Returns stance distribution and detects stance shifts.
    """
    try:
        detector = StanceDetector()

        # Detect stances
        results = await detector.detect_stances_batch(
            claim=request.claim,
            documents=request.documents
        )

        # Detect shifts
        shifts = await detector.detect_stance_shifts(
            claim=request.claim,
            documents=request.documents
        )

        # Get distribution
        distribution = detector.get_stance_distribution(results)

        # Add to graph (background task)
        background_tasks.add_task(
            detector.add_stance_to_graph,
            graph_db,
            results
        )

        return {
            "success": True,
            "stances": [
                {
                    "doc_id": r.doc_id,
                    "doc_title": r.doc_title,
                    "stance": r.stance.value,
                    "confidence": r.confidence,
                    "explanation": r.explanation
                }
                for r in results
            ],
            "shifts": [
                {
                    "from_doc": s.from_doc_id,
                    "to_doc": s.to_doc_id,
                    "from_stance": s.from_stance.value,
                    "to_stance": s.to_stance.value,
                    "magnitude": s.shift_magnitude
                }
                for s in shifts
            ],
            "distribution": distribution
        }

    except Exception as e:
        logger.error(f"Batch stance detection failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Fact-Checking Endpoints
# ============================================================================

@router.post("/fact-check")
async def fact_check(request: SingleClaim):
    """
    Perform automated fact-check on a claim.

    Classifies claim type, searches sources, and verifies claim.
    Returns truth rating with sources and explanation.
    """
    try:
        checker = FactChecker()
        result = await checker.fact_check_claim(claim=request.claim)

        return {
            "success": True,
            "result": {
                "claim_id": result.claim_id,
                "claim_type": result.claim_type.value,
                "is_checkable": result.is_checkable,
                "truth_rating": result.truth_rating.value,
                "confidence": result.confidence,
                "verification_summary": result.verification_summary,
                "context_needed": result.context_needed,
                "sources": [
                    {
                        "name": src.source_name,
                        "url": src.source_url,
                        "text": src.relevant_text,
                        "credibility": src.credibility_score
                    }
                    for src in result.sources
                ],
                "badge": checker.get_fact_check_badge(result.truth_rating),
                "checked_at": result.checked_at
            }
        }

    except Exception as e:
        logger.error(f"Fact-checking failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fact-check-batch")
async def fact_check_batch(
    request: ClaimList,
    background_tasks: BackgroundTasks
):
    """
    Fact-check multiple claims.

    Processes claims in batch and adds results to graph.
    """
    try:
        checker = FactChecker()
        results = await checker.fact_check_claims_batch(claims=request.claims)

        # Add to graph (background task)
        background_tasks.add_task(
            checker.add_fact_check_to_graph,
            graph_db,
            results
        )

        return {
            "success": True,
            "count": len(results),
            "results": [
                {
                    "claim_id": r.claim_id,
                    "truth_rating": r.truth_rating.value,
                    "confidence": r.confidence,
                    "is_checkable": r.is_checkable,
                    "summary": r.verification_summary,
                    "badge": checker.get_fact_check_badge(r.truth_rating)
                }
                for r in results
            ]
        }

    except Exception as e:
        logger.error(f"Batch fact-checking failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Entity Extraction Endpoints
# ============================================================================

@router.post("/extract-entities")
async def extract_entities(request: DocumentText):
    """
    Extract named entities from text.

    Identifies persons, organizations, locations, dates, etc.
    """
    try:
        extractor = EntityExtractor()
        entities = await extractor.extract_entities(
            text=request.text,
            doc_id=request.doc_id
        )

        return {
            "success": True,
            "count": len(entities),
            "entities": [
                {
                    "id": e.id,
                    "text": e.text,
                    "type": e.entity_type.value,
                    "confidence": e.confidence,
                    "mentions": e.mentions,
                    "context": e.context
                }
                for e in entities
            ]
        }

    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-entities-full")
async def extract_entities_full(
    request: DocumentText,
    background_tasks: BackgroundTasks
):
    """
    Extract entities and relations, create entity graph.

    Full entity extraction pipeline including relation detection.
    """
    try:
        extractor = EntityExtractor()

        # Extract entities and relations
        result = await extractor.extract_entities_and_relations(
            text=request.text,
            doc_id=request.doc_id
        )

        # Create graph (background task)
        background_tasks.add_task(
            extractor.create_entity_graph,
            graph_db,
            result
        )

        if request.doc_id:
            # Link entities to claims (background task)
            background_tasks.add_task(
                extractor.link_entities_to_claims,
                graph_db,
                request.doc_id,
                result.entities
            )

        return {
            "success": True,
            "entities_count": len(result.entities),
            "relations_count": len(result.relations),
            "confidence": result.extraction_confidence,
            "entities": [
                {
                    "id": e.id,
                    "text": e.text,
                    "type": e.entity_type.value,
                    "confidence": e.confidence
                }
                for e in result.entities
            ],
            "relations": [
                {
                    "from": r.from_entity_id,
                    "to": r.to_entity_id,
                    "type": r.relation_type.value,
                    "confidence": r.confidence,
                    "evidence": r.evidence_text
                }
                for r in result.relations
            ]
        }

    except Exception as e:
        logger.error(f"Full entity extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Combined NLP Analysis
# ============================================================================

@router.post("/analyze-document")
async def analyze_document(
    request: DocumentText,
    background_tasks: BackgroundTasks
):
    """
    Run complete NLP analysis on a document.

    Performs all NLP operations:
    - Entity extraction
    - Argument mining
    - Fact-checking (if applicable)
    - Contradiction detection (with existing claims)

    This is the main endpoint for the "NLP Analysis" button.
    """
    try:
        # Initialize all processors
        entity_extractor = EntityExtractor()
        argument_miner = ArgumentMiner()

        # Extract entities and relations
        entity_result = await entity_extractor.extract_entities_and_relations(
            text=request.text,
            doc_id=request.doc_id
        )

        # Mine arguments
        arguments = await argument_miner.extract_argument_structure(
            text=request.text,
            doc_id=request.doc_id
        )

        # Create graphs (background tasks)
        background_tasks.add_task(
            entity_extractor.create_entity_graph,
            graph_db,
            entity_result
        )

        if arguments:
            relations = await argument_miner.detect_argument_relations(arguments)
            background_tasks.add_task(
                argument_miner.create_argument_graph,
                graph_db,
                arguments,
                relations
            )

        return {
            "success": True,
            "doc_id": request.doc_id,
            "analysis": {
                "entities": {
                    "count": len(entity_result.entities),
                    "types": list(set([e.entity_type.value for e in entity_result.entities]))
                },
                "relations": {
                    "count": len(entity_result.relations)
                },
                "arguments": {
                    "count": len(arguments),
                    "schemes": list(set([a.scheme.value for a in arguments]))
                }
            },
            "message": "NLP analysis completed. Results added to graph."
        }

    except Exception as e:
        logger.error(f"Document analysis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """Health check for NLP service."""
    return {
        "status": "healthy",
        "service": "NLP Analysis",
        "features": [
            "contradiction_detection",
            "argument_mining",
            "stance_detection",
            "fact_checking",
            "entity_extraction"
        ]
    }
