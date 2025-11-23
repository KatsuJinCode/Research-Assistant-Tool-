"""
Entity and Relation Extraction Module.

Extracts named entities and their relationships from text.
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import json

from .base_nlp import BaseNLPProcessor

logger = logging.getLogger(__name__)


class EntityType(Enum):
    """Named entity types."""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    EVENT = "event"
    CONCEPT = "concept"
    QUANTITY = "quantity"
    PRODUCT = "product"
    OTHER = "other"


class RelationType(Enum):
    """Entity relationship types."""
    WORKS_FOR = "works_for"  # Person works for Organization
    LOCATED_IN = "located_in"  # Entity located in Location
    PARTICIPATED_IN = "participated_in"  # Person/Org participated in Event
    RELATED_TO = "related_to"  # Generic relation
    CAUSED_BY = "caused_by"  # Causal relation
    PART_OF = "part_of"  # Part-whole relation
    ASSOCIATED_WITH = "associated_with"  # Association


@dataclass
class Entity:
    """An extracted entity."""
    id: str
    text: str
    entity_type: EntityType
    confidence: float
    mentions: List[str]  # All mentions in text
    context: Optional[str] = None
    linked_id: Optional[str] = None  # Link to knowledge base


@dataclass
class EntityRelation:
    """Relationship between entities."""
    id: str
    from_entity_id: str
    to_entity_id: str
    relation_type: RelationType
    confidence: float
    evidence_text: str  # Text supporting the relation


@dataclass
class EntityExtractionResult:
    """Result of entity extraction."""
    doc_id: str
    entities: List[Entity]
    relations: List[EntityRelation]
    extraction_confidence: float


class EntityExtractor(BaseNLPProcessor):
    """
    Extracts named entities and relationships from text.

    Uses AI to identify entities (persons, organizations, locations, etc.)
    and extract relationships between them.
    """

    def __init__(self, **kwargs):
        """Initialize entity extractor."""
        super().__init__(**kwargs)

    async def extract_entities(
        self,
        text: str,
        doc_id: Optional[str] = None
    ) -> List[Entity]:
        """
        Extract named entities from text.

        Args:
            text: Input text
            doc_id: Optional document ID

        Returns:
            List of extracted entities
        """
        # Chunk text if too long
        chunks = self.chunk_text(text, max_chunk_size=3000)

        all_entities = []
        entity_counter = 0

        for chunk in chunks:
            prompt = f"""Extract named entities from this text:

"{chunk}"

Identify:
1. Persons (names of people)
2. Organizations (companies, institutions)
3. Locations (places, countries, cities)
4. Dates (specific dates, time periods)
5. Events (named events, conferences, etc.)
6. Concepts (key concepts, theories)
7. Quantities (numbers, measurements)
8. Products (specific products, technologies)

For each entity, provide:
- The entity text
- Type (person, organization, location, date, event, concept, quantity, product, other)
- Confidence (0-100)
- All mentions in the text"""

            schema = {
                "entities": [
                    {
                        "text": "string - entity text",
                        "entity_type": "string - person, organization, location, date, event, concept, quantity, product, or other",
                        "confidence": "number - 0-100",
                        "mentions": ["array of strings - all mentions"],
                        "context": "string - brief context or null"
                    }
                ]
            }

            try:
                result = await self.analyze_with_schema(prompt, schema, temperature=0.2)

                for ent_data in result.get('entities', []):
                    entity_counter += 1

                    # Parse entity type
                    type_str = ent_data.get('entity_type', 'other').lower()
                    entity_type = EntityType.OTHER
                    for et in EntityType:
                        if et.value == type_str:
                            entity_type = et
                            break

                    all_entities.append(Entity(
                        id=f"entity_{entity_counter}",
                        text=ent_data.get('text', ''),
                        entity_type=entity_type,
                        confidence=float(ent_data.get('confidence', 0.0)),
                        mentions=ent_data.get('mentions', []),
                        context=ent_data.get('context', None)
                    ))

            except Exception as e:
                logger.error(f"Entity extraction failed for chunk: {e}")
                continue

        # Deduplicate entities by text (case-insensitive)
        unique_entities = {}
        for entity in all_entities:
            key = entity.text.lower()
            if key not in unique_entities or entity.confidence > unique_entities[key].confidence:
                unique_entities[key] = entity

        deduplicated = list(unique_entities.values())
        logger.info(f"Extracted {len(deduplicated)} unique entities from text")

        return deduplicated

    async def extract_relations(
        self,
        text: str,
        entities: List[Entity]
    ) -> List[EntityRelation]:
        """
        Extract relationships between entities.

        Args:
            text: Input text
            entities: List of extracted entities

        Returns:
            List of entity relations
        """
        if len(entities) < 2:
            logger.info("Not enough entities to extract relations")
            return []

        # Create entity reference list
        entity_list = "\n".join([
            f"- {e.id}: {e.text} ({e.entity_type.value})"
            for e in entities
        ])

        # Chunk text if needed
        chunks = self.chunk_text(text, max_chunk_size=3000)

        all_relations = []
        relation_counter = 0

        for chunk in chunks:
            prompt = f"""Extract relationships between entities in this text:

