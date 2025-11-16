-- ============================================================================
-- Research Verification Agent System - MVP Database Schema
-- Version: 1.0 (MVP)
-- PostgreSQL 15+ with extensions
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- UUID generation
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- Fuzzy text search
CREATE EXTENSION IF NOT EXISTS "vector";         -- pgvector for embeddings
CREATE EXTENSION IF NOT EXISTS "ltree";          -- Hierarchical data

-- ============================================================================
-- DOCUMENTS
-- ============================================================================

CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title TEXT NOT NULL,
    source_type VARCHAR(50) NOT NULL,
    file_path TEXT,
    full_text TEXT,
    metadata JSONB,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_source_type CHECK (source_type IN ('pdf', 'docx', 'txt', 'url'))
);

CREATE INDEX idx_documents_source_type ON documents(source_type);

-- ============================================================================
-- CLAIMS (simplified for MVP)
-- ============================================================================

CREATE TABLE claims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_document_id UUID REFERENCES documents(id) ON DELETE CASCADE,
    parent_claim_id UUID REFERENCES claims(id) ON DELETE SET NULL,

    -- Claim content
    original_text TEXT NOT NULL,
    normalized_text TEXT,  -- NULL until normalized

    -- Status tracking
    status VARCHAR(50) DEFAULT 'extracted',
    confidence_score DECIMAL(3,2),
    priority_score INT DEFAULT 50,

    -- Investigation tracking
    investigation_count INT DEFAULT 0,
    support_count INT DEFAULT 0,
    challenge_count INT DEFAULT 0,
    neutral_count INT DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_investigated_at TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT confidence_range CHECK (confidence_score BETWEEN 0.00 AND 1.00 OR confidence_score IS NULL),
    CONSTRAINT valid_status CHECK (status IN ('extracted', 'queued', 'investigating', 'supported', 'challenged', 'verified', 'uncertain', 'archived'))
);

CREATE INDEX idx_claims_status ON claims(status);
CREATE INDEX idx_claims_priority ON claims(priority_score DESC) WHERE status IN ('queued', 'extracted');
CREATE INDEX idx_claims_parent ON claims(parent_claim_id) WHERE parent_claim_id IS NOT NULL;
CREATE INDEX idx_claims_document ON claims(source_document_id);

-- ============================================================================
-- CLAIM QUALIFIERS (CRITICAL - Preserve modals, quantifiers, etc.)
-- ============================================================================

CREATE TABLE claim_qualifiers (
    claim_id UUID REFERENCES claims(id) ON DELETE CASCADE,
    qualifier_type VARCHAR(50) NOT NULL,  -- 'modal', 'frequency', 'quantity', 'certainty', 'temporal'
    qualifier_text VARCHAR(50) NOT NULL,  -- The actual word: 'can', 'mostly', 'all', etc.
    semantic_impact TEXT,                 -- 'indicates_possibility', 'indicates_certainty', etc.

    PRIMARY KEY (claim_id, qualifier_type, qualifier_text)
);

CREATE INDEX idx_qualifiers_claim ON claim_qualifiers(claim_id);
CREATE INDEX idx_qualifiers_type ON claim_qualifiers(qualifier_type);

-- ============================================================================
-- AGENTS
-- ============================================================================

CREATE TABLE agents (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    framework VARCHAR(50) NOT NULL,
    instance_name VARCHAR(100) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'idle',

    -- Performance metrics
    investigations_completed INT DEFAULT 0,
    average_duration_seconds DECIMAL(10,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active_at TIMESTAMP,
    last_error TEXT,

    CONSTRAINT valid_agent_status CHECK (status IN ('idle', 'working', 'paused', 'failed')),
    CONSTRAINT valid_framework CHECK (framework IN (
        'support_empirical', 'challenge_empirical', 'analysis_definitional'
    ))
);

CREATE INDEX idx_agents_status ON agents(status);
CREATE INDEX idx_agents_framework ON agents(framework);

-- ============================================================================
-- INVESTIGATIONS (Work Queue)
-- ============================================================================

CREATE TABLE investigations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,
    agent_id UUID REFERENCES agents(id) ON DELETE SET NULL,
    agent_framework VARCHAR(50) NOT NULL,

    -- Work assignment
    status VARCHAR(20) DEFAULT 'queued',
    priority INT DEFAULT 50,
    claimed_at TIMESTAMP,

    -- Execution
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    duration_seconds INT,

    -- Results
    findings_count INT DEFAULT 0,
    evidence_count INT DEFAULT 0,

    -- Error handling
    error_message TEXT,
    retry_count INT DEFAULT 0,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_investigation_status CHECK (status IN ('queued', 'claimed', 'in_progress', 'completed', 'failed', 'timeout'))
);

