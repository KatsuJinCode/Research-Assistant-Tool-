# **Implementation Plan: Robust Multi-Document Research Graph**

**Last Updated**: 2025-11-18
**Purpose**: Migrate to production-ready schema supporting arbitrary depth, multiple documents, and complex investigations

---

## Phase 0: Pre-Implementation Assessment

### Current State Inventory

**Step 0.1**: Document what exists
```bash
# Run these queries in Neo4j to understand current state
```

```cypher
// Count current nodes
MATCH (n) RETURN labels(n) as type, count(*) as count

// Count current relationships
MATCH ()-[r]->() RETURN type(r) as rel_type, count(*) as count

// Check existing properties
MATCH (c:Claim) RETURN keys(c) LIMIT 1
MATCH (d:Document) RETURN keys(d) LIMIT 1
```

**Step 0.2**: Export current data (backup)
```bash
# Create backup before migration
python backup_neo4j.py
```

**Step 0.3**: List code files that interact with Neo4j
```bash
# Find all files
find . -name "*.py" -exec grep -l "neo4j\|Neo4j" {} \;
```

**Deliverable**:
- `CURRENT_STATE.md` - Documentation of existing schema
- `backup_YYYY-MM-DD.cypher` - Full database export
- `CODE_INVENTORY.md` - List of files to update

---

## Phase 1: Schema Design & Documentation (Week 1)

### 1.1 Create Schema Definition Files

**File**: `database/schema_v2_production.sql`
```sql
-- Complete schema definition with:
-- - All node types
-- - All relationship types
-- - Constraints
-- - Indexes
-- Comments explaining each element
```

**File**: `database/migration_v1_to_v2.cypher`
```cypher
-- Cypher statements to transform existing data
-- - Add new properties to existing nodes
-- - Create new node types
-- - Migrate relationships
-- - Create indexes
```

**File**: `docs/SCHEMA_V2_REFERENCE.md`
```markdown
# Visual diagrams
# Property descriptions
# Example queries
# Use cases for each relationship type
```

### 1.2 Design Migration Strategy

**File**: `database/migration_plan.md`

Key decisions:
- Backward compatibility: Keep old properties during transition?
- Rollback strategy: How to revert if migration fails?
- Downtime: Can we do zero-downtime migration?
- Data validation: How to verify migration success?

**Deliverable**:
- Complete schema files
- Migration strategy document
- Rollback plan

---

## Phase 2: Core Infrastructure (Week 2-3)

### 2.1 Enhanced Database Layer

**File**: `research_agent/neo4j_database_v2.py`

New methods needed:
```python
class Neo4jDatabaseV2:
    # Document operations
    def create_document(self, metadata: Dict) -> str
    def link_documents_by_author(self, author: str)
    def link_documents_by_field(self, field: str)
    def find_similar_documents(self, doc_id: str, threshold: float)

    # Claim operations (enhanced)
    def create_claim(self, claim_data: Dict, source_doc_id: str) -> str
    def add_claim_to_multiple_documents(self, claim_id: str, doc_ids: List[str])
    def find_claim_instances(self, canonical_claim_id: str)

    # Community operations (arbitrary depth)
    def create_community(self, level: int, parent_id: Optional[str]) -> str
    def assign_claim_to_community(self, claim_id: str, community_id: str)
    def get_community_hierarchy(self, root_community_id: str)
    def get_community_depth(self, community_id: str) -> int

    # Investigation operations
    def create_investigation(self, target_claim_id: str, inv_type: str,
                            parent_inv_id: Optional[str]) -> str
    def update_investigation_status(self, inv_id: str, status: str)
    def get_investigation_tree(self, root_inv_id: str)
    def get_investigation_depth(self, inv_id: str) -> int

    # Evidence operations
    def add_evidence(self, evidence_data: Dict, claim_id: str,
                    evidence_type: str) -> str
    def link_evidence_to_source(self, evidence_id: str, doc_id: str)

    # User operations
    def add_user_claim(self, user_id: str, claim_text: str,
                      linked_claim_id: Optional[str])
    def add_user_note(self, user_id: str, content: str, target_id: str)
    def create_user_link(self, user_id: str, from_id: str, to_id: str,
                        description: str)

    # Provenance tracking
    def get_provenance(self, node_id: str) -> Dict
    def get_audit_trail(self, node_id: str) -> List[Dict]

    # Traversal operations (arbitrary depth)
    def traverse_parent_hierarchy(self, claim_id: str, max_depth: Optional[int])
    def traverse_investigation_tree(self, inv_id: str, max_depth: Optional[int])
    def find_path_between_claims(self, claim_id_1: str, claim_id_2: str)
```

**Deliverable**:
- `neo4j_database_v2.py` with all methods
- Unit tests for each method
- API documentation

### 2.2 Migration Scripts

