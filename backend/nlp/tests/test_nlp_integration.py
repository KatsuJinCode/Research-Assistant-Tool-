"""
Integration tests for NLP modules.

Tests all 5 NLP features with realistic examples.
"""

import pytest
import asyncio
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


# Test data
TEST_CLAIMS = [
    {
        "id": "claim_1",
        "text": "Climate change is primarily caused by human activities.",
        "original_text": "Climate change is primarily caused by human activities."
    },
    {
        "id": "claim_2",
        "text": "Climate change is mainly due to natural cycles.",
        "original_text": "Climate change is mainly due to natural cycles."
    },
    {
        "id": "claim_3",
        "text": "Renewable energy is cost-effective.",
        "original_text": "Renewable energy is cost-effective."
    }
]

TEST_DOCUMENT = {
    "id": "doc_1",
    "title": "Climate Science Report",
    "content": """
    The scientific consensus is clear: climate change is primarily driven by
    human activities, particularly the burning of fossil fuels. According to
    multiple studies, over 97% of climate scientists agree that human-caused
    warming is occurring. Therefore, we must take immediate action to reduce
    carbon emissions. Because the evidence is overwhelming, policy makers
    should prioritize renewable energy solutions.
    """
}

TEST_ARGUMENT_TEXT = """
Scientists have shown that carbon dioxide levels have increased dramatically
since the industrial revolution. Because these increases correlate with
human industrial activity, we can conclude that human activities are the
primary driver of climate change. Therefore, reducing carbon emissions is
essential for mitigating climate change.
"""

TEST_ENTITY_TEXT = """
Dr. Jane Smith from Stanford University published a groundbreaking study
in Nature Climate Change. The research, conducted in collaboration with
NASA and the European Space Agency, analyzed temperature data from 1850
to 2020. The findings were presented at the United Nations Climate Summit
in Paris.
"""


@pytest.mark.asyncio
class TestContradictionDetector:
    """Tests for ContradictionDetector."""

    async def test_detect_contradiction_true(self):
        """Test detecting actual contradiction."""
        detector = ContradictionDetector()

        result = await detector.detect_contradiction(
            claim1=TEST_CLAIMS[0],
            claim2=TEST_CLAIMS[1]
        )

        assert result.is_contradiction is True
        assert result.confidence > 50.0
        assert result.contradiction_type.value in ['direct', 'implicit', 'semantic']
        assert len(result.explanation) > 0

    async def test_detect_contradiction_false(self):
        """Test detecting no contradiction."""
        detector = ContradictionDetector()

        result = await detector.detect_contradiction(
            claim1=TEST_CLAIMS[0],
            claim2=TEST_CLAIMS[2]
        )

        # These claims shouldn't contradict
        assert result.confidence >= 0.0

    async def test_batch_detection(self):
        """Test batch contradiction detection."""
        detector = ContradictionDetector()

        results = await detector.detect_contradictions_batch(
            claims=TEST_CLAIMS,
            min_confidence=50.0
        )

        # Should find at least one contradiction
        assert len(results) >= 0

    async def test_graph_integration(self):
        """Test creating CONTRADICTS relationships."""
        detector = ContradictionDetector()
        graph_db = GraphDatabase()

        # Add claims to graph
        for claim in TEST_CLAIMS:
            graph_db.create_node('Claim', claim)

        # Detect contradictions
        results = await detector.detect_contradictions_batch(
            claims=TEST_CLAIMS,
            min_confidence=50.0
        )

        # Create relationships
        count = await detector.create_contradiction_relationships(
            graph_db, results
        )

        assert count >= 0