CREATE INDEX idx_investigations_claim ON investigations(claim_id);
CREATE INDEX idx_investigations_status ON investigations(status);
CREATE INDEX idx_investigations_priority ON investigations(priority DESC, created_at ASC) WHERE status = 'queued';
CREATE INDEX idx_investigations_agent ON investigations(agent_id) WHERE agent_id IS NOT NULL;

-- ============================================================================
-- FINDINGS (Agent Results)
-- ============================================================================

CREATE TABLE findings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    investigation_id UUID NOT NULL REFERENCES investigations(id) ON DELETE CASCADE,
    claim_id UUID NOT NULL REFERENCES claims(id) ON DELETE CASCADE,

    finding_type VARCHAR(20) NOT NULL,  -- 'support', 'challenge', 'neutral'
    summary TEXT NOT NULL,
    detailed_analysis TEXT,
    confidence DECIMAL(3,2),            -- Agent's confidence in this finding

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_finding_type CHECK (finding_type IN ('support', 'challenge', 'neutral', 'clarification')),
    CONSTRAINT confidence_range CHECK (confidence BETWEEN 0.00 AND 1.00 OR confidence IS NULL)
);

CREATE INDEX idx_findings_investigation ON findings(investigation_id);
CREATE INDEX idx_findings_claim ON findings(claim_id);
CREATE INDEX idx_findings_type ON findings(finding_type);

-- ============================================================================
-- EVIDENCE (With APA Citations)
-- ============================================================================

CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    finding_id UUID NOT NULL REFERENCES findings(id) ON DELETE CASCADE,

    -- Source identification
    source_category VARCHAR(20) NOT NULL,  -- 'academic' or 'web'
    citation_apa TEXT NOT NULL,

    -- Content
    relevant_quote TEXT,

    -- Quality scores
    relevance_score DECIMAL(3,2),
    credibility_score DECIMAL(3,2),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT valid_category CHECK (source_category IN ('academic', 'web')),
    CONSTRAINT relevance_range CHECK (relevance_score BETWEEN 0.00 AND 1.00 OR relevance_score IS NULL),
    CONSTRAINT credibility_range CHECK (credibility_score BETWEEN 0.00 AND 1.00 OR credibility_score IS NULL)
);

CREATE INDEX idx_evidence_finding ON evidence(finding_id);
CREATE INDEX idx_evidence_category ON evidence(source_category);

-- ============================================================================
-- NORMALIZATION VALIDATIONS (Human-in-the-Loop)
-- ============================================================================

CREATE TABLE normalization_validations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    claim_id UUID REFERENCES claims(id) ON DELETE CASCADE,
    original_text TEXT NOT NULL,
    proposed_normalized TEXT NOT NULL,
    confidence DECIMAL(3,2),

    -- Human review
    status VARCHAR(20) DEFAULT 'pending',  -- 'pending', 'approved', 'edited', 'rejected'
    user_corrected_text TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_at TIMESTAMP,

    CONSTRAINT valid_validation_status CHECK (status IN ('pending', 'approved', 'edited', 'rejected')),
    CONSTRAINT confidence_range CHECK (confidence BETWEEN 0.00 AND 1.00 OR confidence IS NULL)
);

