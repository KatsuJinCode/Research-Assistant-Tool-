"""
Framework Manager for Runtime Framework Management

Manages framework loading, caching, and switching at runtime.
Provides a singleton interface for accessing the current framework across the application.
"""

from pathlib import Path
from typing import Dict, Optional, List
import logging
import threading
from backend.frameworks.framework_loader import Framework, load_framework, validate_framework

logger = logging.getLogger(__name__)


class FrameworkManager:
    """
    Singleton manager for research frameworks.

    Handles framework loading, caching, validation, and runtime switching.

    Example:
        >>> manager = FrameworkManager()
        >>> manager.set_framework('medical_research')
        >>> framework = manager.get_current_framework()
        >>> print(framework.entity_types)
        ['Disease', 'Treatment', 'Drug', ...]
    """

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Ensure singleton instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize framework manager (only once due to singleton)."""
        if self._initialized:
            return

        self._current_framework: Optional[Framework] = None
        self._framework_cache: Dict[str, Framework] = {}
        self._frameworks_dir = Path(__file__).parent / 'templates'
        self._custom_frameworks_dir = Path.cwd() / 'custom_frameworks'
        self._initialized = True

        # Load default framework
        try:
            self.set_framework('general_research')
            logger.info("Framework manager initialized with general_research framework")
        except Exception as e:
            logger.error(f"Failed to load default framework: {e}")
            # Create minimal fallback framework
            self._current_framework = self._create_fallback_framework()

    def get_current_framework(self) -> Framework:
        """
        Get the currently active framework.

        Returns:
            Current Framework instance

        Example:
            >>> framework = manager.get_current_framework()
            >>> print(framework.name)
            'medical_research'
        """
        if self._current_framework is None:
            logger.warning("No framework loaded, using fallback")
            self._current_framework = self._create_fallback_framework()

        return self._current_framework

    def set_framework(self, framework_name: str, custom_path: Optional[Path] = None) -> None:
        """
        Set the active framework.

        Args:
            framework_name: Name of framework (e.g., 'medical_research')
            custom_path: Optional path to custom framework YAML file

        Raises:
            FileNotFoundError: If framework file doesn't exist
            ValueError: If framework validation fails

        Example:
            >>> manager.set_framework('medical_research')
            >>> manager.set_framework('custom', Path('/path/to/custom.yaml'))
        """
        # Check cache first
        cache_key = custom_path or framework_name
        if cache_key in self._framework_cache:
            self._current_framework = self._framework_cache[cache_key]
            logger.info(f"Loaded framework from cache: {framework_name}")
            return

        # Load framework
        if custom_path:
            framework = load_framework(custom_path)
        else:
            # Try built-in frameworks first
            yaml_path = self._frameworks_dir / f"{framework_name}.yaml"
            if not yaml_path.exists():
                # Try custom frameworks directory
                yaml_path = self._custom_frameworks_dir / f"{framework_name}.yaml"

            framework = load_framework(yaml_path, self._frameworks_dir)

        # Cache and activate
        self._framework_cache[cache_key] = framework
        self._current_framework = framework

        logger.info(f"Activated framework: {framework.name} v{framework.version}")

    def list_available_frameworks(self) -> List[Dict[str, str]]:
        """
        List all available frameworks (built-in and custom).

        Returns:
            List of dicts with framework metadata

        Example:
            >>> frameworks = manager.list_available_frameworks()
            >>> for fw in frameworks:
            ...     print(f"{fw['name']}: {fw['description']}")
        """
        frameworks = []

        # Built-in frameworks
        for yaml_file in self._frameworks_dir.glob('*.yaml'):
            try:
                # Load just to get metadata (will be cached)
                framework = load_framework(yaml_file, self._frameworks_dir)
                frameworks.append({
                    'name': framework.name,
                    'description': framework.description,
                    'version': framework.version,
                    'type': 'built-in',
                    'path': str(yaml_file),
                })
            except Exception as e:
                logger.warning(f"Failed to load framework {yaml_file}: {e}")

        # Custom frameworks
        if self._custom_frameworks_dir.exists():
            for yaml_file in self._custom_frameworks_dir.glob('*.yaml'):
                try:
                    framework = load_framework(yaml_file, self._frameworks_dir)
                    frameworks.append({
                        'name': framework.name,
                        'description': framework.description,
                        'version': framework.version,
                        'type': 'custom',
                        'path': str(yaml_file),
                    })
                except Exception as e:
                    logger.warning(f"Failed to load custom framework {yaml_file}: {e}")

        return frameworks

    def get_framework_details(self, framework_name: str) -> Dict:
        """
        Get detailed information about a framework.

        Args:
            framework_name: Name of framework

        Returns:
            Dict with framework details

        Example:
            >>> details = manager.get_framework_details('medical_research')
            >>> print(details['entity_types'])
            ['Disease', 'Treatment', 'Drug', ...]
        """
        # Load framework (from cache if available)
        if framework_name not in self._framework_cache:
            yaml_path = self._frameworks_dir / f"{framework_name}.yaml"
            if not yaml_path.exists():
                yaml_path = self._custom_frameworks_dir / f"{framework_name}.yaml"

            framework = load_framework(yaml_path, self._frameworks_dir)
            self._framework_cache[framework_name] = framework
        else:
            framework = self._framework_cache[framework_name]

        return framework.to_dict()

    def reload_framework(self) -> None:
        """
        Reload the current framework from disk.

        Useful for development when modifying framework files.

        Example:
            >>> manager.reload_framework()  # Reloads current framework
        """
        if self._current_framework is None:
            logger.warning("No framework to reload")
            return

        framework_name = self._current_framework.name

        # Clear cache entry
        self._framework_cache.pop(framework_name, None)

        # Reload
        self.set_framework(framework_name)
        logger.info(f"Reloaded framework: {framework_name}")

    def validate_framework_compatibility(self, framework_name: str) -> Dict[str, any]:
        """
        Validate if switching to a framework is compatible with current graph data.

        Checks:
        - Entity types used in graph are compatible
        - Relationship types used in graph are compatible
        - No data loss would occur from switching

        Args:
            framework_name: Name of framework to validate

        Returns:
            Dict with compatibility status and warnings

        Example:
            >>> result = manager.validate_framework_compatibility('medical_research')
            >>> if result['compatible']:
            ...     manager.set_framework('medical_research')
            >>> else:
            ...     print(result['warnings'])
        """
        from research_agent.graph_database import GraphDatabase

        # Load target framework
        yaml_path = self._frameworks_dir / f"{framework_name}.yaml"
        if not yaml_path.exists():
            yaml_path = self._custom_frameworks_dir / f"{framework_name}.yaml"

        target_framework = load_framework(yaml_path, self._frameworks_dir)

        # Get current graph data
        db = GraphDatabase()
        current_entity_types = set()
        current_relationship_types = set()

        for node_id, data in db.graph.nodes(data=True):
            entity_type = data.get('label', 'Unknown')
            current_entity_types.add(entity_type)

        for u, v, data in db.graph.edges(data=True):
            rel_type = data.get('type', 'Unknown')
            current_relationship_types.add(rel_type)

        # Check compatibility
        target_entity_set = set(target_framework.entity_types)
        target_rel_set = set(target_framework.relationship_types)

        unsupported_entities = current_entity_types - target_entity_set
        unsupported_relationships = current_relationship_types - target_rel_set

        compatible = len(unsupported_entities) == 0 and len(unsupported_relationships) == 0

        warnings = []
        if unsupported_entities:
            warnings.append(f"Entity types in graph not supported by framework: {unsupported_entities}")
        if unsupported_relationships:
            warnings.append(f"Relationship types in graph not supported by framework: {unsupported_relationships}")

        return {
            'compatible': compatible,
            'target_framework': framework_name,
            'current_framework': self._current_framework.name if self._current_framework else 'none',
            'unsupported_entities': list(unsupported_entities),
            'unsupported_relationships': list(unsupported_relationships),
            'warnings': warnings,
            'can_switch_safely': compatible or (len(unsupported_entities) == 0 and len(unsupported_relationships) == 0),
        }

    def create_custom_framework(
        self,
        name: str,
        base_framework: str = 'general_research',
        custom_settings: Optional[Dict] = None
    ) -> Framework:
        """
        Create a custom framework by extending a base framework.

        Args:
            name: Name for custom framework
            base_framework: Base framework to extend
            custom_settings: Custom settings to override

        Returns:
            New custom Framework

        Example:
            >>> custom = manager.create_custom_framework(
            ...     name='psychology_research',
            ...     base_framework='scientific_research',
            ...     custom_settings={
            ...         'entity_types': ['Behavior', 'Cognitive_Process'],
            ...         'relationship_types': ['INFLUENCES', 'CORRELATES_WITH']
            ...     }
            ... )
        """
        # Load base framework
        base_yaml = self._frameworks_dir / f"{base_framework}.yaml"
        base = load_framework(base_yaml, self._frameworks_dir)

        # Create custom framework data
        custom_data = {
            'name': name,
            'version': '1.0.0',
            'extends': base_framework,
            'entity_types': [],
            'relationship_types': [],
        }

        if custom_settings:
            custom_data.update(custom_settings)

        # Create and merge
        custom = Framework.from_dict(custom_data)
        merged = custom.merge_with_parent(base)

        # Save to custom frameworks directory
        self._custom_frameworks_dir.mkdir(exist_ok=True)
        custom_path = self._custom_frameworks_dir / f"{name}.yaml"

        from backend.frameworks.framework_loader import save_framework
        save_framework(merged, custom_path)

        logger.info(f"Created custom framework: {name}")
        return merged

    def _create_fallback_framework(self) -> Framework:
        """
        Create minimal fallback framework when no framework can be loaded.

        Returns:
            Minimal Framework with basic types
        """
        return Framework(
            name='fallback',
            description='Minimal fallback framework',
            version='1.0.0',
            entity_types=['Claim', 'Evidence', 'Document'],
            relationship_types=['SUPPORTS', 'CONTRADICTS', 'CITES'],
        )

    def clear_cache(self) -> None:
        """
        Clear the framework cache.

        Forces frameworks to be reloaded from disk on next access.

        Example:
            >>> manager.clear_cache()
        """
        self._framework_cache.clear()
        logger.info("Framework cache cleared")


# Global singleton instance
_global_manager: Optional[FrameworkManager] = None


def get_framework_manager() -> FrameworkManager:
    """
    Get the global FrameworkManager singleton.

    Returns:
        Global FrameworkManager instance

    Example:
        >>> from backend.frameworks import get_framework_manager
        >>> manager = get_framework_manager()
        >>> framework = manager.get_current_framework()
    """
    global _global_manager
    if _global_manager is None:
        _global_manager = FrameworkManager()
    return _global_manager