Entities:
{entity_list}

Text:
"{chunk}"

Identify relationships such as:
- works_for (Person works for Organization)
- located_in (Entity located in Location)
- participated_in (Person/Org participated in Event)
- caused_by (Event caused by Entity)
- part_of (Entity is part of another Entity)
- associated_with (Entity associated with another)
- related_to (Generic relation)

For each relationship, provide:
- From entity ID
- To entity ID
- Relation type
- Confidence (0-100)
- Evidence text from the passage"""

            schema = {
                "relations": [
                    {
                        "from_entity_id": "string - source entity ID",
                        "to_entity_id": "string - target entity ID",
                        "relation_type": "string - works_for, located_in, participated_in, caused_by, part_of, associated_with, or related_to",
                        "confidence": "number - 0-100",
                        "evidence_text": "string - supporting text"
                    }
                ]
            }

            try:
                result = await self.analyze_with_schema(prompt, schema, temperature=0.3)

                for rel_data in result.get('relations', []):
                    relation_counter += 1

                    # Parse relation type
                    type_str = rel_data.get('relation_type', 'related_to').lower()
                    relation_type = RelationType.RELATED_TO
                    for rt in RelationType:
                        if rt.value == type_str:
                            relation_type = rt
                            break

                    all_relations.append(EntityRelation(
                        id=f"relation_{relation_counter}",
                        from_entity_id=rel_data.get('from_entity_id', ''),
                        to_entity_id=rel_data.get('to_entity_id', ''),
                        relation_type=relation_type,
                        confidence=float(rel_data.get('confidence', 0.0)),
                        evidence_text=rel_data.get('evidence_text', '')
                    ))

            except Exception as e:
                logger.error(f"Relation extraction failed for chunk: {e}")
                continue

        logger.info(f"Extracted {len(all_relations)} entity relations")
        return all_relations

    async def extract_entities_and_relations(
        self,
        text: str,
        doc_id: Optional[str] = None
    ) -> EntityExtractionResult:
        """
        Extract both entities and relations from text.

        Args:
            text: Input text
            doc_id: Optional document ID

        Returns:
            EntityExtractionResult with entities and relations
        """
        logger.info(f"Extracting entities and relations from document {doc_id}")

        # Step 1: Extract entities
        entities = await self.extract_entities(text, doc_id)

        # Step 2: Extract relations
        relations = await self.extract_relations(text, entities)

        # Calculate overall confidence
        entity_confidences = [e.confidence for e in entities]
        relation_confidences = [r.confidence for r in relations]

        all_confidences = entity_confidences + relation_confidences
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

        return EntityExtractionResult(
            doc_id=doc_id or 'unknown',
            entities=entities,
            relations=relations,
            extraction_confidence=avg_confidence
        )

    async def link_entities_to_claims(
        self,
        graph_db,
        doc_id: str,
        entities: List[Entity]
    ) -> int:
        """
        Link extracted entities to claims in the same document.

        Args:
            graph_db: GraphDatabase instance
            doc_id: Document ID
            entities: List of extracted entities

        Returns:
            Number of links created
        """
        # Get all claims from this document
        claims = graph_db.find_nodes('Claim', {'doc_id': doc_id})

        links_created = 0

        for claim in claims:
            claim_text = claim.get('text', '').lower()

            # Check which entities appear in this claim
            for entity in entities:
                # Check if entity text appears in claim
                if entity.text.lower() in claim_text:
                    # Create MENTIONS relationship
                    graph_db.create_relationship(
                        from_node=claim['id'],
                        to_node=entity.id,
                        rel_type='MENTIONS',
                        properties={
                            'entity_type': entity.entity_type.value,
                            'confidence': entity.confidence
                        }
                    )
                    links_created += 1

        logger.info(f"Created {links_created} entity-claim links")
        return links_created

    def create_entity_graph(
        self,
        graph_db,
        extraction_result: EntityExtractionResult
    ) -> Dict[str, int]:
        """
        Create entity graph in database.

        Args:
            graph_db: GraphDatabase instance
            extraction_result: Entity extraction result

        Returns:
            Stats dict with counts
        """
        stats = {
            'entities': 0,
            'relations': 0
        }

        # Create entity nodes
        entity_id_map = {}  # Map from temp IDs to graph IDs

        for entity in extraction_result.entities:
            node_id = graph_db.create_node('Entity', {
                'text': entity.text,
                'entity_type': entity.entity_type.value,
                'confidence': entity.confidence,
                'mentions': json.dumps(entity.mentions),
                'context': entity.context,
                'linked_id': entity.linked_id
            })

            entity_id_map[entity.id] = node_id
            stats['entities'] += 1

            # Link to document
            if extraction_result.doc_id:
                graph_db.create_relationship(
                    from_node=extraction_result.doc_id,
                    to_node=node_id,
                    rel_type='CONTAINS_ENTITY',
                    properties={}
                )

        # Create entity relations
        for relation in extraction_result.relations:
            from_node = entity_id_map.get(relation.from_entity_id)
            to_node = entity_id_map.get(relation.to_entity_id)

            if from_node and to_node:
                graph_db.create_relationship(
                    from_node=from_node,
                    to_node=to_node,
                    rel_type=relation.relation_type.value.upper(),
                    properties={
                        'confidence': relation.confidence,
                        'evidence_text': relation.evidence_text
                    }
                )
                stats['relations'] += 1

        logger.info(f"Created entity graph: {stats}")
        return stats

    def get_entity_network(
        self,
        graph_db,
        entity_id: str,
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get network of entities connected to a given entity.

        Args:
            graph_db: GraphDatabase instance
            entity_id: Starting entity ID
            max_depth: Maximum traversal depth

        Returns:
            Network data for visualization
        """
        visited = set()
        nodes = []
        edges = []

        def traverse(current_id, depth):
            if depth > max_depth or current_id in visited:
                return

            visited.add(current_id)
            entity = graph_db.get_node(current_id)

            if entity:
                nodes.append({
                    'id': current_id,
                    'text': entity.get('text', ''),
                    'type': entity.get('entity_type', 'other'),
                    'confidence': entity.get('confidence', 0.0)
                })

                # Get related entities
                relations = graph_db.get_relationships(current_id, direction='both')

                for target_id, rel_data in relations:
                    rel_type = rel_data.get('type', 'RELATED_TO')

                    # Only follow entity relations
                    if rel_type.upper() in [rt.value.upper() for rt in RelationType]:
                        edges.append({
                            'from': current_id,
                            'to': target_id,
                            'type': rel_type,
                            'confidence': rel_data.get('confidence', 0.0)
                        })

                        traverse(target_id, depth + 1)

        traverse(entity_id, 0)

        return {
            'nodes': nodes,
            'edges': edges,
            'center_entity': entity_id
        }