CREATE INDEX idx_normalizations_claim ON normalization_validations(claim_id);
CREATE INDEX idx_normalizations_status ON normalization_validations(status);
CREATE INDEX idx_normalizations_pending ON normalization_validations(created_at) WHERE status = 'pending';

-- ============================================================================
-- TRIGGERS & AUTOMATION
-- ============================================================================

-- Auto-update claim statistics when findings are added
CREATE OR REPLACE FUNCTION update_claim_statistics()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE claims
    SET
        support_count = (SELECT COUNT(*) FROM findings WHERE claim_id = NEW.claim_id AND finding_type = 'support'),
        challenge_count = (SELECT COUNT(*) FROM findings WHERE claim_id = NEW.claim_id AND finding_type = 'challenge'),
        neutral_count = (SELECT COUNT(*) FROM findings WHERE claim_id = NEW.claim_id AND finding_type IN ('neutral', 'clarification')),
        investigation_count = (SELECT COUNT(*) FROM investigations WHERE claim_id = NEW.claim_id AND status = 'completed'),
        last_investigated_at = CURRENT_TIMESTAMP,
        updated_at = CURRENT_TIMESTAMP
    WHERE id = NEW.claim_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_claim_statistics
AFTER INSERT ON findings
FOR EACH ROW
EXECUTE FUNCTION update_claim_statistics();

-- Auto-update investigation statistics
CREATE OR REPLACE FUNCTION update_investigation_statistics()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE investigations
    SET
        findings_count = (SELECT COUNT(*) FROM findings WHERE investigation_id = NEW.investigation_id),
        evidence_count = (SELECT COUNT(*) FROM evidence e JOIN findings f ON e.finding_id = f.id WHERE f.investigation_id = NEW.investigation_id)
    WHERE id = NEW.investigation_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_investigation_statistics
AFTER INSERT ON findings
FOR EACH ROW
EXECUTE FUNCTION update_investigation_statistics();

-- ============================================================================
-- HELPER FUNCTIONS
-- ============================================================================

-- Get next available work for an agent framework
CREATE OR REPLACE FUNCTION get_next_work(p_framework VARCHAR)
RETURNS UUID AS $$
DECLARE
    investigation_id UUID;
BEGIN
    -- Find highest priority unclaimed investigation matching framework
    UPDATE investigations
    SET
        status = 'claimed',
        claimed_at = CURRENT_TIMESTAMP
    WHERE id = (
        SELECT id
        FROM investigations
        WHERE status = 'queued'
          AND agent_framework = p_framework
        ORDER BY priority DESC, created_at ASC
        LIMIT 1
        FOR UPDATE SKIP LOCKED
    )
    RETURNING id INTO investigation_id;

    RETURN investigation_id;
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
    SELECT COALESCE(SUM(e.credibility_score * e.relevance_score), 0)
    INTO support_weight
    FROM evidence e
    JOIN findings f ON e.finding_id = f.id
    WHERE f.claim_id = p_claim_id AND f.finding_type = 'support';

    SELECT COALESCE(SUM(e.credibility_score * e.relevance_score), 0)
    INTO challenge_weight
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

-- ============================================================================
-- VIEWS FOR WORK QUEUES
-- ============================================================================

-- Unverified claims needing support investigation
CREATE VIEW unverified_claims AS
SELECT
    c.*,
    c.priority_score + (EXTRACT(EPOCH FROM (NOW() - c.created_at))/3600)::INT AS dynamic_priority
FROM claims c
WHERE c.status IN ('extracted', 'queued')
  AND c.support_count = 0
ORDER BY dynamic_priority DESC;

-- Unchallenged claims needing challenge investigation
CREATE VIEW unchallenged_claims AS
SELECT
    c.*,
    c.priority_score + (EXTRACT(EPOCH FROM (NOW() - c.created_at))/3600)::INT AS dynamic_priority
FROM claims c
WHERE c.status IN ('supported', 'queued')
  AND c.challenge_count = 0
ORDER BY dynamic_priority DESC;

-- ============================================================================
-- INITIAL DATA
-- ============================================================================

-- No initial data for MVP
