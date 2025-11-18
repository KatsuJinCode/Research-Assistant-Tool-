# ClaimNormalizer: Research-Backed Design

## Ground Truth Principles

**CRITICAL**: We must NEVER change the claim's meaning when normalizing. All downstream investigation depends on accurate claim representation. A mist

ated claim makes all subsequent work worthless.

### Core Requirements

1. **Semantic Equivalence**: Normalized claim must be 100% semantically equivalent to original
2. **Context Preservation**: Full situational, rhetorical, and discourse context must be maintained
3. **Human Validation**: User must be able to verify and refine normalization
4. **Iterative Refinement**: System must learn from user corrections
5. **Audit Trail**: Complete history of normalization decisions and user feedback

## Research Foundations

### 1. Argument Mining (MIT Computational Linguistics 2019)

**Key Findings**:
- Argument mining extracts structure of inference and reasoning from natural language
- Core tasks: identifying argumentative components (claims, premises) and relationships (support, attack)
- Scientific papers require special handling: argumentative zoning, claim extraction, evidence linking

**Application to Our System**:
```
Scientific Paper → Argument Mining
├── Identify argumentative zones (introduction, methods, results, discussion)
├── Extract claims with rhetorical role labels
├── Link claims to supporting evidence/data
└── Preserve discourse context (e.g., "We argue that..." vs "Previous work claims...")
```

### 2. Toulmin Model of Argumentation

**Six Components** (Essential for claim structure):

```
Claim: The main assertion
  ↓
Grounds: Evidence/data supporting the claim
  ↓
Warrant: Logical connection between grounds and claim (often implicit)
  ↓
Backing: Support for the warrant
  ↓
Qualifier: Degree of certainty ("usually", "sometimes", "always")
  ↓
Rebuttal: Exceptions or counter-arguments
```

**Application**:
- Each claim is decomposed into Toulmin components
- Qualifiers are preserved (critical for accuracy!)
- Rebuttals become counter-claims
- Warrants (often implicit) are made explicit

**Example**:
```
Original: "Renewable energy can meet 100% of needs by 2050 if carbon pricing is implemented"

Toulmin Decomposition:
├── Claim: "Renewable energy can meet 100% of global energy needs by 2050"
├── Grounds: [To be found by evidence agents]
├── Warrant: (IMPLICIT) "Policy interventions can drive technology adoption"
├── Backing: [To be found]
├── Qualifier: "can" (not "will") - indicates possibility, not certainty
└── Rebuttal: (IMPLICIT) "unless economic/political barriers prevent it"
```

### 3. Semantic Role Labeling (SRL)

**What SRL Provides**:
- Identifies "who did what to whom" - predicate-argument structure
- Preserves semantic relationships across transformations
- Captures long-range dependencies
- Enables accurate paraphrasing while preserving meaning

**SRL Tags** (PropBank/FrameNet):
- **ARG0**: Agent (who performs action)
- **ARG1**: Patient (what is acted upon)
- **ARG2**: Instrument, benefactive, or end state
- **ARG3**: Starting point, source
- **ARG4**: Ending point, destination
- **ARGM**: Modifiers (time, location, manner, purpose)

**Example**:
```
Original Claim: "Deep learning models outperformed traditional methods on ImageNet by 15% in 2012"

SRL Analysis:
[ARG0 Deep learning models] [PREDICATE outperformed] [ARG1 traditional methods]
[ARGM-LOC on ImageNet] [ARGM-EXT by 15%] [ARGM-TMP in 2012]

Preserved Structure:
- Agent: Deep learning models (what)
- Action: outperformed (predicate)
- Patient: traditional methods (what was surpassed)
- Location: on ImageNet (context - specific dataset)
- Extent: by 15% (quantifier - must preserve!)
- Time: in 2012 (temporal context - critical!)

Normalized: "Deep learning models outperformed traditional methods on ImageNet by 15% in 2012"
(In this case, claim is already atomic - no simplification needed, but SRL confirms all semantic roles)
```

### 4. Context-Aware Paraphrase Generation

**Research Findings**:
- Quality measured by **semantic preservation** - meaning similarity to original
- **Syntax attention mechanisms** help preserve key information
- **Topic-aware models** incorporate domain context
- **Evaluation**: Semantic similarity measures + human judgment