**File**: `database/migrate.py`

Steps:
```python
def migrate_to_v2():
    """Main migration orchestrator."""

    # 1. Validate current state
    validate_v1_schema()

    # 2. Create backup
    create_backup()

    # 3. Add new properties to existing nodes
    add_new_properties_to_claims()
    add_new_properties_to_documents()

    # 4. Create new node types
    create_investigation_nodes()
    create_evidence_nodes()
    create_research_question_nodes()

    # 5. Migrate relationships
    migrate_claim_relationships()
    add_provenance_relationships()

    # 6. Create indexes and constraints
    create_indexes()
    create_constraints()

    # 7. Validate migration
    validate_v2_schema()

    # 8. Test queries
    run_test_queries()

    print("✅ Migration complete!")
```

**File**: `database/rollback.py`
```python
def rollback_migration():
    """Rollback to v1 schema if needed."""
    restore_from_backup()
    remove_v2_additions()
    validate_v1_schema()
```

**Deliverable**:
- Migration script with progress logging
- Rollback script
- Validation tests

---

## Phase 3: Application Layer Updates (Week 4-5)

### 3.1 Update Existing Components

**Files to modify**:

1. **`research_agent/document_processing/pdf_extractor.py`**
   - Add document metadata extraction
   - Extract author, topic, field
   - Generate document embedding

2. **`research_agent/sentence_analyzer.py`**
   - Update to use v2 database layer
   - Add provenance tracking
   - Track extraction method

3. **`research_agent/claim_analysis/claim_space_optimizer.py`**
   - Support arbitrary depth communities
   - Add multi-level community detection
   - Track community hierarchy

4. **`build_optimal_hierarchy.py`**
   - Update to create arbitrary depth hierarchy
   - Add investigation tree building
   - Support parent_investigation tracking

### 3.2 New Components

**File**: `research_agent/document_clustering.py`
```python
class DocumentClusterer:
    """Cluster documents by author, topic, field."""

    def cluster_by_author(self)
    def cluster_by_field(self)
    def cluster_by_topic(self)
    def find_similar_documents(self, doc_id: str)
    def create_document_communities(self)
```

**File**: `research_agent/investigation_manager.py`
```python
class InvestigationManager:
    """Manage investigation trees."""

    def create_investigation(self, claim_id: str, inv_type: str)
    def spawn_child_investigation(self, parent_inv_id: str, target_claim_id: str)
    def get_investigation_depth(self, inv_id: str)
    def get_full_investigation_tree(self, root_inv_id: str)
    def update_investigation_progress(self, inv_id: str)
```

**File**: `research_agent/provenance_tracker.py`
```python
class ProvenanceTracker:
    """Track who added what, when, why."""

    def record_claim_creation(self, claim_id: str, source: str)
    def record_relationship_creation(self, rel_id: str, creator: str)
    def get_full_history(self, node_id: str)
    def get_audit_report(self, date_range: tuple)
```

**File**: `research_agent/user_interaction.py`
```python
class UserInteractionHandler:
    """Handle user-added content."""

    def add_user_claim(self, user_id: str, claim_text: str)
    def add_user_note(self, user_id: str, note: str, target_id: str)
    def create_custom_link(self, from_id: str, to_id: str, description: str)
    def flag_for_investigation(self, user_id: str, claim_id: str)
```

**Deliverable**:
- All files updated with v2 database calls
- New components implemented
- Integration tests

---

## Phase 4: Data Migration & Validation (Week 6)

### 4.1 Migrate Existing Data

**Script**: `scripts/migrate_existing_data.py`

Steps:
```python
# 1. Migrate documents
for doc in get_all_v1_documents():
    add_metadata(doc)
    generate_embedding(doc)
    extract_author_topic_field(doc)

# 2. Migrate claims
for claim in get_all_v1_claims():
    add_provenance(claim)
    add_extraction_method(claim)
    link_to_source_documents(claim)

# 3. Rebuild communities with new algorithm
rebuild_communities_arbitrary_depth()

# 4. Create investigation records for existing research
migrate_investigation_history()

# 5. Validate all data
validate_all_nodes()
validate_all_relationships()
```

### 4.2 Validation Tests

**File**: `tests/test_schema_v2.py`

Tests:
```python
def test_arbitrary_depth_hierarchy():
    """Test claims can have unlimited parent depth."""

def test_multiple_document_support():
    """Test same claim in multiple documents."""

def test_investigation_tree():
    """Test investigation spawning."""

def test_document_clustering():
    """Test documents cluster by author/topic/field."""

def test_user_additions():
    """Test user can add claims, notes, links."""

def test_provenance_tracking():
    """Test all additions tracked to source."""

def test_community_arbitrary_levels():
    """Test communities at any level."""
```

