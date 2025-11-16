# Agent Philosophy Framework & Claim Normalization System

## Overview

This document extends the architecture with:

1. **ClaimNormalizer Agent**: Analyzes, simplifies, and decomposes claims while tracking presuppositions
2. **Philosophy Framework System**: Configurable cognitive frameworks that shape how agents think
3. **Investigation Tree Visualization**: Elegant display of claim branching and verification chains

## Part 1: ClaimNormalizer Agent

### Purpose

The ClaimNormalizer is a specialized meta-agent that:
- **Simplifies** claims to their core logical form without changing meaning
- **Decomposes** compound claims into atomic sub-claims
- **Identifies** presuppositions and hidden assumptions
- **Maps** hierarchical relationships between claim elements
- **Organizes** claim trees for optimal agent routing and report generation

### ClaimNormalizer Workflow

```
Original Claim (from document):
"Renewable energy can meet 100% of global energy needs by 2050 if governments
implement aggressive carbon pricing and investment in grid infrastructure."

↓ ClaimNormalizer Agent Processing ↓

Normalized Claim (simplified):
"Renewable energy can meet 100% of global energy needs by 2050"

Presuppositions Extracted:
1. "Current renewable technology is scalable to 100% coverage"
2. "Grid infrastructure can be upgraded sufficiently"
3. "Energy storage technology will advance adequately"

Conditional Dependencies:
1. "Governments implement aggressive carbon pricing" [CONDITION]
2. "Investment in grid infrastructure occurs" [CONDITION]

Atomic Sub-Claims:
1. "Renewable energy technology exists" [FACTUAL]
2. "Renewable energy can scale to 100% of demand" [EMPIRICAL]
3. "Timeline of 2050 is achievable" [PREDICTIVE]
4. "Global energy needs are definable/measurable" [DEFINITIONAL]

Key Terms Requiring Definition:
- "renewable energy" → What qualifies? (solar, wind, hydro, nuclear?)
- "100% of energy needs" → All sectors? (transport, heating, industry?)
- "by 2050" → Hard deadline or target date?
```

### Database Schema Extensions

