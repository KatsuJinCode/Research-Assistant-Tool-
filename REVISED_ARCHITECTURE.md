# Research Verification Agent Swarm - Pull-Based Architecture

## Core Architecture Principle: Work Queue System

Agents **discover and claim** work from a persistent database rather than spawning child agents. This creates a self-organizing system where:

1. **Claims are endpoints** that agents can discover
2. **Agents pull work** from priority queues
3. **New claims are added to database** for future investigation
4. **Separate passes** allow different agents to expand the claim tree
5. **No recursion** - just continuous autonomous background processing

## Revised System Flow

```
┌──────────────────────────────────────────────────────────────┐
│                     Persistent Work Queue                    │
│  ┌────────────┐  ┌──────────────┐  ┌────────────────┐       │
│  │ Unverified │  │ Unchallenged │  │ Unexpanded     │       │
│  │   Claims   │  │    Claims    │  │    Claims      │       │
│  └─────┬──────┘  └──────┬───────┘  └────────┬───────┘       │
│        │                │                    │               │
└────────┼────────────────┼────────────────────┼───────────────┘
         │                │                    │
         ↓                ↓                    ↓
    ┌────────┐       ┌────────┐          ┌────────┐
    │ Agent  │       │ Agent  │          │ Agent  │
    │ Pool   │       │ Pool   │          │ Pool   │
    │(Support)│      │(Challenge)│       │(Discovery)│
    └────┬───┘       └────┬───┘          └────┬───┘
         │                │                    │
         ↓                ↓                    ↓
    ┌────────────────────────────────────────────┐
    │         Investigation Results              │
    │  ┌──────────┐  ┌──────────┐  ┌─────────┐  │
    │  │ Evidence │  │ New Claims│  │Findings │  │
    │  │  (APA)   │  │  (spawn)  │  │         │  │
    │  └──────────┘  └──────────┘  └─────────┘  │
    └────────────────────────────────────────────┘
                         │
                         ↓
              ┌──────────────────┐
              │  Claims added to │
              │  work queue for  │
              │  next agent pass │
              └──────────────────┘
```

## Database Design - PostgreSQL with Extensions

### Why PostgreSQL?
- **JSONB**: Flexible metadata storage for claims and evidence
- **Full-text search**: Built-in search capabilities
- **pgvector**: Semantic similarity for claim matching
- **Concurrent transactions**: Multiple agents working simultaneously
- **Foreign keys**: Maintain data integrity across claim trees
- **Partitioning**: Scale to millions of claims
- **Triggers**: Auto-update priorities and work queues

### Required PostgreSQL Extensions
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- Fuzzy text search
CREATE EXTENSION IF NOT EXISTS "vector";         -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS "btree_gist";     -- Advanced indexing
```

## Complete Database Schema

```sql
-- ============================================================================
-- CORE ENTITIES
-- ============================================================================

-- Documents (research papers, articles)
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    authors JSONB,  -- [{name, affiliation, email}]
    source_type VARCHAR(50) NOT NULL,  -- pdf, docx, url, arxiv, pubmed
    file_path TEXT,
    url TEXT,
    doi TEXT,
    abstract TEXT,
    full_text TEXT,
    metadata JSONB,  -- {journal, year, volume, issue, pages, keywords}
    embedding vector(1536),  -- Document embedding for similarity
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    processing_status VARCHAR(50) DEFAULT 'pending',  -- pending, processing, completed, failed

    CONSTRAINT valid_source_type CHECK (source_type IN ('pdf', 'docx', 'txt', 'url', 'arxiv', 'pubmed', 'semantic_scholar'))
);

CREATE INDEX idx_documents_doi ON documents(doi) WHERE doi IS NOT NULL;
CREATE INDEX idx_documents_status ON documents(processing_status);
CREATE INDEX idx_documents_embedding ON documents USING ivfflat (embedding vector_cosine_ops);

-- ============================================================================
-- CLAIMS SYSTEM
-- ============================================================================