**Deliverable**:
- Migration script with logging
- 100+ validation tests
- Migration report

---

## Phase 5: API & Interface Updates (Week 7)

### 5.1 Update Web UI Backend

**File**: `web_ui/api_routes.py`

New endpoints:
```python
# Document management
POST   /api/documents              # Upload document
GET    /api/documents/{id}         # Get document
GET    /api/documents/{id}/claims  # Get all claims from document
GET    /api/documents/similar/{id} # Find similar documents

# Investigation management
POST   /api/investigations                    # Create investigation
POST   /api/investigations/{id}/spawn         # Spawn child investigation
GET    /api/investigations/{id}/tree          # Get full investigation tree
PUT    /api/investigations/{id}/status        # Update status

# User interactions
POST   /api/user/claims            # Add user claim
POST   /api/user/notes             # Add user note
POST   /api/user/links             # Create custom link
POST   /api/user/research-questions # Flag for investigation

# Provenance
GET    /api/provenance/{node_id}   # Get creation history
GET    /api/audit/{date_range}     # Get audit report

# Hierarchy traversal
GET    /api/claims/{id}/ancestors  # Get parent hierarchy
GET    /api/claims/{id}/descendants # Get child hierarchy
GET    /api/claims/{id}/path/{to_id} # Get path between claims
```

### 5.2 Update Web UI Frontend

**Files**:
- `web_ui/components/DocumentClusterView.tsx` - Show document groupings
- `web_ui/components/InvestigationTreeView.tsx` - Visualize investigation tree
- `web_ui/components/HierarchyExplorer.tsx` - Navigate arbitrary depth
- `web_ui/components/ProvenanceView.tsx` - Show audit trail
- `web_ui/components/UserAnnotationPanel.tsx` - Add notes/claims

**Deliverable**:
- API endpoints implemented
- Frontend components
- Integration tests

---

## Phase 6: Advanced Features (Week 8-9)

### 6.1 Intelligent Document Clustering

**File**: `research_agent/document_intelligence.py`

```python
class DocumentIntelligence:
    """Advanced document analysis."""

    def auto_extract_metadata(self, pdf_path: str) -> Dict:
        """Extract author, topic, field from PDF."""

    def generate_document_embedding(self, doc_text: str):
        """Create semantic document embedding."""

    def find_document_communities(self):
        """Cluster documents by similarity."""

    def suggest_related_documents(self, doc_id: str, n: int = 5):
        """Recommend related documents."""
```

### 6.2 Investigation Orchestration

**File**: `research_agent/investigation_orchestrator.py`

```python
class InvestigationOrchestrator:
    """Manage complex investigation workflows."""

    def plan_investigation(self, claim_id: str, depth: int) -> Dict:
        """Plan multi-level investigation."""

    def execute_investigation_plan(self, plan: Dict):
        """Execute planned investigation."""

    def auto_suggest_follow_ups(self, claim_id: str) -> List[str]:
        """Suggest potential investigations."""

    def prioritize_investigations(self, claim_ids: List[str]) -> List[str]:
        """Rank investigation importance."""
```

### 6.3 Query Optimization

**File**: `database/optimized_queries.cypher`

Pre-built queries for common operations:
```cypher
// Get full claim ancestry (optimized)
// Get investigation impact (claims discovered per investigation)
// Find claim clusters across documents
// Get document co-citation network
// Find orphaned claims (no parent)
// Get investigation bottlenecks
```

**Deliverable**:
- Advanced components implemented
- Optimized queries
- Performance benchmarks

---

## Phase 7: Testing & Optimization (Week 10)

### 7.1 Performance Testing

**Tests**:
- Load 100 documents (test document clustering)
- Extract 1000 claims (test hierarchy building)
- Create 50 investigation trees (test arbitrary depth)
- 10 concurrent users (test user additions)
- Query response times (all common queries < 1s)

### 7.2 Stress Testing

**Scenarios**:
- 10,000 claims in database
- 100-level deep investigation tree
- 50 documents by same author
- 1000 overlapping claims
- 100 concurrent agent operations

### 7.3 Optimization

**Tasks**:
- Add missing indexes
- Optimize slow queries
- Cache frequent operations
- Batch operations where possible

**Deliverable**:
- Performance test suite
- Stress test results
- Optimization report
- Benchmarks document

---

## Complete File Checklist

### Database Files
- [ ] `database/schema_v2_production.sql` - Schema definition
- [ ] `database/migration_v1_to_v2.cypher` - Migration statements
- [ ] `database/migration_plan.md` - Migration strategy
- [ ] `database/migrate.py` - Migration script
- [ ] `database/rollback.py` - Rollback script
- [ ] `database/optimized_queries.cypher` - Common queries
- [ ] `database/indexes.cypher` - Index definitions
- [ ] `database/constraints.cypher` - Constraint definitions

