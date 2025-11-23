"""
Framework Loader and Schema Definition

Loads and validates domain-specific research framework configurations from YAML files.
Frameworks define entity types, relationship types, prompts, and evaluation criteria
for different research domains (medical, legal, scientific, etc.).
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from pathlib import Path
import yaml
import logging

logger = logging.getLogger(__name__)


@dataclass
class PromptSet:
    """Domain-specific prompts for extraction and analysis."""
    extraction: str = ""
    analysis: str = ""
    evaluation: str = ""
    claim_simplification: str = ""
    evidence_assessment: str = ""

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary."""
        return {
            'extraction': self.extraction,
            'analysis': self.analysis,
            'evaluation': self.evaluation,
            'claim_simplification': self.claim_simplification,
            'evidence_assessment': self.evidence_assessment,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'PromptSet':
        """Create PromptSet from dictionary."""
        return cls(
            extraction=data.get('extraction', ''),
            analysis=data.get('analysis', ''),
            evaluation=data.get('evaluation', ''),
            claim_simplification=data.get('claim_simplification', ''),
            evidence_assessment=data.get('evidence_assessment', ''),
        )


@dataclass
class EvaluationCriteria:
    """Domain-specific evaluation criteria for assessing claims and evidence."""
    evidence_levels: List[str] = field(default_factory=list)
    quality_metrics: List[str] = field(default_factory=list)
    authority_indicators: List[str] = field(default_factory=list)
    minimum_confidence: float = 0.5

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'evidence_levels': self.evidence_levels,
            'quality_metrics': self.quality_metrics,
            'authority_indicators': self.authority_indicators,
            'minimum_confidence': self.minimum_confidence,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationCriteria':
        """Create EvaluationCriteria from dictionary."""
        return cls(
            evidence_levels=data.get('evidence_levels', []),
            quality_metrics=data.get('quality_metrics', []),
            authority_indicators=data.get('authority_indicators', []),
            minimum_confidence=data.get('minimum_confidence', 0.5),
        )


@dataclass
class ClaimStructure:
    """How claims are structured in this domain."""
    components: List[str] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)
    optional_fields: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'components': self.components,
            'required_fields': self.required_fields,
            'optional_fields': self.optional_fields,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ClaimStructure':
        """Create ClaimStructure from dictionary."""
        return cls(
            components=data.get('components', []),
            required_fields=data.get('required_fields', []),
            optional_fields=data.get('optional_fields', []),
        )


@dataclass
class EvidenceRequirements:
    """What counts as evidence in this domain."""
    source_types: List[str] = field(default_factory=list)
    minimum_sources: int = 1
    preferred_date_range: Optional[str] = None
    peer_review_required: bool = False

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'source_types': self.source_types,
            'minimum_sources': self.minimum_sources,
            'preferred_date_range': self.preferred_date_range,
            'peer_review_required': self.peer_review_required,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvidenceRequirements':
        """Create EvidenceRequirements from dictionary."""
        return cls(
            source_types=data.get('source_types', []),
            minimum_sources=data.get('minimum_sources', 1),
            preferred_date_range=data.get('preferred_date_range'),
            peer_review_required=data.get('peer_review_required', False),
        )


@dataclass
class SourcePreferences:
    """Preferred source types for this domain."""
    databases: List[str] = field(default_factory=list)
    journals: List[str] = field(default_factory=list)
    publication_types: List[str] = field(default_factory=list)
    authority_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'databases': self.databases,
            'journals': self.journals,
            'publication_types': self.publication_types,
            'authority_sources': self.authority_sources,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SourcePreferences':
        """Create SourcePreferences from dictionary."""
        return cls(
            databases=data.get('databases', []),
            journals=data.get('journals', []),
            publication_types=data.get('publication_types', []),
            authority_sources=data.get('authority_sources', []),
        )