```sql
-- ============================================================================
-- CLAIM NORMALIZATION TABLES
-- ============================================================================

CREATE TYPE claim_complexity AS ENUM (
    'atomic',        -- Cannot be decomposed further
    'simple',        -- Single assertion
    'compound',      -- Multiple sub-claims (AND/OR logic)
    'conditional',   -- If X then Y structure
    'comparative'    -- A vs B structure
);

CREATE TYPE presupposition_type AS ENUM (
    'existential',      -- Assumes something exists
    'definitional',     -- Assumes a definition
    'causal',          -- Assumes causal relationship
    'temporal',        -- Assumes time-based relationship
    'modal',           -- Assumes possibility/necessity
    'normative'        -- Assumes value judgment
);

-- Normalized claims (simplified versions)
CREATE TABLE normalized_claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    original_claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,

    -- Normalized form
    normalized_text TEXT NOT NULL,
    complexity claim_complexity NOT NULL,

    -- Logical structure
    logical_form TEXT,  -- Formal logic representation (optional)
    is_atomic BOOLEAN DEFAULT FALSE,

    -- Decomposition
    parent_normalized_id UUID REFERENCES normalized_claims(id) ON DELETE CASCADE,
    decomposition_level INT DEFAULT 0,  -- 0 = original, 1 = first decomp, etc.

    -- Analysis metadata
    analyzed_by_agent_id UUID REFERENCES agents(id),
    confidence_in_normalization DECIMAL(3,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT confidence_range CHECK (confidence_in_normalization BETWEEN 0.00 AND 1.00)
);

CREATE INDEX idx_normalized_original ON normalized_claims(original_claim_id);
CREATE INDEX idx_normalized_parent ON normalized_claims(parent_normalized_id) WHERE parent_normalized_id IS NOT NULL;
CREATE INDEX idx_normalized_atomic ON normalized_claims(is_atomic) WHERE is_atomic = TRUE;

-- Presuppositions (hidden assumptions in claims)
CREATE TABLE presuppositions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    normalized_claim_id UUID NOT NULL REFERENCES normalized_claims(id) ON DELETE CASCADE,

    presupposition_type presupposition_type NOT NULL,
    text TEXT NOT NULL,
    is_explicit BOOLEAN DEFAULT FALSE,  -- Stated vs implied

    -- This presupposition might itself be a claim to investigate
    spawned_claim_id UUID REFERENCES claims(id) ON DELETE SET NULL,

    -- Importance
    criticality DECIMAL(3,2),  -- How critical is this assumption? (0.0-1.0)

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT criticality_range CHECK (criticality BETWEEN 0.00 AND 1.00)
);

CREATE INDEX idx_presuppositions_claim ON presuppositions(normalized_claim_id);
CREATE INDEX idx_presuppositions_type ON presuppositions(presupposition_type);
CREATE INDEX idx_presuppositions_spawned ON presuppositions(spawned_claim_id) WHERE spawned_claim_id IS NOT NULL;

-- Key terms requiring definition
CREATE TABLE claim_terms (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    normalized_claim_id UUID NOT NULL REFERENCES normalized_claims(id) ON DELETE CASCADE,

    term TEXT NOT NULL,
    term_type VARCHAR(50),  -- 'concept', 'entity', 'method', 'metric'

    -- Definition tracking
    requires_definition BOOLEAN DEFAULT TRUE,
    working_definition TEXT,
    definition_source_id UUID REFERENCES evidence(id),

    -- Operationalization
    operational_definition TEXT,  -- How is this measured/tested?
    measurement_criteria TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_terms_claim ON claim_terms(normalized_claim_id);
CREATE INDEX idx_terms_undefined ON claim_terms(requires_definition) WHERE requires_definition = TRUE;

-- Conditional dependencies (if-then structures)
CREATE TABLE claim_conditions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,

    condition_type VARCHAR(50) NOT NULL,  -- 'necessary', 'sufficient', 'contributory'
    condition_text TEXT NOT NULL,

    -- This condition might be a separate claim
    condition_claim_id UUID REFERENCES claims(id) ON DELETE SET NULL,

    is_met BOOLEAN,  -- NULL = unknown, TRUE/FALSE = evaluated
    evaluated_by_investigation_id UUID REFERENCES investigations(id),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_conditions_claim ON claim_conditions(claim_id);
CREATE INDEX idx_conditions_condition_claim ON claim_conditions(condition_claim_id) WHERE condition_claim_id IS NOT NULL;

-- Claim decomposition tree (compound → atomic)
CREATE TABLE claim_decomposition (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    child_claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,

    decomposition_type VARCHAR(50) NOT NULL,  -- 'AND', 'OR', 'IF-THEN', 'SEQUENCE'
    position_index INT,  -- Order in logical structure

    is_critical BOOLEAN DEFAULT TRUE,  -- Must this sub-claim be true for parent to be true?

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT no_self_decomp CHECK (parent_claim_id != child_claim_id)
);

CREATE INDEX idx_decomp_parent ON claim_decomposition(parent_claim_id);
CREATE INDEX idx_decomp_child ON claim_decomposition(child_claim_id);

-- Claim hierarchy metadata (for organization and display)
CREATE TABLE claim_hierarchy (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE UNIQUE,

    -- Position in tree
    tree_depth INT DEFAULT 0,
    tree_path TEXT,  -- Materialized path: "1.2.3" for easy querying

    -- Structural metadata
    has_children BOOLEAN DEFAULT FALSE,
    child_count INT DEFAULT 0,
    descendant_count INT DEFAULT 0,  -- All descendants (recursive)

    -- Investigation routing
    primary_investigation_type VARCHAR(50),  -- Which agents should prioritize this?
    complexity_score DECIMAL(3,2),  -- How complex is this claim?

    -- Display metadata
    display_order INT,
    collapse_children BOOLEAN DEFAULT FALSE,  -- For UI

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT complexity_range CHECK (complexity_score BETWEEN 0.00 AND 1.00)
);

CREATE INDEX idx_hierarchy_claim ON claim_hierarchy(claim_id);
CREATE INDEX idx_hierarchy_path ON claim_hierarchy(tree_path);
CREATE INDEX idx_hierarchy_depth ON claim_hierarchy(tree_depth);

-- ============================================================================
-- PHILOSOPHY FRAMEWORK SYSTEM
-- ============================================================================

CREATE TYPE philosophy_category AS ENUM (
    'epistemological',   -- How we know things (empiricism, rationalism, etc.)
    'methodological',    -- How we investigate (scientific method, hermeneutics, etc.)
    'critical',          -- Critical theory, deconstruction, etc.
    'domain_specific',   -- Field-specific frameworks (deep learning, systems thinking, etc.)
    'ethical',          -- Ethical frameworks (utilitarian, deontological, etc.)
    'adversarial'       -- Devil's advocate, red team thinking, etc.
);

-- Philosophy frameworks that shape agent cognition
CREATE TABLE philosophy_frameworks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),

    -- Framework identity
    name VARCHAR(100) NOT NULL UNIQUE,
    category philosophy_category NOT NULL,

    -- Description
    description TEXT NOT NULL,
    core_principles JSONB,  -- [{principle: "...", description: "..."}]

    -- Prompting instructions for LLM
    system_prompt_prefix TEXT NOT NULL,  -- Prepended to agent system prompt
    thinking_guidelines TEXT[],  -- Array of thinking instructions

    -- Constraints and biases
    emphasizes TEXT[],  -- What to focus on
    de_emphasizes TEXT[],  -- What to downplay
    forbidden_assumptions TEXT[],  -- What not to assume

    -- Examples for few-shot learning
    example_analyses JSONB,  -- [{claim: "...", analysis: "...", reasoning: "..."}]

    -- Metadata
    created_by VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INT DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_frameworks_category ON philosophy_frameworks(category);
CREATE INDEX idx_frameworks_active ON philosophy_frameworks(is_active) WHERE is_active = TRUE;

-- Example philosophy frameworks (pre-populated)
INSERT INTO philosophy_frameworks (name, category, description, system_prompt_prefix, thinking_guidelines, emphasizes, de_emphasizes) VALUES

-- Epistemological Frameworks
('Empiricism', 'epistemological',
 'Knowledge comes from sensory experience and observable evidence',
 'You are an empiricist researcher. Prioritize observable, measurable evidence. Be skeptical of unfalsifiable claims.',
 ARRAY[
   'Demand concrete, observable evidence for all claims',
   'Prefer quantitative data over qualitative interpretation',
   'Look for replication studies and large sample sizes',
   'Question theoretical claims that lack empirical grounding'
 ],
 ARRAY['observable data', 'measurement', 'replication', 'falsifiability'],
 ARRAY['pure theory', 'speculation', 'unfalsifiable claims']),

('Rationalism', 'epistemological',
 'Knowledge comes from reason and logical deduction',
 'You are a rationalist analyst. Focus on logical coherence, theoretical consistency, and conceptual clarity.',
 ARRAY[
   'Examine logical structure and internal consistency',
   'Identify necessary vs contingent truths',
   'Evaluate theoretical frameworks and axioms',
   'Use deductive reasoning to test implications'
 ],
 ARRAY['logical consistency', 'theoretical coherence', 'conceptual analysis'],
 ARRAY['mere observation without theory', 'inductive generalizations']),

-- Critical Frameworks
('Critical Theory', 'critical',
 'Examine power structures, hidden assumptions, and whose interests are served',
 'You are a critical theorist. Question assumptions, examine power dynamics, and consider whose perspective is privileged.',
 ARRAY[
   'Ask: Who benefits from this claim being accepted as true?',
   'Identify hidden assumptions and naturalized beliefs',
   'Examine historical and social context',
   'Consider marginalized or excluded perspectives'
 ],
 ARRAY['power dynamics', 'hidden assumptions', 'social context', 'alternative perspectives'],
 ARRAY['taking claims at face value', 'ahistorical analysis']),

('Skeptical Inquiry', 'adversarial',
 'Actively seek to challenge and falsify claims',
 'You are a professional skeptic. Your job is to find weaknesses, alternative explanations, and reasons to doubt.',
 ARRAY[
   'Assume the claim is wrong and look for why',
   'Generate alternative explanations for the same evidence',
   'Identify methodological flaws and confounds',
   'Look for contradicting evidence',
   'Check for selective citation or cherry-picking'
 ],
 ARRAY['weaknesses', 'alternatives', 'methodological flaws', 'contradictions'],
 ARRAY['supporting evidence', 'confirmatory findings']),

-- Domain-Specific Frameworks
('Deep Learning Perspective', 'domain_specific',
 'Analyze through the lens of deep learning and neural network principles',
 'You are a deep learning researcher. Consider how neural networks, gradient descent, and representation learning apply to this domain.',
 ARRAY[
   'Look for hierarchical feature learning patterns',
   'Consider optimization landscapes and local minima',
   'Examine representation quality and transferability',
   'Identify data efficiency and sample complexity issues',
   'Consider inductive biases and architectural choices'
 ],
 ARRAY['hierarchical representations', 'optimization', 'generalization', 'scalability'],
 ARRAY['hand-crafted features', 'symbolic reasoning']),

('Systems Thinking', 'domain_specific',
 'Analyze as interconnected systems with feedback loops and emergent properties',
 'You are a systems thinker. Look for feedback loops, emergent properties, and system-level dynamics.',
 ARRAY[
   'Identify feedback loops (positive and negative)',
   'Look for emergent properties not predictable from components',
   'Map interdependencies and cascading effects',
   'Consider time delays and system inertia',
   'Examine boundary conditions and system limits'
 ],
 ARRAY['interconnections', 'feedback', 'emergence', 'complexity'],
 ARRAY['isolated variables', 'linear causation']),

-- Methodological Frameworks
('Bayesian Reasoning', 'methodological',
 'Update beliefs proportionally to evidence strength using Bayesian inference',
 'You are a Bayesian reasoner. Assess prior probabilities, likelihood ratios, and update beliefs incrementally.',
 ARRAY[
   'Start with prior probability based on existing evidence',
   'Calculate likelihood ratio for new evidence',
   'Update posterior probability using Bayes theorem',
   'Consider evidence strength, not just direction',
   'Be explicit about confidence intervals'
 ],
 ARRAY['prior probabilities', 'evidence strength', 'incremental updating', 'uncertainty quantification'],
 ARRAY['binary thinking', 'ignoring base rates']),

('Interdisciplinary Synthesis', 'methodological',
 'Integrate insights from multiple fields and methodologies',
 'You are an interdisciplinary synthesizer. Draw connections across fields and integrate diverse perspectives.',
 ARRAY[
   'Look for analogous phenomena in other disciplines',
   'Integrate quantitative and qualitative evidence',
   'Use metaphors and models from different fields',
   'Identify complementary methodological approaches',
   'Synthesize apparently contradictory findings'
 ],
 ARRAY['cross-domain connections', 'methodological pluralism', 'synthesis'],
 ARRAY['disciplinary silos', 'single-method approaches']);

-- Agent philosophy assignments (which frameworks each agent uses)
CREATE TABLE agent_philosophy_assignments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_id UUID NOT NULL REFERENCES agents(id) ON DELETE CASCADE,
    philosophy_id UUID NOT NULL REFERENCES philosophy_frameworks(id) ON DELETE CASCADE,

    -- Configuration
    is_primary BOOLEAN DEFAULT TRUE,  -- Primary vs secondary framework
    weight DECIMAL(3,2) DEFAULT 1.0,  -- How strongly to apply (0.0-1.0)

    -- Context-specific activation
    active_for_claim_types claim_type[],  -- Only apply for these claim types
    active_for_domains TEXT[],  -- Only apply for these subject domains

    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT weight_range CHECK (weight BETWEEN 0.00 AND 1.00),
    CONSTRAINT unique_agent_philosophy UNIQUE (agent_id, philosophy_id)
);

CREATE INDEX idx_agent_philosophy_agent ON agent_philosophy_assignments(agent_id);
CREATE INDEX idx_agent_philosophy_philosophy ON agent_philosophy_assignments(philosophy_id);

-- Investigation philosophy context (applied at runtime)
CREATE TABLE investigation_philosophy_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,

    -- Active philosophies for this investigation
    philosophy_ids UUID[],  -- Array of framework IDs

    -- Combined prompt
    effective_system_prompt TEXT,  -- Merged system prompt with all frameworks
    active_guidelines TEXT[],  -- Combined thinking guidelines

    -- Reasoning trace
    reasoning_framework_used VARCHAR(100),  -- Which framework dominated reasoning

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_investigation_philosophy ON investigation_philosophy_context(investigation_id);

-- ============================================================================
-- INVESTIGATION TREE VISUALIZATION DATA
-- ============================================================================

-- Pre-computed tree structure for efficient report generation
CREATE TABLE investigation_trees (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    root_claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,

    -- Tree metadata
    total_nodes INT DEFAULT 0,
    max_depth INT DEFAULT 0,
    total_investigations INT DEFAULT 0,
    total_evidence_items INT DEFAULT 0,

    -- Tree structure (JSON for visualization)
    tree_json JSONB,  -- Full tree structure for rendering
    /*
    Example structure:
    {
      "id": "claim-uuid",
      "text": "Original claim",
      "normalized": "Simplified claim",
      "status": "verified",
      "confidence": 0.85,
      "children": [
        {
          "id": "presupposition-uuid",
          "type": "presupposition",
          "text": "Assumption 1",
          "status": "challenged",
          "children": [...]
        },
        {
          "id": "subclaim-uuid",
          "type": "decomposed_claim",
          "text": "Sub-claim 1",
          "status": "supported",
          "evidence_count": 5,
          "children": [...]
        }
      ],
      "evidence_summary": {
        "support": 12,
        "challenge": 3,
        "neutral": 2
      }
    }
    */

    -- Rendering metadata
    layout_algorithm VARCHAR(50) DEFAULT 'hierarchical',  -- 'hierarchical', 'radial', 'tree'
    visual_complexity_score DECIMAL(3,2),

    -- Cache management
    is_stale BOOLEAN DEFAULT FALSE,
    last_computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_trees_root ON investigation_trees(root_claim_id);
CREATE INDEX idx_trees_stale ON investigation_trees(is_stale) WHERE is_stale = TRUE;

-- Trigger to mark tree as stale when related data changes
CREATE OR REPLACE FUNCTION mark_tree_stale()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE investigation_trees
    SET is_stale = TRUE
    WHERE root_claim_id IN (
        SELECT root_claim_id FROM claims WHERE id = NEW.claim_id
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_mark_tree_stale_on_finding
AFTER INSERT ON findings
FOR EACH ROW
EXECUTE FUNCTION mark_tree_stale();

-- ============================================================================
-- UPDATED VIEWS FOR WORK DISCOVERY
-- ============================================================================

-- Claims needing normalization
CREATE VIEW claims_needing_normalization AS
SELECT c.*
FROM claims c
LEFT JOIN normalized_claims nc ON c.id = nc.original_claim_id
WHERE nc.id IS NULL
  AND c.status NOT IN ('archived')
ORDER BY c.priority_score DESC;

-- Presuppositions that should become claims
CREATE VIEW presuppositions_to_investigate AS
SELECT
    p.*,
    c.text as parent_claim_text,
    c.priority_score as parent_priority
FROM presuppositions p
JOIN normalized_claims nc ON p.normalized_claim_id = nc.id
JOIN claims c ON nc.original_claim_id = c.id
WHERE p.spawned_claim_id IS NULL  -- Not yet turned into a claim
  AND p.criticality > 0.7  -- High importance
ORDER BY p.criticality DESC, parent_priority DESC;

-- Terms needing definition
CREATE VIEW undefined_terms AS
SELECT
    ct.*,
    c.text as claim_text,
    COUNT(*) OVER (PARTITION BY ct.term) as term_frequency
FROM claim_terms ct
JOIN normalized_claims nc ON ct.normalized_claim_id = nc.id
JOIN claims c ON nc.original_claim_id = c.id
WHERE ct.requires_definition = TRUE
  AND ct.working_definition IS NULL
ORDER BY term_frequency DESC;

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Materialize investigation tree for a claim
CREATE OR REPLACE FUNCTION build_investigation_tree(p_root_claim_id UUID)
RETURNS JSONB AS $$
DECLARE
    tree_json JSONB;
BEGIN
    WITH RECURSIVE claim_tree AS (
        -- Base case: root claim
        SELECT
            c.id,
            c.text,
            nc.normalized_text,
            c.status,
            c.confidence_score,
            c.parent_claim_id,
            0 as depth,
            ARRAY[c.id] as path
        FROM claims c
        LEFT JOIN normalized_claims nc ON c.id = nc.original_claim_id
        WHERE c.id = p_root_claim_id

        UNION ALL

        -- Recursive case: child claims
        SELECT
            c.id,
            c.text,
            nc.normalized_text,
            c.status,
            c.confidence_score,
            c.parent_claim_id,
            ct.depth + 1,
            ct.path || c.id
        FROM claims c
        LEFT JOIN normalized_claims nc ON c.id = nc.original_claim_id
        JOIN claim_tree ct ON c.parent_claim_id = ct.id
        WHERE c.id != ALL(ct.path)  -- Prevent cycles
          AND ct.depth < 10  -- Max depth
    )
    SELECT jsonb_agg(
        jsonb_build_object(
            'id', id,
            'text', text,
            'normalized', normalized_text,
            'status', status,
            'confidence', confidence_score,
            'depth', depth,
            'evidence', (
                SELECT jsonb_build_object(
                    'support', COUNT(*) FILTER (WHERE f.finding_type = 'support'),
                    'challenge', COUNT(*) FILTER (WHERE f.finding_type = 'challenge'),
                    'neutral', COUNT(*) FILTER (WHERE f.finding_type IN ('neutral', 'clarification'))
                )
                FROM findings f
                WHERE f.claim_id = claim_tree.id
            )
        )
    ) INTO tree_json
    FROM claim_tree;

    RETURN tree_json;
END;
$$ LANGUAGE plpgsql;

-- Auto-update tree when investigations complete
CREATE OR REPLACE FUNCTION refresh_investigation_tree()
RETURNS TRIGGER AS $$
DECLARE
    root_id UUID;
BEGIN
    -- Find root claim
    SELECT root_claim_id INTO root_id
    FROM claims
    WHERE id = NEW.claim_id;

    -- Update or create tree
    INSERT INTO investigation_trees (root_claim_id, tree_json, last_computed_at)
    VALUES (root_id, build_investigation_tree(root_id), CURRENT_TIMESTAMP)
    ON CONFLICT (root_claim_id) DO UPDATE
    SET
        tree_json = build_investigation_tree(root_id),
        last_computed_at = CURRENT_TIMESTAMP,
        is_stale = FALSE;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_refresh_tree
AFTER UPDATE ON investigations
FOR EACH ROW
WHEN (NEW.status = 'completed' AND OLD.status != 'completed')
EXECUTE FUNCTION refresh_investigation_tree();
```