**Application**:
- Use LLM with explicit semantic preservation instructions
- Preserve named entities, quantifiers, temporal markers
- Maintain syntactic structure where possible
- Generate multiple candidates and rank by semantic similarity
- **Human validation required** before accepting normalization

### 5. Hierarchical Data Storage (PostgreSQL Research)

**Five Models Compared**:

| Model | Best For | Query Performance | Update Performance | Complexity |
|-------|----------|-------------------|-------------------|------------|
| **Adjacency List** | Simple trees, frequent updates | Poor (recursive) | Excellent | Low |
| **Materialized Path** | Read-heavy, ancestor queries | Excellent | Good | Low |
| **Nested Sets** | Read-heavy, immutable | Excellent | Poor | Medium |
| **Closure Table** | Complex queries, many-to-many | Excellent | Good | Medium |
| **ltree (PostgreSQL)** | Path queries, hierarchical data | Excellent | Good | Low |

**Recommendation for Our System: Hybrid Approach**

```sql
-- 1. Adjacency List (core structure)
claims (
    id UUID PRIMARY KEY,
    parent_claim_id UUID REFERENCES claims(id),  -- Simple parent reference
    ...
)

-- 2. Materialized Path (fast queries)
claim_hierarchy (
    claim_id UUID,
    tree_path TEXT,  -- "1.2.5" format
    depth INT,       -- Pre-computed depth
    ...
)

-- 3. ltree Extension (PostgreSQL-specific power)
claim_paths (
    claim_id UUID,
    path ltree,      -- PostgreSQL ltree type: 'root.subclaim.leafclaim'
    ...
)

-- 4. Closure Table (for complex relationship queries)
claim_ancestors (
    ancestor_id UUID,
    descendant_id UUID,
    depth INT        -- How many levels between them
)
```

**Why Hybrid**:
- Adjacency List: Easy to understand, easy updates
- Materialized Path: Fast "all descendants" queries
- ltree: Pattern matching, path queries with operators
- Closure Table: Fast "find all ancestors", "common ancestor" queries

**Cycle Detection**:
```sql
-- Prevent cycles when inserting/updating
CREATE OR REPLACE FUNCTION prevent_claim_cycles()
RETURNS TRIGGER AS $$
BEGIN
    -- Check if new parent is a descendant (would create cycle)
    IF EXISTS (
        SELECT 1 FROM claim_ancestors
        WHERE ancestor_id = NEW.id AND descendant_id = NEW.parent_claim_id
    ) THEN
        RAISE EXCEPTION 'Cannot create cycle: claim % is already an ancestor of %',
            NEW.id, NEW.parent_claim_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

## Context Preservation System

### Multi-Level Context Capture

Claims exist in nested contexts - we must preserve ALL levels:

```
1. DOCUMENT CONTEXT
   ├── Source (journal article, book, blog post)
   ├── Publication metadata (authors, year, venue)
   ├── Document type (empirical study, review, opinion piece)
   └── Field/domain (machine learning, climate science, economics)