@dataclass
class Framework:
    """
    Domain-specific research framework configuration.

    Attributes:
        name: Framework name (e.g., 'medical_research')
        description: Human-readable description
        version: Framework version string
        extends: Optional parent framework to inherit from
        entity_types: List of custom entity types for this domain
        relationship_types: List of custom relationship types
        prompts: Domain-specific prompts
        evaluation_criteria: Quality assessment criteria
        claim_structure: How claims are structured
        evidence_requirements: What counts as evidence
        source_preferences: Preferred source types
        metadata: Additional custom metadata

    Example:
        >>> framework = Framework(
        ...     name='medical_research',
        ...     entity_types=['Disease', 'Treatment', 'Drug'],
        ...     relationship_types=['TREATS', 'CAUSES', 'INDICATES']
        ... )
    """
    name: str
    description: str = ""
    version: str = "1.0.0"
    extends: Optional[str] = None
    entity_types: List[str] = field(default_factory=list)
    relationship_types: List[str] = field(default_factory=list)
    prompts: PromptSet = field(default_factory=PromptSet)
    evaluation_criteria: EvaluationCriteria = field(default_factory=EvaluationCriteria)
    claim_structure: ClaimStructure = field(default_factory=ClaimStructure)
    evidence_requirements: EvidenceRequirements = field(default_factory=EvidenceRequirements)
    source_preferences: SourcePreferences = field(default_factory=SourcePreferences)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert framework to dictionary for serialization."""
        return {
            'name': self.name,
            'description': self.description,
            'version': self.version,
            'extends': self.extends,
            'entity_types': self.entity_types,
            'relationship_types': self.relationship_types,
            'prompts': self.prompts.to_dict(),
            'evaluation_criteria': self.evaluation_criteria.to_dict(),
            'claim_structure': self.claim_structure.to_dict(),
            'evidence_requirements': self.evidence_requirements.to_dict(),
            'source_preferences': self.source_preferences.to_dict(),
            'metadata': self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Framework':
        """Create Framework from dictionary."""
        return cls(
            name=data.get('name', 'unknown'),
            description=data.get('description', ''),
            version=data.get('version', '1.0.0'),
            extends=data.get('extends'),
            entity_types=data.get('entity_types', []),
            relationship_types=data.get('relationship_types', []),
            prompts=PromptSet.from_dict(data.get('prompts', {})),
            evaluation_criteria=EvaluationCriteria.from_dict(data.get('evaluation_criteria', {})),
            claim_structure=ClaimStructure.from_dict(data.get('claim_structure', {})),
            evidence_requirements=EvidenceRequirements.from_dict(data.get('evidence_requirements', {})),
            source_preferences=SourcePreferences.from_dict(data.get('source_preferences', {})),
            metadata=data.get('metadata', {}),
        )

    def merge_with_parent(self, parent: 'Framework') -> 'Framework':
        """
        Merge this framework with its parent framework.

        Child framework values override parent values.
        Lists are merged (parent + child, with duplicates removed).

        Args:
            parent: Parent framework to inherit from

        Returns:
            New merged framework
        """
        return Framework(
            name=self.name,
            description=self.description or parent.description,
            version=self.version,
            extends=self.extends,
            entity_types=list(set(parent.entity_types + self.entity_types)),
            relationship_types=list(set(parent.relationship_types + self.relationship_types)),
            prompts=PromptSet(
                extraction=self.prompts.extraction or parent.prompts.extraction,
                analysis=self.prompts.analysis or parent.prompts.analysis,
                evaluation=self.prompts.evaluation or parent.prompts.evaluation,
                claim_simplification=self.prompts.claim_simplification or parent.prompts.claim_simplification,
                evidence_assessment=self.prompts.evidence_assessment or parent.prompts.evidence_assessment,
            ),
            evaluation_criteria=EvaluationCriteria(
                evidence_levels=list(set(parent.evaluation_criteria.evidence_levels + self.evaluation_criteria.evidence_levels)),
                quality_metrics=list(set(parent.evaluation_criteria.quality_metrics + self.evaluation_criteria.quality_metrics)),
                authority_indicators=list(set(parent.evaluation_criteria.authority_indicators + self.evaluation_criteria.authority_indicators)),
                minimum_confidence=self.evaluation_criteria.minimum_confidence or parent.evaluation_criteria.minimum_confidence,
            ),
            claim_structure=ClaimStructure(
                components=list(set(parent.claim_structure.components + self.claim_structure.components)),
                required_fields=list(set(parent.claim_structure.required_fields + self.claim_structure.required_fields)),
                optional_fields=list(set(parent.claim_structure.optional_fields + self.claim_structure.optional_fields)),
            ),
            evidence_requirements=EvidenceRequirements(
                source_types=list(set(parent.evidence_requirements.source_types + self.evidence_requirements.source_types)),
                minimum_sources=self.evidence_requirements.minimum_sources or parent.evidence_requirements.minimum_sources,
                preferred_date_range=self.evidence_requirements.preferred_date_range or parent.evidence_requirements.preferred_date_range,
                peer_review_required=self.evidence_requirements.peer_review_required or parent.evidence_requirements.peer_review_required,
            ),
            source_preferences=SourcePreferences(
                databases=list(set(parent.source_preferences.databases + self.source_preferences.databases)),
                journals=list(set(parent.source_preferences.journals + self.source_preferences.journals)),
                publication_types=list(set(parent.source_preferences.publication_types + self.source_preferences.publication_types)),
                authority_sources=list(set(parent.source_preferences.authority_sources + self.source_preferences.authority_sources)),
            ),
            metadata={**parent.metadata, **self.metadata},
        )


def load_framework(yaml_path: Path | str, frameworks_dir: Optional[Path] = None) -> Framework:
    """
    Load a framework from a YAML file.

    Supports framework inheritance via the 'extends' field. If a framework
    extends another, the parent is loaded and merged first.

    Args:
        yaml_path: Path to YAML file (absolute or relative to frameworks_dir)
        frameworks_dir: Base directory for framework files (defaults to backend/frameworks/templates)

    Returns:
        Loaded and validated Framework

    Raises:
        FileNotFoundError: If YAML file doesn't exist
        yaml.YAMLError: If YAML is malformed
        ValueError: If framework fails validation

    Example:
        >>> framework = load_framework('medical_research.yaml')
        >>> print(framework.entity_types)
        ['Disease', 'Treatment', 'Drug', 'Symptom', ...]
    """
    yaml_path = Path(yaml_path)

    # Determine base directory
    if frameworks_dir is None:
        frameworks_dir = Path(__file__).parent / 'templates'

    # Resolve path
    if not yaml_path.is_absolute():
        yaml_path = frameworks_dir / yaml_path

    if not yaml_path.exists():
        raise FileNotFoundError(f"Framework file not found: {yaml_path}")

    # Load YAML
    logger.info(f"Loading framework from {yaml_path}")
    with open(yaml_path, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    if not data:
        raise ValueError(f"Empty framework file: {yaml_path}")

    # Create framework
    framework = Framework.from_dict(data)

    # Handle inheritance
    if framework.extends:
        parent_path = frameworks_dir / f"{framework.extends}.yaml"
        if not parent_path.exists():
            raise FileNotFoundError(f"Parent framework not found: {parent_path}")

        logger.info(f"Loading parent framework: {framework.extends}")
        parent_framework = load_framework(parent_path, frameworks_dir)
        framework = framework.merge_with_parent(parent_framework)

    # Validate
    validate_framework(framework)

    logger.info(f"Successfully loaded framework: {framework.name} v{framework.version}")
    return framework


def validate_framework(framework: Framework) -> None:
    """
    Validate framework schema and constraints.

    Checks:
    - Required fields are present
    - Entity and relationship types are non-empty
    - Version string is valid
    - Confidence thresholds are in valid range

    Args:
        framework: Framework to validate

    Raises:
        ValueError: If validation fails

    Example:
        >>> framework = Framework(name='test')
        >>> validate_framework(framework)  # Raises ValueError - missing entity_types
    """
    errors = []

    # Check required fields
    if not framework.name:
        errors.append("Framework must have a name")

    if not framework.entity_types:
        errors.append("Framework must define at least one entity_type")

    if not framework.relationship_types:
        errors.append("Framework must define at least one relationship_type")

    # Validate version format (simple semantic versioning check)
    if framework.version:
        parts = framework.version.split('.')
        if len(parts) != 3:
            errors.append(f"Invalid version format: {framework.version} (expected X.Y.Z)")
        else:
            for part in parts:
                if not part.isdigit():
                    errors.append(f"Invalid version format: {framework.version} (parts must be numeric)")
                    break

    # Validate confidence threshold
    if not (0.0 <= framework.evaluation_criteria.minimum_confidence <= 1.0):
        errors.append(f"minimum_confidence must be between 0.0 and 1.0, got {framework.evaluation_criteria.minimum_confidence}")

    # Validate minimum sources
    if framework.evidence_requirements.minimum_sources < 1:
        errors.append(f"minimum_sources must be at least 1, got {framework.evidence_requirements.minimum_sources}")

    # Check for duplicate entity types
    if len(framework.entity_types) != len(set(framework.entity_types)):
        duplicates = [t for t in framework.entity_types if framework.entity_types.count(t) > 1]
        errors.append(f"Duplicate entity types: {set(duplicates)}")

    # Check for duplicate relationship types
    if len(framework.relationship_types) != len(set(framework.relationship_types)):
        duplicates = [t for t in framework.relationship_types if framework.relationship_types.count(t) > 1]
        errors.append(f"Duplicate relationship types: {set(duplicates)}")

    # Raise all errors at once
    if errors:
        raise ValueError("Framework validation failed:\n" + "\n".join(f"  - {e}" for e in errors))

    logger.debug(f"Framework validation passed: {framework.name}")


def save_framework(framework: Framework, yaml_path: Path | str) -> None:
    """
    Save a framework to a YAML file.

    Args:
        framework: Framework to save
        yaml_path: Path to output YAML file

    Example:
        >>> framework = Framework(name='custom', entity_types=['Thing'])
        >>> save_framework(framework, 'custom.yaml')
    """
    yaml_path = Path(yaml_path)

    # Validate before saving
    validate_framework(framework)

    # Convert to dict
    data = framework.to_dict()

    # Save to YAML
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    logger.info(f"Framework saved to {yaml_path}")