### Core Components
- [ ] `research_agent/neo4j_database_v2.py` - Enhanced database layer
- [ ] `research_agent/document_clustering.py` - Document clustering
- [ ] `research_agent/investigation_manager.py` - Investigation trees
- [ ] `research_agent/provenance_tracker.py` - Audit trail
- [ ] `research_agent/user_interaction.py` - User additions
- [ ] `research_agent/document_intelligence.py` - Advanced doc analysis
- [ ] `research_agent/investigation_orchestrator.py` - Investigation planning

### Updated Components
- [ ] `research_agent/document_processing/pdf_extractor.py` - Add metadata
- [ ] `research_agent/sentence_analyzer.py` - Use v2 DB
- [ ] `research_agent/claim_analysis/claim_space_optimizer.py` - Arbitrary depth
- [ ] `build_optimal_hierarchy.py` - Support v2 schema

### Scripts
- [ ] `scripts/migrate_existing_data.py` - Data migration
- [ ] `scripts/backup_neo4j.py` - Backup utility
- [ ] `scripts/validate_migration.py` - Validation
- [ ] `scripts/generate_test_data.py` - Test data creation

### Tests
- [ ] `tests/test_schema_v2.py` - Schema tests
- [ ] `tests/test_arbitrary_depth.py` - Depth tests
- [ ] `tests/test_multi_document.py` - Multi-doc tests
- [ ] `tests/test_investigation_tree.py` - Investigation tests
- [ ] `tests/test_user_interaction.py` - User feature tests
- [ ] `tests/test_performance.py` - Performance tests
- [ ] `tests/test_integration_v2.py` - Integration tests

### API & UI
- [ ] `web_ui/api_routes.py` - API endpoints
- [ ] `web_ui/components/DocumentClusterView.tsx`
- [ ] `web_ui/components/InvestigationTreeView.tsx`
- [ ] `web_ui/components/HierarchyExplorer.tsx`
- [ ] `web_ui/components/ProvenanceView.tsx`
- [ ] `web_ui/components/UserAnnotationPanel.tsx`

### Documentation
- [ ] `docs/SCHEMA_V2_REFERENCE.md` - Schema documentation
- [ ] `docs/API_V2_REFERENCE.md` - API documentation
- [ ] `docs/MIGRATION_GUIDE.md` - Migration guide
- [ ] `docs/USER_GUIDE.md` - User features guide
- [ ] `CURRENT_STATE.md` - Pre-migration state
- [ ] `CODE_INVENTORY.md` - Files needing updates

---

## Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| 0. Assessment | 2 days | Current state docs, backup |
| 1. Schema Design | 1 week | Schema files, migration plan |
| 2. Infrastructure | 2 weeks | Enhanced DB layer, migration scripts |
| 3. Application Updates | 2 weeks | Updated components, new features |
| 4. Data Migration | 1 week | Migrated data, validation |
| 5. API/UI | 1 week | Updated interfaces |
| 6. Advanced Features | 2 weeks | Intelligence, orchestration |
| 7. Testing | 1 week | Performance, stress tests |
| **Total** | **10 weeks** | **Production-ready system** |

---

## Risk Mitigation

### Risk 1: Data Loss During Migration
**Mitigation**:
- Full backup before migration
- Staged migration (documents → claims → relationships)
- Validation after each stage
- Rollback script ready

### Risk 2: Performance Degradation
**Mitigation**:
- Index all foreign keys
- Optimize queries before deployment
- Performance testing with 10x expected data
- Caching strategy

### Risk 3: Breaking Existing Functionality
**Mitigation**:
- Keep v1 database layer during transition
- Feature flags for v2 features
- Gradual rollout
- Extensive integration tests

### Risk 4: Complex Queries Too Slow
**Mitigation**:
- Pre-compute expensive operations
- Materialized views for common queries
- Query timeout limits
- Pagination for large result sets

---

## Success Criteria

### Must Have (Week 10)
- [ ] All existing data migrated successfully
- [ ] Zero data loss
- [ ] All v1 features working
- [ ] Arbitrary depth hierarchy working
- [ ] Multi-document support working
- [ ] Investigation trees working
- [ ] User additions working
- [ ] Provenance tracking working
- [ ] All tests passing
- [ ] Query performance < 2s

### Nice to Have (Post-launch)
- [ ] Advanced document clustering
- [ ] Investigation auto-suggestions
- [ ] Real-time collaboration
- [ ] Advanced visualizations

---

## Next Steps

**Immediate (This Week)**:
1. [ ] Review this plan
2. [ ] Run Phase 0 assessment
3. [ ] Create backup of current database
4. [ ] Document current state

**Week 1**:
1. [ ] Design schema files
2. [ ] Write migration strategy
3. [ ] Get approval on approach

Ready to start Phase 0?