2. DISCOURSE CONTEXT
   ├── Section location (introduction, methods, results, discussion, conclusion)
   ├── Rhetorical function (main claim, supporting claim, counter-argument, limitation)
   ├── Stance (author's claim, citation of others, criticism)
   └── Argumentative role (premise, conclusion, rebuttal)

3. LINGUISTIC CONTEXT
   ├── Surrounding sentences (3 before, 3 after)
   ├── Paragraph topic/theme
   ├── Coreference chains (pronouns, definite references)
   └── Discourse markers ("however", "therefore", "in contrast")

4. SEMANTIC CONTEXT
   ├── Implicit assumptions
   ├── Presupposed knowledge
   ├── Definitional dependencies (terms requiring definition)
   └── Logical dependencies (claims this claim depends on)

5. QUANTITATIVE CONTEXT
   ├── Numbers and metrics ("15%", "100%", "by 2050")
   ├── Qualifiers ("can", "may", "will", "must", "always", "never", "some", "all")
   ├── Comparatives ("more than", "less than", "faster than")
   └── Scope indicators ("in this context", "for deep learning", "on ImageNet")

6. TEMPORAL CONTEXT
   ├── Time of publication (when was this claimed?)
   ├── Time references in claim ("in 2012", "by 2050", "currently")
   ├── Tense (past results, present state, future predictions)
   └── Historical context (paradigm at time of writing)
```

### Database Schema for Context

```sql
-- Complete context storage
CREATE TABLE claim_context (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,

    -- Document context
    source_document_id UUID REFERENCES documents(id),
    document_type VARCHAR(50),  -- 'empirical_study', 'review', 'opinion', etc.
    domain_tags TEXT[],

    -- Discourse context
    section_name VARCHAR(100),  -- 'introduction', 'methods', 'results', 'discussion'
    section_type VARCHAR(50),   -- 'background', 'methodology', 'findings', 'interpretation'
    rhetorical_function VARCHAR(50),  -- 'main_claim', 'support', 'counter', 'limitation'
    stance VARCHAR(50),  -- 'author_claim', 'cited_claim', 'challenged_claim'
    argumentative_role VARCHAR(50),  -- 'premise', 'conclusion', 'rebuttal', 'concession'

    -- Linguistic context (full text windows)
    preceding_text TEXT,  -- 3 sentences before
    following_text TEXT,  -- 3 sentences after
    paragraph_text TEXT,  -- Full paragraph

    -- Coreference information
    coreferents JSONB,  -- {"it": "renewable energy", "this": "the claim", ...}

    -- Semantic context
    implicit_assumptions TEXT[],
    presupposed_knowledge TEXT[],
    definitional_dependencies TEXT[],  -- Terms that need definition

    -- Quantitative context
    quantifiers JSONB,  -- {"modal": "can", "temporal": "by 2050", "scope": "100%"}

    -- Temporal context
    publication_date DATE,
    temporal_references JSONB,  -- {"claim_time": "2012", "prediction_time": "2050"}
    tense VARCHAR(20),  -- 'past', 'present', 'future', 'conditional'

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_claim_context_claim ON claim_context(claim_id);
CREATE INDEX idx_claim_context_section ON claim_context(section_name);
CREATE INDEX idx_claim_context_function ON claim_context(rhetorical_function);
```

## ClaimNormalizer Agent: Multi-Stage Pipeline

### Stage 1: Context Extraction

```python
class ContextExtractor:
    """
    Extracts complete context before any normalization.
    Uses multiple NLP models to capture all context layers.
    """

    async def extract_context(self, claim_text: str, document_data: dict) -> dict:
        """
        Extract all six levels of context.
        """
        context = {}

        # 1. Document context (from database)
        context['document'] = {
            'source_id': document_data['id'],
            'authors': document_data['authors'],
            'year': document_data['publication_year'],
            'type': document_data['document_type'],
            'domain': document_data['domain_tags']
        }

        # 2. Discourse context (NLP extraction)
        context['discourse'] = await self.extract_discourse_context(
            claim_text,
            document_data['full_text']
        )

        # 3. Linguistic context (window extraction)
        context['linguistic'] = self.extract_linguistic_window(
            claim_text,
            document_data['full_text']
        )

        # 4. Semantic context (LLM-powered)
        context['semantic'] = await self.extract_semantic_context(
            claim_text,
            context['linguistic']
        )

        # 5. Quantitative context (pattern matching + NER)
        context['quantitative'] = self.extract_quantifiers(claim_text)

        # 6. Temporal context
        context['temporal'] = self.extract_temporal_markers(
            claim_text,
            document_data['publication_date']
        )

        return context

    async def extract_discourse_context(self, claim_text: str, full_document: str) -> dict:
        """
        Identify section, rhetorical function, stance, argumentative role.
        Uses argument mining models.
        """
        # Find which section this claim appears in
        section = self.identify_section(claim_text, full_document)

        # Use LLM to classify rhetorical function
        rhetorical_function = await self.classify_rhetorical_function(
            claim_text,
            section_context=section
        )

        # Determine stance (is this the author's claim or are they citing/criticizing?)
        stance = await self.identify_stance(claim_text)

        # Argumentative role (Toulmin model)
        arg_role = await self.classify_argumentative_role(claim_text, section)

        return {
            'section': section,
            'function': rhetorical_function,
            'stance': stance,
            'role': arg_role
        }

    async def extract_semantic_context(self, claim_text: str, linguistic_context: dict) -> dict:
        """
        Use LLM to identify implicit assumptions and presuppositions.
        """
        prompt = f"""Analyze this claim and its context to identify implicit information:

CLAIM: "{claim_text}"

CONTEXT (preceding): {linguistic_context['preceding']}
CONTEXT (following): {linguistic_context['following']}

Identify:
1. Implicit assumptions (what must be true for this claim to make sense?)
2. Presupposed knowledge (what background knowledge is assumed?)
3. Terms that require explicit definition
4. Logical dependencies (other claims this depends on)

Return JSON:
{{
  "implicit_assumptions": ["assumption 1", "assumption 2"],
  "presupposed_knowledge": ["background fact 1", ...],
  "definitional_dependencies": ["term 1", "term 2"],
  "logical_dependencies": ["claim X must be true", ...]
}}"""

        response = await self.llm.generate(prompt, temperature=0.2, response_format='json')
        return json.loads(response)

    def extract_quantifiers(self, claim_text: str) -> dict:
        """
        Extract all quantifiers, modals, comparatives, scope indicators.
        These MUST be preserved in normalization.
        """
        import re

        quantifiers = {}

        # Modal verbs (indicate degree of certainty)
        modals = ['can', 'could', 'may', 'might', 'will', 'would', 'shall', 'should', 'must']
        quantifiers['modal'] = [m for m in modals if re.search(rf'\b{m}\b', claim_text, re.I)]

        # Quantifiers (scope)
        quant_patterns = [
            r'\b(all|every|each|any|some|most|many|few|several|no|none)\b',
            r'\b(\d+%|\d+\s*percent)\b',
            r'\b(always|never|often|rarely|sometimes|usually|generally)\b'
        ]
        quantifiers['scope'] = []
        for pattern in quant_patterns:
            quantifiers['scope'].extend(re.findall(pattern, claim_text, re.I))

        # Numbers and metrics
        quantifiers['metrics'] = re.findall(r'\b\d+(?:\.\d+)?(?:%|°C|km|kg|etc)?\b', claim_text)

        # Comparatives
        comp_patterns = [
            r'\b(more|less|greater|smaller|higher|lower|faster|slower)\s+than\b',
            r'\b(better|worse|superior|inferior)\s+(?:than|to)\b',
            r'\b(increase|decrease|improve|decline)(?:d|s)?\s+by\b'
        ]
        quantifiers['comparatives'] = []
        for pattern in comp_patterns:
            quantifiers['comparatives'].extend(re.findall(pattern, claim_text, re.I))

        return quantifiers
```

### Stage 2: Semantic Preservation Normalization

```python
class SemanticPreservingNormalizer:
    """
    Normalizes claims while rigorously preserving semantic meaning.
    Uses multiple strategies to ensure equivalence.
    """

    async def normalize(self, claim_text: str, context: dict) -> dict:
        """
        Multi-strategy normalization with semantic verification.
        """
        # Generate multiple normalization candidates
        candidates = await self.generate_candidates(claim_text, context)

        # Score each candidate for semantic preservation
        scored_candidates = []
        for candidate in candidates:
            score = await self.score_semantic_preservation(
                original=claim_text,
                normalized=candidate,
                context=context
            )
            scored_candidates.append({
                'text': candidate,
                'semantic_score': score['similarity'],
                'preservation_details': score
            })

        # Rank and select best
        best = max(scored_candidates, key=lambda x: x['semantic_score'])

        # Verify with SRL (Semantic Role Labeling)
        srl_verified = await self.verify_with_srl(claim_text, best['text'])

        # Final check: Do all quantifiers and modals still appear?
        quantifier_check = self.verify_quantifiers(
            original=claim_text,
            normalized=best['text'],
            context=context
        )

        return {
            'normalized_text': best['text'],
            'confidence': best['semantic_score'],
            'all_candidates': scored_candidates,
            'srl_verified': srl_verified,
            'quantifiers_preserved': quantifier_check,
            'needs_human_review': best['semantic_score'] < 0.95  # Flag for review
        }

    async def generate_candidates(self, claim_text: str, context: dict) -> List[str]:
        """
        Generate multiple normalization candidates using different strategies.
        """
        candidates = []

        # Strategy 1: Minimal normalization (remove only obvious fluff)
        candidates.append(await self.minimal_normalize(claim_text, context))

        # Strategy 2: Syntax-guided normalization (preserve syntactic structure)
        candidates.append(await self.syntax_guided_normalize(claim_text, context))

        # Strategy 3: Toulmin-based normalization (extract core claim from Toulmin structure)
        candidates.append(await self.toulmin_normalize(claim_text, context))

        # Strategy 4: SRL-based normalization (simplify while preserving semantic roles)
        candidates.append(await self.srl_normalize(claim_text, context))

        return candidates

    async def score_semantic_preservation(self, original: str, normalized: str, context: dict) -> dict:
        """
        Multi-metric semantic similarity scoring.
        """
        # 1. Embedding similarity (high-quality embeddings)
        embedding_sim = await self.compute_embedding_similarity(original, normalized)

        # 2. LLM-based semantic equivalence check
        llm_check = await self.llm_equivalence_check(original, normalized, context)

        # 3. Information preservation (are all key facts still present?)
        info_preservation = await self.check_information_preservation(
            original, normalized, context
        )

        # 4. Quantifier preservation (exact match required)
        quant_preserved = self.verify_quantifiers(original, normalized, context)

        # Combined score (weighted)
        combined_score = (
            0.30 * embedding_sim +
            0.40 * llm_check['equivalence_score'] +
            0.20 * info_preservation +
            0.10 * (1.0 if quant_preserved else 0.0)
        )

        return {
            'similarity': combined_score,
            'embedding_similarity': embedding_sim,
            'llm_equivalence': llm_check,
            'information_preserved': info_preservation,
            'quantifiers_preserved': quant_preserved
        }

    async def llm_equivalence_check(self, original: str, normalized: str, context: dict) -> dict:
        """
        Use LLM to verify semantic equivalence.
        """
        prompt = f"""You are a semantic equivalence validator. Determine if two claims mean the same thing.

ORIGINAL CLAIM: "{original}"
NORMALIZED CLAIM: "{normalized}"

CONTEXT:
- Domain: {context['document']['domain']}
- Section: {context['discourse']['section']}
- Rhetorical function: {context['discourse']['function']}

QUESTIONS:
1. Do these claims make the same assertion? (yes/no)
2. Are all quantifiers preserved? ("100%", "by 2050", "can", etc.) (yes/no)
3. Are all named entities preserved? (yes/no)
4. Is the scope the same? (yes/no)
5. Is the certainty level the same? (yes/no)
6. Overall semantic equivalence score (0.0-1.0)
7. If not equivalent, what information was lost or changed?

Return JSON:
{{
  "same_assertion": true/false,
  "quantifiers_preserved": true/false,
  "entities_preserved": true/false,
  "scope_preserved": true/false,
  "certainty_preserved": true/false,
  "equivalence_score": 0.0-1.0,
  "differences": "what changed, if anything"
}}"""

        response = await self.llm.generate(prompt, temperature=0.1, response_format='json')
        return json.loads(response)

    async def verify_with_srl(self, original: str, normalized: str) -> bool:
        """
        Use Semantic Role Labeling to verify predicate-argument structure is preserved.
        """
        # Extract SRL for both
        original_srl = await self.extract_srl(original)
        normalized_srl = await self.extract_srl(normalized)

        # Check if all semantic roles are preserved
        # ARG0 (agent), ARG1 (patient), ARGM-* (modifiers) should match

        roles_match = (
            original_srl['ARG0'] == normalized_srl['ARG0'] and
            original_srl['ARG1'] == normalized_srl['ARG1'] and
            original_srl['predicate'] == normalized_srl['predicate']
        )

        modifiers_preserved = all(
            mod in normalized_srl['modifiers']
            for mod in original_srl['modifiers']
        )

        return roles_match and modifiers_preserved
```

### Stage 3: Human-in-the-Loop Validation

```python
class HumanValidationInterface:
    """
    Presents normalization to user for validation and refinement.
    Learns from user feedback to improve future normalizations.
    """

    async def request_validation(self, claim_id: UUID, normalization_result: dict) -> dict:
        """
        Present normalization to user for approval/revision.
        """
        # Store normalization attempt
        attempt_id = await self.store_normalization_attempt(claim_id, normalization_result)

        # Create validation task
        validation = {
            'attempt_id': attempt_id,
            'claim_id': claim_id,
            'original_claim': normalization_result['original'],
            'normalized_claim': normalization_result['normalized_text'],
            'confidence': normalization_result['confidence'],
            'context_summary': self.summarize_context(normalization_result['context']),
            'all_candidates': normalization_result['all_candidates'],
            'status': 'pending_review'
        }

        # Save to database
        await self.db.execute("""
            INSERT INTO normalization_validations (
                attempt_id, claim_id, original_text, normalized_text,
                confidence, context_data, candidates, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            attempt_id, claim_id, validation['original_claim'],
            validation['normalized_claim'], validation['confidence'],
            json.dumps(normalization_result['context']),
            json.dumps(validation['all_candidates']),
            'pending_review'
        ))

        return validation

    async def process_user_feedback(self, validation_id: UUID, feedback: dict) -> dict:
        """
        Process user feedback on normalization.

        Feedback types:
        1. Approve: Accept normalization as-is
        2. Select Alternative: Choose different candidate
        3. Edit: User provides corrected version
        4. Reject: Claim cannot be normalized (too complex, needs decomposition)
        """
        feedback_type = feedback['type']

        if feedback_type == 'approve':
            # Mark as approved, use normalized version
            await self.approve_normalization(validation_id)
            return {'status': 'approved'}

        elif feedback_type == 'select_alternative':
            # User chose a different candidate
            candidate_index = feedback['candidate_index']
            await self.select_alternative(validation_id, candidate_index)

            # Learn: This candidate was better than our top choice
            await self.record_preference(validation_id, candidate_index)
            return {'status': 'alternative_selected'}

        elif feedback_type == 'edit':
            # User provided corrected normalization
            user_version = feedback['corrected_text']
            await self.save_user_correction(validation_id, user_version)

            # Learn: Analyze what user changed
            await self.analyze_user_correction(
                original_normalized=feedback['original_normalized'],
                user_corrected=user_version,
                context=feedback['context']
            )
            return {'status': 'user_corrected'}

        elif feedback_type == 'reject':
            # Claim is too complex, needs decomposition first
            reason = feedback.get('reason', 'Too complex')
            await self.mark_for_decomposition(validation_id, reason)
            return {'status': 'needs_decomposition'}

        else:
            raise ValueError(f"Unknown feedback type: {feedback_type}")

    async def analyze_user_correction(self, original_normalized: str, user_corrected: str, context: dict):
        """
        Learn from user corrections to improve future normalizations.
        """
        # Compute diff
        changes = self.compute_semantic_diff(original_normalized, user_corrected)

        # Use LLM to analyze what was wrong with our normalization
        analysis_prompt = f"""Analyze why the user corrected this normalization:

OUR NORMALIZATION: "{original_normalized}"
USER'S CORRECTION: "{user_corrected}"

CHANGES MADE: {changes}

CONTEXT: {json.dumps(context, indent=2)}

What did we get wrong? What pattern should we learn?

Return JSON:
{{
  "error_type": "lost_quantifier" | "changed_scope" | "lost_context" | "changed_meaning" | "wrong_simplification",
  "specific_issue": "description of what went wrong",
  "learning": "what to do differently next time",
  "confidence_adjustment": -0.1  // how much to reduce confidence for similar cases
}}"""

        learning = await self.llm.generate(analysis_prompt, temperature=0.2, response_format='json')
        learning_data = json.loads(learning)

        # Store learning for future improvement
        await self.db.execute("""
            INSERT INTO normalization_learnings (
                validation_id, error_type, issue, learning, confidence_adjustment
            ) VALUES (%s, %s, %s, %s, %s)
        """, (
            validation_id,
            learning_data['error_type'],
            learning_data['specific_issue'],
            learning_data['learning'],
            learning_data['confidence_adjustment']
        ))

        # Update normalization model with this learning
        await self.update_normalization_strategy(learning_data)
```

### Stage 4: Iterative Refinement

```python
class IterativeNormalizer:
    """
    Handles iterative normalization with user feedback loop.
    """

    async def normalize_with_feedback_loop(self, claim_id: UUID, max_iterations: int = 3) -> dict:
        """
        Normalize claim, get user feedback, refine, repeat until approved.
        """
        iteration = 0
        approved = False

        while not approved and iteration < max_iterations:
            iteration += 1

            # Attempt normalization
            result = await self.normalizer.normalize(claim_id)

            # Request user validation
            validation = await self.validator.request_validation(claim_id, result)

            # Wait for user feedback (async - could be hours/days)
            feedback = await self.wait_for_user_feedback(validation['id'])

            if feedback['type'] == 'approve':
                approved = True
                final_normalized = result['normalized_text']

            elif feedback['type'] == 'edit':
                # User provided correction - use it and we're done
                approved = True
                final_normalized = feedback['corrected_text']

                # Learn from correction
                await self.validator.analyze_user_correction(
                    result['normalized_text'],
                    feedback['corrected_text'],
                    result['context']
                )

            elif feedback['type'] == 'select_alternative':
                # User chose different candidate - use it
                approved = True
                final_normalized = result['all_candidates'][feedback['candidate_index']]['text']

            elif feedback['type'] == 'reject':
                # Too complex - try decomposition first
                await self.decompose_claim(claim_id)
                return {'status': 'decomposed', 'message': 'Claim was too complex, decomposed into sub-claims'}

            else:
                # Unclear feedback - ask for clarification
                await self.request_clarification(validation['id'])

        if not approved:
            # Max iterations reached without approval
            # Flag for manual review
            await self.flag_for_manual_review(claim_id, "Could not normalize after {} iterations".format(max_iterations))
            return {'status': 'manual_review_needed'}

        # Save final approved normalization
        await self.save_final_normalization(claim_id, final_normalized, iteration)

        return {
            'status': 'approved',
            'normalized_text': final_normalized,
            'iterations': iteration
        }
```

## Database Schema Updates

```sql
-- ============================================================================
-- NORMALIZATION WITH HUMAN-IN-THE-LOOP
-- ============================================================================

-- Normalization attempts (before approval)
CREATE TABLE normalization_attempts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,

    -- Normalization result
    original_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    confidence DECIMAL(3,2) NOT NULL,

    -- Candidates considered
    all_candidates JSONB,  -- All normalization options generated

    -- Semantic verification
    semantic_score DECIMAL(3,2),
    srl_verified BOOLEAN,
    quantifiers_preserved BOOLEAN,

    -- Context used
    context_data JSONB,

    -- Status
    status VARCHAR(50) DEFAULT 'pending_validation',  -- 'pending_validation', 'approved', 'rejected', 'superseded'

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_norm_attempts_claim ON normalization_attempts(claim_id);
CREATE INDEX idx_norm_attempts_status ON normalization_attempts(status);

-- Human validation tasks
CREATE TABLE normalization_validations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    attempt_id UUID NOT NULL REFERENCES normalization_attempts(id) ON DELETE CASCADE,
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,

    -- What user sees
    original_text TEXT NOT NULL,
    normalized_text TEXT NOT NULL,
    confidence DECIMAL(3,2),
    context_summary TEXT,
    candidates JSONB,

    -- User feedback
    status VARCHAR(50) DEFAULT 'pending_review',  -- 'pending_review', 'approved', 'edited', 'rejected', 'alternative_selected'
    feedback_type VARCHAR(50),  -- 'approve', 'edit', 'select_alternative', 'reject'
    user_corrected_text TEXT,  -- If user edited
    selected_candidate_index INT,  -- If user selected alternative
    rejection_reason TEXT,  -- If rejected

    -- Metadata
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,
    reviewed_by VARCHAR(100)  -- User identifier
);

CREATE INDEX idx_validations_status ON normalization_validations(status);
CREATE INDEX idx_validations_pending ON normalization_validations(status) WHERE status = 'pending_review';

-- Learning from user corrections
CREATE TABLE normalization_learnings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    validation_id UUID NOT NULL REFERENCES normalization_validations(id) ON DELETE CASCADE,

    -- What went wrong
    error_type VARCHAR(50) NOT NULL,  -- 'lost_quantifier', 'changed_scope', 'lost_context', 'changed_meaning'
    specific_issue TEXT NOT NULL,

    -- What to learn
    learning TEXT NOT NULL,  -- Natural language description of lesson
    confidence_adjustment DECIMAL(3,2),  -- How much to penalize similar cases

    -- Pattern matching
    error_pattern JSONB,  -- Structured pattern to match in future

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_learnings_type ON normalization_learnings(error_type);

-- Final approved normalizations (the source of truth)
CREATE TABLE approved_normalizations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE UNIQUE,

    -- Final normalized form
    normalized_text TEXT NOT NULL,

    -- How we got here
    source_attempt_id UUID REFERENCES normalization_attempts(id),
    iterations_required INT DEFAULT 1,
    final_confidence DECIMAL(3,2),

    -- Human validation
    was_user_edited BOOLEAN DEFAULT FALSE,
    validator_id VARCHAR(100),

    -- Metadata
    approved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_approved_norm_claim ON approved_normalizations(claim_id);

-- Decomposition history (when claims are too complex to normalize)
CREATE TABLE claim_decompositions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    parent_claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,

    -- Decomposition metadata
    reason TEXT,  -- Why was this decomposed?
    decomposition_strategy VARCHAR(50),  -- 'conjunctive_and', 'disjunctive_or', 'conditional_if_then', 'toulmin'

    -- Generated sub-claims
    sub_claim_ids UUID[],

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_decomp_parent ON claim_decompositions(parent_claim_id);
```

## CLI Commands for Human-in-the-Loop

```bash
# View pending normalization validations
python research_agent.py normalize-queue
# Output:
# Pending Normalizations (5):
# 1. Claim #123: "Renewable energy can..." → "Renewable energy can meet 100%..."
#    Confidence: 0.87 | Context: Climate Science, Results section
# 2. Claim #124: "Deep learning models..." → "Deep learning models outperformed..."
#    Confidence: 0.92 | Context: Machine Learning, Findings
# ...

# Review a specific normalization
python research_agent.py review-normalization --validation-id abc-123
# Shows:
# - Original claim
# - Proposed normalization
# - All alternative candidates
# - Context summary
# - Semantic preservation scores

# Approve normalization
python research_agent.py approve-normalization --validation-id abc-123

# Select alternative candidate
python research_agent.py select-alternative --validation-id abc-123 --candidate 2

# Edit normalization
python research_agent.py edit-normalization --validation-id abc-123 \
  --corrected "User's corrected version of the claim"

# Reject (mark for decomposition)
python research_agent.py reject-normalization --validation-id abc-123 \
  --reason "Claim is conjunctive, needs decomposition"

# View learning history
python research_agent.py show-learnings
# Output:
# Normalization Learnings:
# 1. [lost_quantifier] Removed "by 2050" temporal marker
#    Learning: Always preserve temporal qualifiers in predictions
#    Confidence adjustment: -0.15
# 2. [changed_scope] Changed "can" to "will"
#    Learning: Modal verbs indicate certainty - must preserve exactly
#    Confidence adjustment: -0.20
```

## Quality Assurance Metrics

Track normalization quality over time:

```sql
-- Quality metrics view
CREATE VIEW normalization_quality_metrics AS
SELECT
    DATE_TRUNC('week', approved_at) as week,
    COUNT(*) as total_normalizations,
    AVG(iterations_required) as avg_iterations,
    AVG(final_confidence) as avg_confidence,
    SUM(CASE WHEN was_user_edited THEN 1 ELSE 0 END)::FLOAT / COUNT(*) as user_edit_rate,
    AVG(CASE WHEN was_user_edited THEN iterations_required ELSE NULL END) as avg_iterations_when_edited
FROM approved_normalizations
GROUP BY week
ORDER BY week DESC;

-- Error type distribution
CREATE VIEW normalization_error_distribution AS
SELECT
    error_type,
    COUNT(*) as frequency,
    AVG(confidence_adjustment) as avg_confidence_penalty
FROM normalization_learnings
GROUP BY error_type
ORDER BY frequency DESC;
```

This system ensures:
1. ✅ **No semantic drift** - multi-stage verification
2. ✅ **Complete context preservation** - 6 layers captured
3. ✅ **Human validation** - user approves every normalization
4. ✅ **Continuous learning** - system improves from corrections
5. ✅ **Audit trail** - full history of normalization decisions
6. ✅ **Recursive support** - hybrid database structure with cycle detection

Ready to implement this?