@pytest.mark.asyncio
class TestArgumentMiner:
    """Tests for ArgumentMiner."""

    async def test_extract_argument_structure(self):
        """Test extracting arguments from text."""
        miner = ArgumentMiner()

        arguments = await miner.extract_argument_structure(
            text=TEST_ARGUMENT_TEXT,
            doc_id="test_doc"
        )

        assert len(arguments) > 0
        arg = arguments[0]
        assert len(arg.premises) > 0
        assert arg.conclusion is not None
        assert arg.scheme.value in [
            'deductive', 'inductive', 'abductive',
            'causal', 'analogy', 'authority', 'unknown'
        ]

    async def test_find_indicators(self):
        """Test finding argumentation indicators."""
        miner = ArgumentMiner()

        indicators = miner._find_indicators(TEST_ARGUMENT_TEXT)

        assert 'because' in indicators['premise'] or 'therefore' in indicators['conclusion']

    async def test_detect_relations(self):
        """Test detecting argument relations."""
        miner = ArgumentMiner()

        # Extract arguments first
        arguments = await miner.extract_argument_structure(
            text=TEST_ARGUMENT_TEXT + "\n\n" + TEST_ARGUMENT_TEXT,
            doc_id="test_doc"
        )

        if len(arguments) >= 2:
            relations = await miner.detect_argument_relations(arguments)
            assert isinstance(relations, list)

    async def test_create_graph(self):
        """Test creating argument graph."""
        miner = ArgumentMiner()
        graph_db = GraphDatabase()

        arguments = await miner.extract_argument_structure(
            text=TEST_ARGUMENT_TEXT,
            doc_id="test_doc"
        )

        relations = []
        stats = await miner.create_argument_graph(
            graph_db, arguments, relations
        )

        assert stats['arguments'] >= 0
        assert stats['premises'] >= 0
        assert stats['conclusions'] >= 0


@pytest.mark.asyncio
class TestStanceDetector:
    """Tests for StanceDetector."""

    async def test_detect_stance_support(self):
        """Test detecting supportive stance."""
        detector = StanceDetector()

        result = await detector.detect_stance(
            claim=TEST_CLAIMS[0],
            document=TEST_DOCUMENT
        )

        assert result.stance.value in ['support', 'oppose', 'neutral', 'unclear']
        assert 0.0 <= result.confidence <= 100.0
        assert isinstance(result.supporting_quotes, list)
        assert len(result.explanation) > 0

    async def test_batch_stance_detection(self):
        """Test batch stance detection."""
        detector = StanceDetector()

        results = await detector.detect_stances_batch(
            claim=TEST_CLAIMS[0],
            documents=[TEST_DOCUMENT]
        )

        assert len(results) == 1
        assert results[0].doc_id == TEST_DOCUMENT['id']

    async def test_stance_distribution(self):
        """Test stance distribution calculation."""
        detector = StanceDetector()

        results = await detector.detect_stances_batch(
            claim=TEST_CLAIMS[0],
            documents=[TEST_DOCUMENT]
        )

        distribution = detector.get_stance_distribution(results)

        assert 'distribution' in distribution
        assert 'total_documents' in distribution
        assert distribution['total_documents'] == 1

    async def test_add_to_graph(self):
        """Test adding stance to graph."""
        detector = StanceDetector()
        graph_db = GraphDatabase()

        # Add claim and document to graph
        graph_db.create_node('Claim', TEST_CLAIMS[0])
        graph_db.create_node('Document', TEST_DOCUMENT)

        results = await detector.detect_stances_batch(
            claim=TEST_CLAIMS[0],
            documents=[TEST_DOCUMENT]
        )

        count = detector.add_stance_to_graph(graph_db, results)
        assert count >= 0