CREATE TYPE claim_type AS ENUM (
    'empirical',        -- Based on data/observation
    'theoretical',      -- Conceptual/framework-based
    'methodological',   -- About research methods
    'normative',        -- Should/ought statements
    'predictive',       -- Future-oriented
    'definitional',     -- About meanings/concepts
    'causal'           -- X causes Y
);

CREATE TYPE claim_status AS ENUM (
    'extracted',        -- Newly extracted from document
    'queued',          -- In work queue, not yet claimed
    'investigating',   -- Agent currently working on it
    'supported',       -- Has supporting evidence
    'challenged',      -- Has challenging evidence
    'controversial',   -- Both supported and challenged
    'verified',        -- High confidence support
    'refuted',         -- High confidence challenge
    'uncertain',       -- Insufficient evidence
    'archived'         -- Completed investigation
);

CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    parent_claim_id UUID REFERENCES claims(id) ON DELETE SET NULL,

    -- Claim content
    text TEXT NOT NULL,
    claim_type claim_type NOT NULL,
    context TEXT,  -- Surrounding text for context
    location_in_doc JSONB,  -- {page, paragraph, section}

    -- Metadata
    entities JSONB,  -- Extracted entities: {people: [], orgs: [], concepts: [], methods: []}
    keywords TEXT[],
    embedding vector(1536),  -- For semantic similarity

    -- Status tracking
    status claim_status DEFAULT 'extracted',
    confidence_score DECIMAL(3,2),  -- 0.00 to 1.00
    priority_score INT DEFAULT 0,  -- Calculated priority for investigation

    -- Investigation tracking
    investigation_count INT DEFAULT 0,
    support_count INT DEFAULT 0,
    challenge_count INT DEFAULT 0,
    neutral_count INT DEFAULT 0,

    -- Timestamps
    extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_investigated_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Tree structure
    depth_level INT DEFAULT 0,  -- 0 = original document claim
    root_claim_id UUID,  -- Points to original claim in tree

    CONSTRAINT confidence_range CHECK (confidence_score BETWEEN 0.00 AND 1.00)
);

-- Indexes for efficient querying
CREATE INDEX idx_claims_status ON claims(status);
CREATE INDEX idx_claims_priority ON claims(priority_score DESC) WHERE status IN ('queued', 'extracted');
CREATE INDEX idx_claims_parent ON claims(parent_claim_id) WHERE parent_claim_id IS NOT NULL;
CREATE INDEX idx_claims_root ON claims(root_claim_id) WHERE root_claim_id IS NOT NULL;
CREATE INDEX idx_claims_type ON claims(claim_type);
CREATE INDEX idx_claims_embedding ON claims USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX idx_claims_keywords ON claims USING gin(keywords);

-- Full-text search on claim text
CREATE INDEX idx_claims_text_search ON claims USING gin(to_tsvector('english', text));

-- ============================================================================
-- AGENT SYSTEM
-- ============================================================================

CREATE TYPE agent_framework AS ENUM (
    'support_empirical',
    'support_theoretical',
    'support_cross_domain',
    'challenge_empirical',
    'challenge_methodological',
    'challenge_alternative',
    'analysis_historical',
    'analysis_definitional',
    'analysis_scope',
    'discovery_lateral',
    'discovery_emerging'
);

CREATE TYPE agent_status AS ENUM (
    'idle',
    'working',
    'paused',
    'failed',
    'completed'
);

-- Agent Registry (instances of agents)
CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    framework agent_framework NOT NULL,
    instance_name VARCHAR(100) NOT NULL,  -- e.g., "support_empirical_001"
    status agent_status DEFAULT 'idle',

    -- Current work
    current_claim_id UUID REFERENCES claims(id) ON DELETE SET NULL,
    current_investigation_id UUID,

    -- Performance metrics
    investigations_completed INT DEFAULT 0,
    average_duration_seconds DECIMAL(10,2),
    success_rate DECIMAL(3,2),

    -- Resource tracking
    api_calls_used INT DEFAULT 0,
    tokens_consumed BIGINT DEFAULT 0,

    -- Lifecycle
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP,
    last_error TEXT,

    CONSTRAINT unique_instance_name UNIQUE (instance_name)
);

CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_framework ON agents(framework);