## Part 2: ClaimNormalizer Agent Implementation

```python
# agents/claim_normalizer.py

from typing import Dict, List, Optional
from uuid import UUID
import asyncio

class ClaimNormalizerAgent(BaseAgent):
    """
    Specialized agent that:
    1. Simplifies claims to core form
    2. Decomposes compound claims into atomic parts
    3. Extracts presuppositions and hidden assumptions
    4. Identifies key terms needing definition
    5. Maps claim hierarchy for investigation routing
    """

    def __init__(self, db_connection, ai_provider):
        super().__init__(AgentFramework.CLAIM_NORMALIZER, db_connection)
        self.ai = ai_provider

        # ClaimNormalizer always uses specific philosophy
        self.philosophy = self.load_philosophy_framework('Logical Analysis')

    async def investigate(self, claim_data: dict) -> dict:
        """
        Normalize a claim and extract its structure.
        """
        claim_id = claim_data['id']
        claim_text = claim_data['text']

        # Step 1: Simplify claim to core form
        normalized_text = await self.simplify_claim(claim_text)

        # Step 2: Determine complexity
        complexity = await self.assess_complexity(claim_text, normalized_text)

        # Step 3: Extract presuppositions
        presuppositions = await self.extract_presuppositions(claim_text, normalized_text)

        # Step 4: Decompose if compound
        sub_claims = []
        if complexity in ['compound', 'conditional']:
            sub_claims = await self.decompose_claim(normalized_text, complexity)

        # Step 5: Identify key terms
        key_terms = await self.identify_terms(normalized_text)

        # Step 6: Extract conditions (if-then structure)
        conditions = await self.extract_conditions(claim_text)

        return {
            'claim_id': claim_id,
            'type': 'normalization',
            'summary': f'Normalized claim and extracted {len(presuppositions)} presuppositions, {len(sub_claims)} sub-claims',
            'analysis': self.generate_normalization_report(
                claim_text, normalized_text, complexity,
                presuppositions, sub_claims, key_terms, conditions
            ),
            'confidence': 0.9,
            'normalized_data': {
                'normalized_text': normalized_text,
                'complexity': complexity,
                'presuppositions': presuppositions,
                'sub_claims': sub_claims,
                'key_terms': key_terms,
                'conditions': conditions
            },
            'new_claims': sub_claims,  # Sub-claims become new claims to investigate
            'evidence': []  # Normalization doesn't produce evidence
        }

    async def simplify_claim(self, claim_text: str) -> str:
        """Use LLM to simplify claim to essential form"""
        prompt = f"""Simplify this claim to its core assertion, removing:
- Unnecessary qualifiers
- Rhetorical flourishes
- Redundant phrases
- Conditional clauses (extract them separately)

But preserve:
- The core factual assertion
- Key quantifiers (all, some, most, etc.)
- Critical relationships (causes, correlates, etc.)

Original claim: "{claim_text}"

Simplified claim:"""

        response = await self.ai.generate(prompt, temperature=0.1)
        return response.strip()

    async def extract_presuppositions(self, claim_text: str, normalized_text: str) -> List[Dict]:
        """Extract hidden assumptions"""
        prompt = f"""Identify all presuppositions and assumptions in this claim.

A presupposition is something that must be true for the claim to make sense.

Original: "{claim_text}"
Simplified: "{normalized_text}"

List each presupposition with:
1. The assumption text
2. Type: existential, definitional, causal, temporal, modal, or normative
3. Is it explicit (stated) or implicit (hidden)?
4. Criticality: how important is this assumption? (0.0-1.0)

Format as JSON array:
[
  {{
    "text": "assumption text",
    "type": "existential",
    "is_explicit": false,
    "criticality": 0.8,
    "explanation": "why this is presupposed"
  }}
]"""

        response = await self.ai.generate(prompt, temperature=0.2, response_format='json')
        return json.loads(response)

    async def decompose_claim(self, normalized_text: str, complexity: str) -> List[str]:
        """Break compound claim into atomic sub-claims"""
        prompt = f"""This is a {complexity} claim. Decompose it into atomic sub-claims.

Claim: "{normalized_text}"

Rules:
- Each sub-claim should be independently verifiable
- Preserve logical structure (AND, OR, IF-THEN)
- Make implicit conjunctions explicit

Return JSON:
{{
  "decomposition_type": "AND" | "OR" | "IF-THEN" | "SEQUENCE",
  "sub_claims": [
    {{"text": "sub-claim 1", "is_critical": true}},
    {{"text": "sub-claim 2", "is_critical": true}}
  ]
}}"""

        response = await self.ai.generate(prompt, temperature=0.1, response_format='json')
        data = json.loads(response)
        return [sc['text'] for sc in data['sub_claims']]

    async def identify_terms(self, normalized_text: str) -> List[Dict]:
        """Identify terms that need definition"""
        prompt = f"""Identify key terms in this claim that require clear definition:

Claim: "{normalized_text}"

For each term, specify:
- The term
- Why it needs definition (ambiguous? technical? contested?)
- Suggested operational definition (how to measure/test it)

Return JSON array:
[
  {{
    "term": "renewable energy",
    "term_type": "concept",
    "why_definition_needed": "Multiple technologies could qualify",
    "operational_definition": "Energy from sources that regenerate: solar, wind, hydro, geothermal"
  }}
]"""

        response = await self.ai.generate(prompt, temperature=0.3, response_format='json')
        return json.loads(response)

    async def extract_conditions(self, claim_text: str) -> List[Dict]:
        """Extract if-then conditions"""
        prompt = f"""Identify conditional structures in this claim:

Claim: "{claim_text}"

Look for:
- Necessary conditions (must have for claim to be true)
- Sufficient conditions (enough by itself to make claim true)
- Contributory conditions (helps but not enough alone)

Return JSON:
[
  {{
    "condition_text": "if governments implement carbon pricing",
    "condition_type": "necessary",
    "is_testable": true
  }}
]"""

        response = await self.ai.generate(prompt, temperature=0.2, response_format='json')
        return json.loads(response)

    async def save_findings(self, investigation_id: UUID, findings: dict):
        """Save normalization results to database"""
        norm_data = findings['normalized_data']

        # Insert normalized claim
        norm_id = await self.db.execute("""
            INSERT INTO normalized_claims (
                original_claim_id,
                normalized_text,
                complexity,
                is_atomic,
                analyzed_by_agent_id,
                confidence_in_normalization
            ) VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            findings['claim_id'],
            norm_data['normalized_text'],
            norm_data['complexity'],
            norm_data['complexity'] == 'atomic',
            self.agent_id,
            findings['confidence']
        ))

        # Insert presuppositions
        for presup in norm_data['presuppositions']:
            await self.db.execute("""
                INSERT INTO presuppositions (
                    normalized_claim_id,
                    presupposition_type,
                    text,
                    is_explicit,
                    criticality
                ) VALUES (%s, %s, %s, %s, %s)
            """, (
                norm_id,
                presup['type'],
                presup['text'],
                presup['is_explicit'],
                presup['criticality']
            ))

        # Insert key terms
        for term in norm_data['key_terms']:
            await self.db.execute("""
                INSERT INTO claim_terms (
                    normalized_claim_id,
                    term,
                    term_type,
                    requires_definition,
                    operational_definition
                ) VALUES (%s, %s, %s, TRUE, %s)
            """, (
                norm_id,
                term['term'],
                term['term_type'],
                term['operational_definition']
            ))

        # Insert conditions
        for cond in norm_data['conditions']:
            await self.db.execute("""
                INSERT INTO claim_conditions (
                    claim_id,
                    condition_type,
                    condition_text
                ) VALUES (%s, %s, %s)
            """, (
                findings['claim_id'],
                cond['condition_type'],
                cond['condition_text']
            ))

        # Standard finding record
        await super().save_findings(investigation_id, findings)
```

