"""
Argument Mining and Structure Extraction Module.

Extracts argument structures from documents including premises,
conclusions, and their relationships.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

from .base_nlp import BaseNLPProcessor

logger = logging.getLogger(__name__)


class ArgumentScheme(Enum):
    """Types of argument schemes."""
    DEDUCTIVE = "deductive"  # Logical deduction
    INDUCTIVE = "inductive"  # Inductive reasoning
    ABDUCTIVE = "abductive"  # Inference to best explanation
    CAUSAL = "causal"  # Causal reasoning
    ANALOGY = "analogy"  # Argument by analogy
    AUTHORITY = "authority"  # Argument from authority
    UNKNOWN = "unknown"


class ArgumentRelationType(Enum):
    """Types of argument relationships."""
    SUPPORTS = "supports"  # Premise supports conclusion
    ATTACKS = "attacks"  # Argument attacks another
    REBUTS = "rebuts"  # Rebuts the conclusion
    UNDERCUTS = "undercuts"  # Undercuts the inference


@dataclass
class Premise:
    """A premise in an argument."""
    id: str
    text: str
    confidence: float
    keywords: List[str]


@dataclass
class Conclusion:
    """A conclusion in an argument."""
    id: str
    text: str
    confidence: float
    keywords: List[str]


@dataclass
class Argument:
    """An argument structure."""
    id: str
    premises: List[Premise]
    conclusion: Conclusion
    scheme: ArgumentScheme
    confidence: float
    indicators: List[str]  # Argumentation indicators (e.g., "therefore")
    source_doc_id: Optional[str] = None


@dataclass
class ArgumentRelation:
    """Relationship between arguments."""
    from_arg_id: str
    to_arg_id: str
    relation_type: ArgumentRelationType
    confidence: float
    explanation: str


class ArgumentMiner(BaseNLPProcessor):
    """
    Extracts argument structures from text.

    Identifies premises, conclusions, argument schemes, and relationships.
    """

    # Common argumentation indicators
    CONCLUSION_INDICATORS = [
        'therefore', 'thus', 'hence', 'consequently', 'so', 'accordingly',
        'it follows that', 'we can conclude', 'in conclusion', 'as a result',
        'implies that', 'suggests that', 'demonstrates that', 'proves that'
    ]

    PREMISE_INDICATORS = [
        'because', 'since', 'given that', 'as', 'for', 'assuming that',
        'granted that', 'seeing that', 'in view of', 'on account of',
        'due to', 'owing to', 'may be inferred from', 'based on'
    ]

    def __init__(self, **kwargs):
        """Initialize argument miner."""
        super().__init__(**kwargs)

    async def extract_argument_structure(
        self,
        text: str,
        doc_id: Optional[str] = None
    ) -> List[Argument]:
        """
        Extract argument structures from text.

        Args:
            text: Input text
            doc_id: Optional document ID

        Returns:
            List of extracted arguments
        """
        # Find argumentation indicators
        indicators = self._find_indicators(text)

        # Use AI to extract argument structure
        prompt = f"""Extract the argument structure from this text:

"{text}"

Identify:
1. Premises (supporting statements)
2. Conclusions (claims being argued for)
3. The type of reasoning used (deductive, inductive, abductive, causal, analogy, authority)
4. Argumentation indicators (words like "therefore", "because", etc.)

Analyze the logical structure and respond with the argument components."""

        schema = {
            "arguments": [
                {
                    "premises": [
                        {
                            "text": "string - premise text",
                            "confidence": "number - 0-100"
                        }
                    ],
                    "conclusion": {
                        "text": "string - conclusion text",
                        "confidence": "number - 0-100"
                    },
                    "scheme": "string - deductive, inductive, abductive, causal, analogy, authority, or unknown",
                    "confidence": "number - 0-100",
                    "indicators": ["array of strings - argumentation indicators found"]
                }
            ]
        }

        try:
            result = await self.analyze_with_schema(prompt, schema, temperature=0.3)

            arguments = []
            arg_counter = 0

            for arg_data in result.get('arguments', []):
                arg_counter += 1
                arg_id = f"arg_{arg_counter}"

                # Parse premises
                premises = []
                for i, prem_data in enumerate(arg_data.get('premises', [])):
                    prem_text = prem_data.get('text', '')
                    premises.append(Premise(
                        id=f"{arg_id}_prem_{i+1}",
                        text=prem_text,
                        confidence=float(prem_data.get('confidence', 0.0)),
                        keywords=self.extract_keywords(prem_text, top_n=5)
                    ))

                # Parse conclusion
                concl_data = arg_data.get('conclusion', {})
                concl_text = concl_data.get('text', '')
                conclusion = Conclusion(
                    id=f"{arg_id}_concl",
                    text=concl_text,
                    confidence=float(concl_data.get('confidence', 0.0)),
                    keywords=self.extract_keywords(concl_text, top_n=5)
                )

                # Parse scheme
                scheme_str = arg_data.get('scheme', 'unknown').lower()
                scheme = ArgumentScheme.UNKNOWN
                for sch in ArgumentScheme:
                    if sch.value == scheme_str:
                        scheme = sch
                        break

                # Create argument
                arguments.append(Argument(
                    id=arg_id,
                    premises=premises,
                    conclusion=conclusion,
                    scheme=scheme,
                    confidence=float(arg_data.get('confidence', 0.0)),
                    indicators=arg_data.get('indicators', []),
                    source_doc_id=doc_id
                ))

            logger.info(f"Extracted {len(arguments)} arguments from text")
            return arguments

        except Exception as e:
            logger.error(f"Argument extraction failed: {e}")
            return []

    def _find_indicators(self, text: str) -> Dict[str, List[str]]:
        """
        Find argumentation indicators in text.

        Args:
            text: Input text

        Returns:
            Dict with 'conclusion' and 'premise' indicators found
        """
        text_lower = text.lower()

        conclusion_found = [
            ind for ind in self.CONCLUSION_INDICATORS
            if ind in text_lower
        ]

        premise_found = [
            ind for ind in self.PREMISE_INDICATORS
            if ind in text_lower
        ]

        return {
            'conclusion': conclusion_found,
            'premise': premise_found
        }

    async def detect_argument_relations(
        self,
        arguments: List[Argument]
    ) -> List[ArgumentRelation]:
        """
        Detect relationships between arguments.

        Args:
            arguments: List of arguments to analyze

        Returns:
            List of argument relations
        """
        relations = []

        # Pairwise comparison
        for i in range(len(arguments)):
            for j in range(i + 1, len(arguments)):
                arg1 = arguments[i]
                arg2 = arguments[j]

                # Use AI to detect relation
                prompt = f"""Analyze the relationship between these two arguments:

Argument 1:
Premises: {', '.join([p.text for p in arg1.premises])}
Conclusion: {arg1.conclusion.text}

Argument 2:
Premises: {', '.join([p.text for p in arg2.premises])}
Conclusion: {arg2.conclusion.text}

Does one argument support, attack, rebut, or undercut the other?"""

                schema = {
                    "has_relation": "boolean - true if there is a relation",
                    "relation_type": "string - supports, attacks, rebuts, undercuts, or none",
                    "direction": "string - 1_to_2 or 2_to_1",
                    "confidence": "number - 0-100",
                    "explanation": "string - brief explanation"
                }

                try:
                    result = await self.analyze_with_schema(prompt, schema, temperature=0.2)

                    if result.get('has_relation', False):
                        # Determine direction
                        from_id = arg1.id if result.get('direction') == '1_to_2' else arg2.id
                        to_id = arg2.id if result.get('direction') == '1_to_2' else arg1.id

                        # Parse relation type
                        rel_type_str = result.get('relation_type', 'none').lower()
                        rel_type = ArgumentRelationType.SUPPORTS  # default
                        for rt in ArgumentRelationType:
                            if rt.value == rel_type_str:
                                rel_type = rt
                                break

                        relations.append(ArgumentRelation(
                            from_arg_id=from_id,
                            to_arg_id=to_id,
                            relation_type=rel_type,
                            confidence=float(result.get('confidence', 0.0)),
                            explanation=result.get('explanation', '')
                        ))

                except Exception as e:
                    logger.error(f"Relation detection failed: {e}")
                    continue

        logger.info(f"Detected {len(relations)} argument relations")
        return relations

    async def create_argument_graph(
        self,
        graph_db,
        arguments: List[Argument],
        relations: List[ArgumentRelation]
    ) -> Dict[str, int]:
        """
        Create argument graph in database.

        Args:
            graph_db: GraphDatabase instance
            arguments: List of arguments
            relations: List of argument relations

        Returns:
            Stats dict with counts
        """
        stats = {
            'arguments': 0,
            'premises': 0,
            'conclusions': 0,
            'relations': 0
        }

        # Create argument nodes
        for arg in arguments:
            # Create Argument node
            arg_node_id = graph_db.create_node('Argument', {
                'id': arg.id,
                'scheme': arg.scheme.value,
                'confidence': arg.confidence,
                'indicators': json.dumps(arg.indicators),
                'source_doc_id': arg.source_doc_id
            })
            stats['arguments'] += 1

            # Create Premise nodes
            for premise in arg.premises:
                prem_node_id = graph_db.create_node('Premise', {
                    'id': premise.id,
                    'text': premise.text,
                    'confidence': premise.confidence,
                    'keywords': json.dumps(premise.keywords)
                })
                stats['premises'] += 1

                # Link to argument
                graph_db.create_relationship(
                    from_node=prem_node_id,
                    to_node=arg_node_id,
                    rel_type='SUPPORTS',
                    properties={'role': 'premise'}
                )

            # Create Conclusion node
            concl_node_id = graph_db.create_node('Conclusion', {
                'id': arg.conclusion.id,
                'text': arg.conclusion.text,
                'confidence': arg.conclusion.confidence,
                'keywords': json.dumps(arg.conclusion.keywords)
            })
            stats['conclusions'] += 1

            # Link to argument
            graph_db.create_relationship(
                from_node=arg_node_id,
                to_node=concl_node_id,
                rel_type='HAS_CONCLUSION',
                properties={'role': 'conclusion'}
            )

            # Link to document if available
            if arg.source_doc_id:
                graph_db.create_relationship(
                    from_node=arg.source_doc_id,
                    to_node=arg_node_id,
                    rel_type='CONTAINS_ARGUMENT',
                    properties={}
                )

        # Create argument relations
        for relation in relations:
            graph_db.create_relationship(
                from_node=relation.from_arg_id,
                to_node=relation.to_arg_id,
                rel_type=relation.relation_type.value.upper(),
                properties={
                    'confidence': relation.confidence,
                    'explanation': relation.explanation
                }
            )
            stats['relations'] += 1

        logger.info(f"Created argument graph: {stats}")
        return stats