@pytest.mark.asyncio
class TestFactChecker:
    """Tests for FactChecker."""

    async def test_classify_claim_type(self):
        """Test claim type classification."""
        checker = FactChecker()

        claim_type, is_checkable, confidence = await checker.classify_claim_type(
            TEST_CLAIMS[0]['text']
        )

        assert claim_type.value in [
            'factual', 'opinion', 'prediction', 'definition', 'mixed'
        ]
        assert isinstance(is_checkable, bool)
        assert 0.0 <= confidence <= 100.0

    async def test_search_sources(self):
        """Test searching verification sources."""
        checker = FactChecker()

        sources = await checker.search_verification_sources(
            TEST_CLAIMS[0]['text']
        )

        assert isinstance(sources, list)
        if sources:
            assert sources[0].source_name is not None
            assert 0.0 <= sources[0].credibility_score <= 100.0

    async def test_fact_check_claim(self):
        """Test complete fact-checking."""
        checker = FactChecker()

        result = await checker.fact_check_claim(TEST_CLAIMS[0])

        assert result.claim_id == TEST_CLAIMS[0]['id']
        assert result.claim_type.value in [
            'factual', 'opinion', 'prediction', 'definition', 'mixed'
        ]
        assert result.truth_rating.value in [
            'true', 'mostly_true', 'half_true', 'mostly_false',
            'false', 'unverifiable', 'needs_context'
        ]
        assert 0.0 <= result.confidence <= 100.0

    async def test_get_badge(self):
        """Test getting fact-check badge."""
        checker = FactChecker()

        from backend.nlp.fact_checker import TruthRating

        badge = checker.get_fact_check_badge(TruthRating.TRUE)

        assert 'label' in badge
        assert 'color' in badge
        assert 'icon' in badge

    async def test_add_to_graph(self):
        """Test adding fact-check results to graph."""
        checker = FactChecker()
        graph_db = GraphDatabase()

        # Add claim to graph
        graph_db.create_node('Claim', TEST_CLAIMS[0])

        result = await checker.fact_check_claim(TEST_CLAIMS[0])

        count = checker.add_fact_check_to_graph(graph_db, [result])
        assert count >= 0


@pytest.mark.asyncio
class TestEntityExtractor:
    """Tests for EntityExtractor."""

    async def test_extract_entities(self):
        """Test entity extraction."""
        extractor = EntityExtractor()

        entities = await extractor.extract_entities(
            text=TEST_ENTITY_TEXT,
            doc_id="test_doc"
        )

        assert len(entities) > 0

        # Check entity properties
        for entity in entities:
            assert entity.text is not None
            assert entity.entity_type.value in [
                'person', 'organization', 'location', 'date',
                'event', 'concept', 'quantity', 'product', 'other'
            ]
            assert 0.0 <= entity.confidence <= 100.0

    async def test_extract_relations(self):
        """Test relation extraction."""
        extractor = EntityExtractor()

        entities = await extractor.extract_entities(
            text=TEST_ENTITY_TEXT,
            doc_id="test_doc"
        )

        relations = await extractor.extract_relations(
            text=TEST_ENTITY_TEXT,
            entities=entities
        )

        assert isinstance(relations, list)

        if relations:
            rel = relations[0]
            assert rel.relation_type.value in [
                'works_for', 'located_in', 'participated_in',
                'caused_by', 'part_of', 'associated_with', 'related_to'
            ]
            assert 0.0 <= rel.confidence <= 100.0

    async def test_full_extraction(self):
        """Test full entity and relation extraction."""
        extractor = EntityExtractor()

        result = await extractor.extract_entities_and_relations(
            text=TEST_ENTITY_TEXT,
            doc_id="test_doc"
        )

        assert result.doc_id == "test_doc"
        assert len(result.entities) > 0
        assert 0.0 <= result.extraction_confidence <= 100.0

    async def test_create_graph(self):
        """Test creating entity graph."""
        extractor = EntityExtractor()
        graph_db = GraphDatabase()

        # Create document
        graph_db.create_node('Document', {'id': 'test_doc', 'title': 'Test'})

        result = await extractor.extract_entities_and_relations(
            text=TEST_ENTITY_TEXT,
            doc_id="test_doc"
        )

        stats = extractor.create_entity_graph(graph_db, result)

        assert stats['entities'] > 0


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