## Part 3: Philosophy Framework System

```python
# agents/philosophy_enhanced_agent.py

class PhilosophyEnhancedAgent(BaseAgent):
    """
    Base class for agents that use configurable philosophy frameworks.
    """

    def __init__(self, framework: AgentFramework, db_connection, philosophy_ids: List[UUID] = None):
        super().__init__(framework, db_connection)
        self.philosophies = self.load_philosophies(philosophy_ids or [])

    def load_philosophies(self, philosophy_ids: List[UUID]) -> List[Dict]:
        """Load philosophy frameworks from database"""
        if not philosophy_ids:
            # Use defaults for this agent framework
            return self.get_default_philosophies()

        philosophies = self.db.execute("""
            SELECT * FROM philosophy_frameworks
            WHERE id = ANY(%s) AND is_active = TRUE
        """, (philosophy_ids,))

        return philosophies

    def get_default_philosophies(self) -> List[Dict]:
        """Override in subclasses to set framework-specific defaults"""
        return []

    def build_enhanced_system_prompt(self, base_prompt: str) -> str:
        """Merge base prompt with philosophy framework prompts"""
        philosophy_prompts = [
            p['system_prompt_prefix'] for p in self.philosophies
        ]

        combined = base_prompt + "\n\n"
        combined += "PHILOSOPHICAL FRAMEWORKS:\n"
        combined += "\n".join(philosophy_prompts)
        combined += "\n\nAPPLY THESE PERSPECTIVES IN YOUR ANALYSIS."

        return combined

    def get_thinking_guidelines(self) -> List[str]:
        """Get combined thinking guidelines from all active philosophies"""
        all_guidelines = []
        for phil in self.philosophies:
            all_guidelines.extend(phil['thinking_guidelines'])
        return all_guidelines

    async def investigate(self, claim_data: dict) -> dict:
        """
        Philosophy-enhanced investigation.
        Subclasses still override, but use enhanced prompt.
        """
        # Build enhanced prompt
        base_prompt = self.get_base_investigation_prompt(claim_data)
        enhanced_prompt = self.build_enhanced_system_prompt(base_prompt)

        # Add thinking guidelines
        guidelines = self.get_thinking_guidelines()
        enhanced_prompt += "\n\nTHINKING GUIDELINES:\n"
        enhanced_prompt += "\n".join(f"- {g}" for g in guidelines)

        # Record which philosophies are active
        await self.record_philosophy_context(claim_data['investigation_id'])

        # Do investigation with enhanced context
        return await self.do_philosophy_enhanced_investigation(
            claim_data,
            enhanced_prompt
        )

    async def record_philosophy_context(self, investigation_id: UUID):
        """Record which philosophies were used"""
        philosophy_ids = [p['id'] for p in self.philosophies]

        await self.db.execute("""
            INSERT INTO investigation_philosophy_context (
                investigation_id,
                philosophy_ids,
                effective_system_prompt,
                active_guidelines
            ) VALUES (%s, %s, %s, %s)
        """, (
            investigation_id,
            philosophy_ids,
            self.build_enhanced_system_prompt(""),
            self.get_thinking_guidelines()
        ))

# Example: Support agent with Deep Learning philosophy
class SupportAgent_DeepLearning(PhilosophyEnhancedAgent):
    def get_default_philosophies(self) -> List[Dict]:
        # Load "Deep Learning Perspective" framework
        return self.db.execute("""
            SELECT * FROM philosophy_frameworks
            WHERE name = 'Deep Learning Perspective'
        """)

    async def do_philosophy_enhanced_investigation(self, claim_data: dict, enhanced_prompt: str) -> dict:
        claim_text = claim_data['text']

        # This prompt is enhanced with deep learning perspective
        prompt = enhanced_prompt + f"""

CLAIM TO INVESTIGATE:
"{claim_text}"

YOUR TASK:
Search for evidence that SUPPORTS this claim, but analyze it through the lens of deep learning principles:
- How do hierarchical representations apply?
- What optimization challenges exist?
- Are there data efficiency concerns?
- What inductive biases are relevant?

Provide evidence with APA citations.
"""

        response = await self.ai.generate(prompt, temperature=0.6)
        # ... rest of investigation logic
```