-- ============================================================================
-- INVESTIGATIONS (Work Units)
-- ============================================================================

CREATE TYPE investigation_status AS ENUM (
    'queued',
    'claimed',
    'in_progress',
    'completed',
    'failed',
    'timeout'
);

CREATE TABLE investigations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    agent_framework agent_framework NOT NULL,

    -- Work assignment
    status investigation_status DEFAULT 'queued',
    priority INT DEFAULT 0,
    claimed_at TIMESTAMP,

    -- Execution
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INT,

    -- Results summary
    findings_count INT DEFAULT 0,
    evidence_count INT DEFAULT 0,
    new_claims_spawned INT DEFAULT 0,

    -- Resource usage
    api_calls INT DEFAULT 0,
    tokens_used INT DEFAULT 0,

    -- Error handling
    error_message TEXT,
    retry_count INT DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_investigations_claim ON investigations(claim_id);
CREATE INDEX idx_investigations_status ON investigations(status);
CREATE INDEX idx_investigations_priority ON investigations(priority DESC) WHERE status = 'queued';
CREATE INDEX idx_investigations_agent ON investigations(agent_id) WHERE agent_id IS NOT NULL;

-- ============================================================================
-- FINDINGS (Agent Results)
-- ============================================================================

CREATE TYPE finding_type AS ENUM (
    'support',
    'challenge',
    'neutral',
    'expansion',
    'clarification',
    'limitation'
);

CREATE TABLE findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,

    finding_type finding_type NOT NULL,
    summary TEXT NOT NULL,
    detailed_analysis TEXT,

    confidence DECIMAL(3,2),  -- Agent's confidence in this finding

    -- Generated content
    new_claims_text TEXT[],  -- Array of new claim texts to be created

    metadata JSONB,  -- Additional structured data

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT confidence_range CHECK (confidence BETWEEN 0.00 AND 1.00)
);

CREATE INDEX idx_findings_investigation ON findings(investigation_id);
CREATE INDEX idx_findings_claim ON findings(claim_id);
CREATE INDEX idx_findings_type ON findings(finding_type);

-- ============================================================================
-- EVIDENCE SYSTEM
-- ============================================================================

CREATE TYPE source_type AS ENUM (
    'peer_reviewed_journal',
    'preprint',
    'book',
    'book_chapter',
    'conference_paper',
    'thesis',
    'technical_report',
    'web_article',
    'expert_opinion',
    'dataset',
    'government_report'
);

CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    finding_id UUID NOT NULL REFERENCES findings(id) ON DELETE CASCADE,

    -- Source identification
    source_type source_type NOT NULL,
    source_category VARCHAR(20) NOT NULL,  -- 'academic' or 'web'

    -- Citation information (APA 7 components)
    authors JSONB,  -- [{family_name, given_name, suffix}]
    publication_year INT,
    title TEXT NOT NULL,
    container_title TEXT,  -- Journal/book name
    volume TEXT,
    issue TEXT,
    pages TEXT,
    publisher TEXT,
    doi TEXT,
    url TEXT,

    -- Full APA citation (auto-generated)
    citation_apa TEXT NOT NULL,

    -- Content
    abstract TEXT,
    relevant_quote TEXT,
    context TEXT,

    -- Metadata
    keywords TEXT[],
    accessed_date DATE DEFAULT CURRENT_DATE,

    -- Quality scores
    relevance_score DECIMAL(3,2),
    credibility_score DECIMAL(3,2),
    citation_count INT,  -- How many times cited by others

    -- Embeddings for similarity
    embedding vector(1536),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_category CHECK (source_category IN ('academic', 'web')),
    CONSTRAINT relevance_range CHECK (relevance_score BETWEEN 0.00 AND 1.00),
    CONSTRAINT credibility_range CHECK (credibility_score BETWEEN 0.00 AND 1.00)
);

CREATE INDEX idx_evidence_finding ON evidence(finding_id);
CREATE INDEX idx_evidence_category ON evidence(source_category);
CREATE INDEX idx_evidence_doi ON evidence(doi) WHERE doi IS NOT NULL;
CREATE INDEX idx_evidence_relevance ON evidence(relevance_score DESC);
CREATE INDEX idx_evidence_embedding ON evidence USING ivfflat (embedding vector_cosine_ops);