## Part 4: Report Generation with Tree Visualization

```python
# reports/tree_visualizer.py

class InvestigationTreeVisualizer:
    """
    Generates elegant visual representations of investigation trees
    for inclusion in Word documents and other reports.
    """

    def __init__(self, db_connection):
        self.db = db_connection

    async def generate_tree_for_claim(self, claim_id: UUID) -> Dict:
        """Get or build investigation tree"""
        # Check if tree exists and is fresh
        tree = await self.db.execute("""
            SELECT * FROM investigation_trees
            WHERE root_claim_id = %s
            AND is_stale = FALSE
        """, (claim_id,))

        if tree:
            return tree[0]['tree_json']

        # Build fresh tree
        tree_json = await self.db.execute("""
            SELECT build_investigation_tree(%s)
        """, (claim_id,))

        return tree_json[0]['build_investigation_tree']

    def render_tree_ascii(self, tree_json: dict, max_depth: int = 5) -> str:
        """
        Render tree as ASCII art for terminal/markdown display

        Example output:

        ┌─ Original Claim [VERIFIED: 0.85]
        │  "Renewable energy can meet 100% of needs by 2050"
        │
        ├─┬─ Presupposition [CHALLENGED: 0.45]
        │ │  "Technology is scalable to 100%"
        │ │
        │ ├─── Evidence (3 support, 5 challenge)
        │ │    → Jacobson et al. (2017) [Support]
        │ │    → Clack et al. (2017) [Challenge]
        │ │
        │ └─┬─ Counter-claim [INVESTIGATING]
        │   │  "Scalability faces material constraints"
        │   └─── Evidence (2 support)
        │
        ├─┬─ Sub-claim [SUPPORTED: 0.78]
        │ │  "Solar and wind costs continue declining"
        │ └─── Evidence (8 support, 1 challenge)
        │
        └─┬─ Condition [NOT MET: 0.30]
          │  "IF carbon pricing implemented"
          └─── Evidence (mixed results)
        """
        lines = []
        self._render_node(tree_json, lines, prefix="", is_last=True, depth=0, max_depth=max_depth)
        return "\n".join(lines)

    def _render_node(self, node: dict, lines: list, prefix: str, is_last: bool, depth: int, max_depth: int):
        if depth > max_depth:
            return

        # Node connector
        connector = "└─" if is_last else "├─"

        # Node status badge
        status = node.get('status', 'unknown').upper()
        confidence = node.get('confidence', 0.0)
        badge = f"[{status}: {confidence:.2f}]" if confidence else f"[{status}]"

        # Main node line
        node_type = node.get('type', 'claim')
        lines.append(f"{prefix}{connector}┬─ {node_type.title()} {badge}")

        # Node text (wrapped)
        text = node.get('text', node.get('normalized', ''))
        lines.append(f"{prefix}{'  ' if is_last else '│ '}│  \"{text}\"")
        lines.append(f"{prefix}{'  ' if is_last else '│ '}│")

        # Evidence summary
        evidence = node.get('evidence_summary', {})
        if any(evidence.values()):
            lines.append(
                f"{prefix}{'  ' if is_last else '│ '}├─── Evidence "
                f"({evidence.get('support', 0)} support, "
                f"{evidence.get('challenge', 0)} challenge, "
                f"{evidence.get('neutral', 0)} neutral)"
            )

        # Children
        children = node.get('children', [])
        if children:
            new_prefix = prefix + ("  " if is_last else "│ ")
            for i, child in enumerate(children):
                is_last_child = (i == len(children) - 1)
                self._render_node(child, lines, new_prefix, is_last_child, depth + 1, max_depth)

    def render_tree_mermaid(self, tree_json: dict) -> str:
        """
        Render tree as Mermaid diagram (for GitHub markdown, Obsidian, etc.)

        Example output:
        ```mermaid
        graph TD
          A[Original Claim<br/>VERIFIED 0.85] --> B[Presupposition<br/>CHALLENGED 0.45]
          A --> C[Sub-claim<br/>SUPPORTED 0.78]
          B --> D[Counter-claim<br/>INVESTIGATING]
          C --> E[Evidence: 8 support]
        ```
        """
        lines = ["graph TD"]
        node_id = 0

        def add_node(node, parent_id=None):
            nonlocal node_id
            current_id = f"N{node_id}"
            node_id += 1

            # Node label
            status = node.get('status', '').upper()
            confidence = node.get('confidence', 0.0)
            text = node.get('text', '')[:50]  # Truncate
            label = f"{text}<br/>{status} {confidence:.2f}"

            # Style by status
            style_class = {
                'VERIFIED': 'fill:#90EE90',
                'SUPPORTED': '#B0E0E6',
                'CHALLENGED': '#FFB6C1',
                'REFUTED': '#FFA07A',
                'INVESTIGATING': '#FFD700'
            }.get(status, '#D3D3D3')

            lines.append(f"  {current_id}[\"{label}\"]")
            lines.append(f"  style {current_id} {style_class}")

            if parent_id:
                edge_label = node.get('type', '')
                lines.append(f"  {parent_id} -->|{edge_label}| {current_id}")

            # Recurse
            for child in node.get('children', []):
                add_node(child, current_id)

        add_node(tree_json)
        return "\n".join(lines)

    async def generate_word_document(self, claim_id: UUID, output_path: str):
        """
        Generate comprehensive Word document with investigation tree.

        Includes:
        - Executive summary
        - Visual tree diagram
        - Detailed findings for each node
        - Full evidence list with APA citations
        - Methodology appendix
        """
        from docx import Document
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        doc = Document()

        # Title
        title = doc.add_heading('Investigation Report', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER

        # Get tree data
        tree = await self.generate_tree_for_claim(claim_id)
        claim_text = tree['text']

        # Executive Summary
        doc.add_heading('Executive Summary', 1)
        doc.add_paragraph(f'Original Claim: "{claim_text}"')
        doc.add_paragraph(f'Status: {tree["status"].title()}')
        doc.add_paragraph(f'Confidence: {tree.get("confidence", 0.0):.2%}')

        evidence_summary = tree.get('evidence_summary', {})
        doc.add_paragraph(
            f'Evidence: {evidence_summary.get("support", 0)} supporting, '
            f'{evidence_summary.get("challenge", 0)} challenging, '
            f'{evidence_summary.get("neutral", 0)} neutral'
        )

        # ASCII tree visualization
        doc.add_page_break()
        doc.add_heading('Investigation Tree', 1)
        tree_ascii = self.render_tree_ascii(tree, max_depth=4)
        p = doc.add_paragraph(tree_ascii)
        p.style = 'Normal'
        # Monospace font for ASCII art
        for run in p.runs:
            run.font.name = 'Courier New'
            run.font.size = Pt(9)

        # Detailed findings
        doc.add_page_break()
        doc.add_heading('Detailed Findings', 1)
        await self._add_detailed_findings(doc, claim_id)

        # Evidence bibliography
        doc.add_page_break()
        doc.add_heading('Evidence Bibliography', 1)
        await self._add_evidence_bibliography(doc, claim_id)

        # Methodology
        doc.add_page_break()
        doc.add_heading('Methodology', 1)
        await self._add_methodology_section(doc, claim_id)

        # Save
        doc.save(output_path)
        return output_path

    async def _add_detailed_findings(self, doc, claim_id: UUID):
        """Add detailed findings for each investigation"""
        findings = await self.db.execute("""
            SELECT
                f.*,
                c.text as claim_text,
                i.agent_framework,
                pf.name as philosophy_name
            FROM findings f
            JOIN claims c ON f.claim_id = c.id
            JOIN investigations i ON f.investigation_id = i.id
            LEFT JOIN investigation_philosophy_context ipc ON i.id = ipc.investigation_id
            LEFT JOIN philosophy_frameworks pf ON pf.id = ANY(ipc.philosophy_ids)
            WHERE c.id = %s OR c.root_claim_id = %s
            ORDER BY f.created_at
        """, (claim_id, claim_id))

        for finding in findings:
            doc.add_heading(f"{finding['claim_text'][:60]}...", 2)
            doc.add_paragraph(f"Agent: {finding['agent_framework']}")
            if finding['philosophy_name']:
                doc.add_paragraph(f"Philosophy: {finding['philosophy_name']}")
            doc.add_paragraph(f"Type: {finding['finding_type'].title()}")
            doc.add_paragraph(finding['summary'])
            if finding['detailed_analysis']:
                doc.add_paragraph(finding['detailed_analysis'])
            doc.add_paragraph()  # Spacing

    async def _add_evidence_bibliography(self, doc, claim_id: UUID):
        """Add full APA bibliography"""
        evidence = await self.db.execute("""
            SELECT DISTINCT e.*
            FROM evidence e
            JOIN findings f ON e.finding_id = f.id
            JOIN claims c ON f.claim_id = c.id
            WHERE c.id = %s OR c.root_claim_id = %s
            ORDER BY e.citation_apa
        """, (claim_id, claim_id))

        for i, ev in enumerate(evidence, 1):
            p = doc.add_paragraph(f"{i}. {ev['citation_apa']}")
            p.style = 'List Number'

            if ev['relevant_quote']:
                doc.add_paragraph(f'  "{ev["relevant_quote"]}"', style='Quote')

    async def _add_methodology_section(self, doc, claim_id: UUID):
        """Explain how investigation was conducted"""
        doc.add_paragraph(
            "This investigation was conducted using an autonomous multi-agent system "
            "with the following frameworks:"
        )

        frameworks_used = await self.db.execute("""
            SELECT DISTINCT
                i.agent_framework,
                pf.name as philosophy,
                pf.description
            FROM investigations i
            JOIN claims c ON i.claim_id = c.id
            LEFT JOIN investigation_philosophy_context ipc ON i.id = ipc.investigation_id
            LEFT JOIN philosophy_frameworks pf ON pf.id = ANY(ipc.philosophy_ids)
            WHERE c.id = %s OR c.root_claim_id = %s
        """, (claim_id, claim_id))

        for fw in frameworks_used:
            doc.add_paragraph(
                f"• {fw['agent_framework']}: {fw['philosophy']} - {fw['description']}",
                style='List Bullet'
            )
```