-- ============================================================================
-- CLAIM RELATIONSHIPS (Graph Structure)
-- ============================================================================

CREATE TYPE relationship_type AS ENUM (
    'supports',
    'challenges',
    'refines',
    'contradicts',
    'extends',
    'requires',  -- Dependency
    'similar_to',
    'example_of',
    'generalizes'
);

CREATE TABLE claim_relationships (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    target_claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    relationship_type relationship_type NOT NULL,

    strength DECIMAL(3,2),  -- How strong is this relationship
    evidence_id UUID REFERENCES evidence(id) ON DELETE SET NULL,  -- What evidence establishes this

    created_by_investigation_id UUID REFERENCES investigations(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT no_self_reference CHECK (source_claim_id != target_claim_id),
    CONSTRAINT strength_range CHECK (strength BETWEEN 0.00 AND 1.00)
);

CREATE INDEX idx_relationships_source ON claim_relationships(source_claim_id);
CREATE INDEX idx_relationships_target ON claim_relationships(target_claim_id);
CREATE INDEX idx_relationships_type ON claim_relationships(relationship_type);

-- Prevent duplicate relationships
CREATE UNIQUE INDEX idx_unique_relationship
ON claim_relationships(source_claim_id, target_claim_id, relationship_type);

-- ============================================================================
-- WORK QUEUE VIEWS (What Agents See)
-- ============================================================================

-- Unverified claims needing support investigation
CREATE VIEW unverified_claims AS
SELECT
    c.*,
    c.priority_score + (EXTRACT(EPOCH FROM (NOW() - c.extracted_at))/3600)::INT AS dynamic_priority
FROM claims c
WHERE c.status IN ('extracted', 'queued')
  AND c.support_count = 0
ORDER BY dynamic_priority DESC;

-- Unchallenged claims needing challenge investigation
CREATE VIEW unchallenged_claims AS
SELECT
    c.*,
    c.priority_score + (EXTRACT(EPOCH FROM (NOW() - c.extracted_at))/3600)::INT AS dynamic_priority
FROM claims c
WHERE c.status IN ('supported', 'queued')
  AND c.challenge_count = 0
ORDER BY dynamic_priority DESC;

-- Claims ready for analysis (have both support and challenge)
CREATE VIEW analyzable_claims AS
SELECT
    c.*,
    c.support_count,
    c.challenge_count
FROM claims c
WHERE c.support_count > 0
  AND c.challenge_count > 0
  AND c.neutral_count < 2;  -- Haven't been analyzed much yet

-- High-priority unexpanded claims (have few connections)
CREATE VIEW unexpanded_claims AS
SELECT
    c.*,
    (SELECT COUNT(*) FROM claim_relationships WHERE source_claim_id = c.id) as outgoing_links,
    (SELECT COUNT(*) FROM claim_relationships WHERE target_claim_id = c.id) as incoming_links
FROM claims c
WHERE c.status NOT IN ('archived')
  AND (SELECT COUNT(*) FROM claim_relationships WHERE source_claim_id = c.id) < 3
ORDER BY c.priority_score DESC;

-- ============================================================================
-- INVESTIGATION CHAINS (Tree Traversal)
-- ============================================================================

CREATE TABLE investigation_chains (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    root_claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,

    -- Chain metadata
    current_depth INT DEFAULT 0,
    max_depth_reached INT DEFAULT 0,
    total_claims INT DEFAULT 1,
    total_investigations INT DEFAULT 0,

    -- Status
    is_active BOOLEAN DEFAULT TRUE,

    -- Analytics
    support_evidence_count INT DEFAULT 0,
    challenge_evidence_count INT DEFAULT 0,
    neutral_evidence_count INT DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chains_root ON investigation_chains(root_claim_id);
CREATE INDEX idx_chains_active ON investigation_chains(is_active) WHERE is_active = TRUE;

-- ============================================================================
-- SEARCH CACHE (Performance Optimization)
-- ============================================================================

CREATE TABLE search_cache (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    query_hash VARCHAR(64) NOT NULL,  -- MD5/SHA256 of search query
    search_type VARCHAR(50) NOT NULL,  -- 'semantic_scholar', 'arxiv', 'pubmed', 'web'
    query_text TEXT NOT NULL,

    results JSONB NOT NULL,  -- Cached search results
    result_count INT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_count INT DEFAULT 0,
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    expires_at TIMESTAMP  -- NULL = never expires
);

CREATE UNIQUE INDEX idx_search_cache_hash ON search_cache(query_hash, search_type);
CREATE INDEX idx_search_cache_expires ON search_cache(expires_at) WHERE expires_at IS NOT NULL;

-- ============================================================================
-- SYSTEM LOGS
-- ============================================================================

CREATE TABLE system_logs (
    id BIGSERIAL PRIMARY KEY,
    level VARCHAR(20) NOT NULL,  -- DEBUG, INFO, WARNING, ERROR, CRITICAL
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    investigation_id UUID REFERENCES investigations(id) ON DELETE SET NULL,

    message TEXT NOT NULL,
    context JSONB,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_logs_level ON system_logs(level);
CREATE INDEX idx_logs_created ON system_logs(created_at DESC);
CREATE INDEX idx_logs_agent ON system_logs(agent_id) WHERE agent_id IS NOT NULL;

-- Partition by month for performance
-- CREATE TABLE system_logs_y2024m01 PARTITION OF system_logs
--     FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

-- ============================================================================
-- TRIGGERS & AUTOMATION
-- ============================================================================

-- Auto-update claim status based on investigation results
CREATE OR REPLACE FUNCTION update_claim_status()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE claims
    SET
        investigation_count = (SELECT COUNT(*) FROM investigations WHERE claim_id = NEW.claim_id AND status = 'completed'),
        support_count = (SELECT COUNT(*) FROM findings WHERE claim_id = NEW.claim_id AND finding_type = 'support'),
        challenge_count = (SELECT COUNT(*) FROM findings WHERE claim_id = NEW.claim_id AND finding_type = 'challenge'),
        neutral_count = (SELECT COUNT(*) FROM findings WHERE claim_id = NEW.claim_id AND finding_type IN ('neutral', 'clarification')),
        last_investigated_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.claim_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_claim_status
AFTER INSERT ON findings
FOR EACH ROW
EXECUTE FUNCTION update_claim_status();

-- Auto-calculate priority score for claims
CREATE OR REPLACE FUNCTION calculate_claim_priority()
RETURNS TRIGGER AS $$
DECLARE
    base_priority INT := 50;
    age_hours DECIMAL;
BEGIN
    age_hours := EXTRACT(EPOCH FROM (NOW() - NEW.extracted_at)) / 3600;

    -- Priority factors:
    -- +20 for empirical claims (more verifiable)
    -- +10 for causal claims (important)
    -- +1 per hour old (older = more urgent)
    -- +30 if from root document (original paper claims prioritized)
    -- -10 per investigation already done

    NEW.priority_score := base_priority
        + CASE WHEN NEW.claim_type = 'empirical' THEN 20 ELSE 0 END
        + CASE WHEN NEW.claim_type = 'causal' THEN 10 ELSE 0 END
        + age_hours::INT
        + CASE WHEN NEW.parent_claim_id IS NULL THEN 30 ELSE 0 END
        - (NEW.investigation_count * 10);

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_calculate_priority
BEFORE INSERT OR UPDATE ON claims
FOR EACH ROW
EXECUTE FUNCTION calculate_claim_priority();

-- Auto-spawn new claims from findings
CREATE OR REPLACE FUNCTION spawn_claims_from_findings()
RETURNS TRIGGER AS $$
DECLARE
    new_claim_text TEXT;
    parent_claim_id UUID;
BEGIN
    IF NEW.new_claims_text IS NOT NULL AND array_length(NEW.new_claims_text, 1) > 0 THEN
        SELECT claim_id INTO parent_claim_id FROM findings WHERE id = NEW.id;

        FOREACH new_claim_text IN ARRAY NEW.new_claims_text
        LOOP
            INSERT INTO claims (
                parent_claim_id,
                text,
                claim_type,
                status,
                depth_level,
                root_claim_id
            )
            SELECT
                parent_claim_id,
                new_claim_text,
                c.claim_type,  -- Inherit type from parent
                'queued',
                c.depth_level + 1,
                COALESCE(c.root_claim_id, c.id)
            FROM claims c
            WHERE c.id = parent_claim_id;
        END LOOP;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_spawn_claims
AFTER INSERT ON findings
FOR EACH ROW
EXECUTE FUNCTION spawn_claims_from_findings();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Get next available work for an agent framework
CREATE OR REPLACE FUNCTION get_next_work(p_framework agent_framework)
RETURNS UUID AS $$
DECLARE
    claim_id UUID;
    investigation_id UUID;
BEGIN
    -- Find highest priority unclaimed investigation matching framework
    SELECT i.id, i.claim_id INTO investigation_id, claim_id
    FROM investigations i
    WHERE i.status = 'queued'
      AND i.agent_framework = p_framework
    ORDER BY i.priority DESC, i.created_at ASC
    LIMIT 1
    FOR UPDATE SKIP LOCKED;

    IF investigation_id IS NOT NULL THEN
        UPDATE investigations
        SET status = 'claimed', claimed_at = CURRENT_TIMESTAMP
        WHERE id = investigation_id;

        RETURN investigation_id;
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Calculate confidence score for a claim based on evidence
CREATE OR REPLACE FUNCTION calculate_claim_confidence(p_claim_id UUID)
RETURNS DECIMAL AS $$
DECLARE
    support_weight DECIMAL;
    challenge_weight DECIMAL;
    confidence DECIMAL;
BEGIN
    -- Weight evidence by credibility and relevance
    SELECT
        COALESCE(SUM(e.credibility_score * e.relevance_score), 0) INTO support_weight
    FROM evidence e
    JOIN findings f ON e.finding_id = f.id
    WHERE f.claim_id = p_claim_id AND f.finding_type = 'support';

    SELECT
        COALESCE(SUM(e.credibility_score * e.relevance_score), 0) INTO challenge_weight
    FROM evidence e
    JOIN findings f ON e.finding_id = f.id
    WHERE f.claim_id = p_claim_id AND f.finding_type = 'challenge';

    -- Confidence = support / (support + challenge), bounded 0-1
    IF (support_weight + challenge_weight) > 0 THEN
        confidence := support_weight / (support_weight + challenge_weight);
    ELSE
        confidence := 0.5;  -- No evidence = neutral
    END IF;

    UPDATE claims SET confidence_score = confidence WHERE id = p_claim_id;

    RETURN confidence;
END;
$$ LANGUAGE plpgsql;
```

## Agent Work Loop (Pull-Based)

```python
# agents/base_agent.py

import asyncio
from typing import Optional
from uuid import UUID
from enum import Enum

class AgentFramework(Enum):
    SUPPORT_EMPIRICAL = "support_empirical"
    SUPPORT_THEORETICAL = "support_theoretical"
    CHALLENGE_EMPIRICAL = "challenge_empirical"
    # ... etc

class BaseAgent:
    def __init__(self, framework: AgentFramework, db_connection):
        self.framework = framework
        self.db = db_connection
        self.agent_id = self.register()
        self.running = False

    def register(self) -> UUID:
        """Register this agent instance in the database"""
        result = self.db.execute("""
            INSERT INTO agents (framework, instance_name, status)
            VALUES (%s, %s, 'idle')
            RETURNING id
        """, (self.framework.value, f"{self.framework.value}_{uuid.uuid4().hex[:8]}"))
        return result[0]['id']

    async def run_forever(self):
        """Main agent loop - continuously pull and process work"""
        self.running = True

        while self.running:
            try:
                # 1. Get next available work from queue
                investigation_id = await self.get_next_work()

                if investigation_id is None:
                    # No work available, sleep and retry
                    await asyncio.sleep(30)  # Check every 30 seconds
                    continue

                # 2. Update agent status
                await self.update_status('working', investigation_id)

                # 3. Load claim data
                claim_data = await self.load_claim(investigation_id)

                # 4. Do the investigation work
                findings = await self.investigate(claim_data)

                # 5. Save findings to database
                await self.save_findings(investigation_id, findings)

                # 6. Mark investigation complete
                await self.complete_investigation(investigation_id)

                # 7. Update agent status back to idle
                await self.update_status('idle', None)

            except Exception as e:
                await self.handle_error(investigation_id, e)
                await asyncio.sleep(60)  # Back off on error

    async def get_next_work(self) -> Optional[UUID]:
        """Pull next investigation from work queue"""
        result = await self.db.execute("""
            SELECT get_next_work(%s)
        """, (self.framework.value,))

        return result[0]['get_next_work'] if result else None

    async def investigate(self, claim_data: dict) -> dict:
        """
        Framework-specific investigation logic.
        Subclasses override this.
        """
        raise NotImplementedError

    async def save_findings(self, investigation_id: UUID, findings: dict):
        """Save investigation findings to database"""
        # Insert finding
        finding_id = await self.db.execute("""
            INSERT INTO findings (
                investigation_id,
                claim_id,
                finding_type,
                summary,
                detailed_analysis,
                confidence,
                new_claims_text
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id
        """, (
            investigation_id,
            findings['claim_id'],
            findings['type'],
            findings['summary'],
            findings['analysis'],
            findings['confidence'],
            findings.get('new_claims', [])
        ))

        # Insert evidence with APA citations
        for evidence in findings['evidence']:
            await self.db.execute("""
                INSERT INTO evidence (
                    finding_id,
                    source_type,
                    source_category,
                    authors,
                    publication_year,
                    title,
                    citation_apa,
                    relevant_quote,
                    relevance_score,
                    credibility_score,
                    doi,
                    url
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                finding_id,
                evidence['source_type'],
                evidence['category'],  # 'academic' or 'web'
                evidence['authors'],
                evidence['year'],
                evidence['title'],
                evidence['apa_citation'],
                evidence['quote'],
                evidence['relevance'],
                evidence['credibility'],
                evidence.get('doi'),
                evidence.get('url')
            ))

        # Trigger will auto-spawn new claims from new_claims_text array
```

## Orchestrator System

```python
# orchestrator/work_scheduler.py

class WorkScheduler:
    """
    Creates investigation tasks and adds them to the work queue.
    Does NOT spawn agents - agents pull work themselves.
    """

    async def schedule_initial_investigations(self, claim_id: UUID):
        """
        When a new claim is added, schedule investigations for it.
        Creates investigation records that agents will discover.
        """
        frameworks_to_apply = [
            'support_empirical',
            'support_theoretical',
            'challenge_empirical',
            'challenge_methodological',
            'analysis_definitional'
        ]

        for framework in frameworks_to_apply:
            await self.db.execute("""
                INSERT INTO investigations (
                    claim_id,
                    agent_framework,
                    status,
                    priority
                ) VALUES (%s, %s, 'queued', %s)
            """, (claim_id, framework, self.calculate_priority(claim_id)))

    async def schedule_expansion_investigations(self):
        """
        Periodic job: Find claims that need more investigation.
        Called every hour by a background scheduler.
        """
        # Find claims with low investigation coverage
        underinvestigated = await self.db.execute("""
            SELECT id FROM claims
            WHERE investigation_count < 5
            AND status NOT IN ('archived')
            AND (
                support_count = 0 OR
                challenge_count = 0 OR
                neutral_count < 2
            )
            ORDER BY priority_score DESC
            LIMIT 100
        """)

        for claim in underinvestigated:
            await self.schedule_missing_investigations(claim['id'])

    async def schedule_discovery_pass(self):
        """
        Periodic job: Run discovery agents on high-value claims
        """
        high_value_claims = await self.db.execute("""
            SELECT c.id FROM claims c
            LEFT JOIN investigations i ON i.claim_id = c.id
                AND i.agent_framework LIKE 'discovery%'
            WHERE i.id IS NULL  -- Never had discovery investigation
            AND c.confidence_score > 0.7
            ORDER BY c.priority_score DESC
            LIMIT 50
        """)

        for claim in high_value_claims:
            for framework in ['discovery_lateral', 'discovery_emerging']:
                await self.create_investigation(claim['id'], framework)
```

## Background Process Manager

```python
# orchestrator/process_manager.py

import asyncio
from typing import List

class ProcessManager:
    """
    Manages the pool of autonomous agents running in background.
    Agents run indefinitely, pulling work from queue.
    """

    def __init__(self, config):
        self.config = config
        self.agents: List[BaseAgent] = []

    async def start_agent_pool(self):
        """
        Start configured number of each agent type.
        They run autonomously forever.
        """
        agent_pool_config = {
            AgentFramework.SUPPORT_EMPIRICAL: 3,        # 3 instances
            AgentFramework.SUPPORT_THEORETICAL: 2,
            AgentFramework.SUPPORT_CROSS_DOMAIN: 2,
            AgentFramework.CHALLENGE_EMPIRICAL: 3,
            AgentFramework.CHALLENGE_METHODOLOGICAL: 2,
            AgentFramework.CHALLENGE_ALTERNATIVE: 2,
            AgentFramework.ANALYSIS_HISTORICAL: 1,
            AgentFramework.ANALYSIS_DEFINITIONAL: 2,
            AgentFramework.ANALYSIS_SCOPE: 1,
            AgentFramework.DISCOVERY_LATERAL: 1,
            AgentFramework.DISCOVERY_EMERGING: 1
        }

        tasks = []
        for framework, count in agent_pool_config.items():
            for i in range(count):
                agent = self.create_agent(framework)
                self.agents.append(agent)
                tasks.append(asyncio.create_task(agent.run_forever()))

        # Also start periodic schedulers
        tasks.append(asyncio.create_task(self.run_expansion_scheduler()))
        tasks.append(asyncio.create_task(self.run_discovery_scheduler()))

        await asyncio.gather(*tasks)

    async def run_expansion_scheduler(self):
        """Run every hour to schedule expansion work"""
        scheduler = WorkScheduler(self.db)
        while True:
            await scheduler.schedule_expansion_investigations()
            await asyncio.sleep(3600)  # 1 hour

    async def run_discovery_scheduler(self):
        """Run every 6 hours to schedule discovery work"""
        scheduler = WorkScheduler(self.db)
        while True:
            await scheduler.schedule_discovery_pass()
            await asyncio.sleep(21600)  # 6 hours
```

## CLI Commands (Revised)

```bash
# Start the autonomous agent system (runs in background)
python research_agent.py start-agents --config config.yaml

# Ingest a research paper
python research_agent.py ingest paper.pdf --auto-extract-claims

# View work queue status
python research_agent.py queue-status
# Output:
# Work Queue Status:
# ==================
# Queued Investigations: 847
#   - support_empirical: 234
#   - challenge_empirical: 189
#   - discovery_lateral: 67
#   ...
#
# Active Investigations: 12
# Completed Today: 156

# View claim status
python research_agent.py claim-status --claim-id abc-123
# Output shows: investigations done, pending, findings, evidence count

# Generate report for a claim tree
python research_agent.py generate-report --claim-id abc-123 --format docx --output report.docx

# View investigation chain
python research_agent.py show-chain --claim-id abc-123 --depth 5

# Database statistics
python research_agent.py stats
# Output:
# Database Statistics:
# ===================
# Total Claims: 12,458
# Total Investigations: 45,234 (completed: 43,001)
# Total Evidence Items: 128,456
#   - Academic: 98,234 (76.5%)
#   - Web: 30,222 (23.5%)
# Average chain depth: 3.2
```

This architecture is:
- ✅ **Pull-based** - agents discover work, don't spawn recursively
- ✅ **PostgreSQL** - robust for scientific data with JSONB, vectors, full-text search
- ✅ **Dual-source** - academic (APA) and web sources tracked separately
- ✅ **Autonomous** - agents run forever in background
- ✅ **Scalable** - work queue pattern handles unlimited agents
- ✅ **Database-centric** - all state in DB, reports generated on-demand

Ready to start implementation?