## CLI Commands (Updated)

```bash
# Normalize all claims in a document
python research_agent.py normalize --doc-id 123

# Launch agents with specific philosophy
python research_agent.py launch-agents --framework support_empirical \
  --philosophy "Deep Learning Perspective" --count 3

# Launch adversarial agents with skeptical framework
python research_agent.py launch-agents --framework challenge_empirical \
  --philosophy "Skeptical Inquiry" --count 2

# View claim normalization
python research_agent.py show-normalized --claim-id abc-123
# Output:
# Original: "Renewable energy can meet 100% of needs by 2050 if..."
# Normalized: "Renewable energy can meet 100% of global energy needs by 2050"
# Complexity: conditional
# Presuppositions (3):
#   1. [existential] Technology scalability assumption (criticality: 0.85)
#   2. [temporal] Grid infrastructure advancement (criticality: 0.75)
#   ...
# Sub-claims (2):
#   1. "Renewable energy technology exists and is deployable"
#   2. "Energy storage can support 100% renewable grid"

# Generate investigation report with tree
python research_agent.py generate-report --claim-id abc-123 \
  --format docx --include-tree --output report.docx

# View tree in terminal
python research_agent.py show-tree --claim-id abc-123 --depth 5
# Shows ASCII art tree

# Export tree as Mermaid diagram
python research_agent.py export-tree --claim-id abc-123 --format mermaid
```

This extension adds:

1. ✅ **ClaimNormalizer agent** - simplifies, decomposes, extracts presuppositions
2. ✅ **Philosophy framework system** - configurable agent cognition
3. ✅ **Investigation tree visualization** - elegant display for reports
4. ✅ **Presupposition tracking** - identifies hidden assumptions
5. ✅ **Term definition management** - tracks concepts needing clarification
6. ✅ **Hierarchical claim organization** - proper tree structure
7. ✅ **Word document generation** - comprehensive formatted reports

Ready to proceed with implementation?