# Feature Roadmap - Research Assistant Tool

## User Requirements (from latest session)

### 1. Multi-Source Input Support
**Goal**: User can provide claims/documents from multiple sources

**Features**:
- [  ] **URL Support**: Load documents from web URLs
- [  ] **Multi-Format Support**: Handle PDF, TXT, DOCX, MD, HTML, etc.
- [  ] **Folder Processing**: Process entire directories of mixed file types
- [  ] **Manual Claim Input**: User can type individual claims directly
- [  ] **Text Paste Support**: Copy/paste text blocks for processing
- [  ] **Batch Processing**: Process multiple sources simultaneously
- [  ] **Source Tracking**: Track which source each claim came from

**Implementation Priority**: HIGH
**Estimated Effort**: 3-5 days
**Dependencies**: None

---

### 2. Text Extraction Quality Scoring
**Goal**: Rate extraction quality and warn user of potential issues

**Features**:
- [  ] **Extraction Integrity Checker**: Score 0-1 for extraction quality
- [  ] **Pre-Extraction Check**: Detect multi-column, rotated text, tables, images
- [  ] **Post-Extraction Validation**: Check for nonsense patterns
- [  ] **Warning System**: Alert user when extraction quality is low
- [  ] **Manual Review Flag**: Mark claims needing human review
- [  ] **Quality Metrics**:
  - [ ] Sentence coherence score
  - [ ] Grammar/syntax validation
  - [ ] Special character detection (encoding issues)
  - [ ] Line-break anomaly detection
  - [ ] Column-crossing detection

**Scoring Algorithm**:
```python
quality_score = {
    'coherence': 0.0-1.0,      # Sentence makes sense
    'grammar': 0.0-1.0,         # Grammatically correct
    'encoding': 0.0-1.0,        # No encoding artifacts
    'structure': 0.0-1.0,       # Proper document structure
    'overall': weighted_average
}
```

**Implementation Priority**: CRITICAL
**Estimated Effort**: 2-3 days
**Dependencies**: None

**Rationale**: This would have caught the column detection issue earlier!

---

### 3. Claim Integrity Validation
**Goal**: Ensure claims are meaningful after extraction

**Features**:
- [  ] **Claim Coherence Check**: Verify claim makes logical sense
- [  ] **Nonsense Detection**: Flag gibberish claims (like the column issue)
- [  ] **Semantic Validation**: Use embeddings to detect anomalies
- [  ] **Manual Review Queue**: Claims flagged for human verification
- [  ] **Auto-Fix Suggestions**: Suggest corrections for common issues
- [  ] **Quality Dashboard**: Show extraction/claim quality metrics

**Validation Checks**:
- Sentence structure (subject-verb-object)
- Qualifier presence (modal/quantity/certainty)
- Semantic embedding similarity to known good claims
- Character encoding issues
- Unusual punctuation patterns
- Mid-sentence topic changes (column crossing indicator)

**Implementation Priority**: HIGH
**Estimated Effort**: 2-3 days
**Dependencies**: Text Extraction Quality Scoring

---

### 4. Project Management System
**Goal**: Organize claims into projects and manage workflows

**Features**:
- [  ] **Project Creation**: Create named projects (e.g., "AI Ethics Research")
- [  ] **Project Assignment**: Add claims to specific projects
- [  ] **Multi-Project Support**: Single claim can belong to multiple projects
- [  ] **Project Views**: Filter Neo4j view by project
- [  ] **Project Metadata**:
  - [ ] Project name
  - [ ] Description
  - [ ] Creation date
  - [ ] Owner/researchers
  - [ ] Tags/categories
- [  ] **Project Dashboard**: Stats per project

**Database Schema Addition**:
```cypher
CREATE (p:Project {
    id: 'uuid',
    name: 'Project Name',
    description: '...',
    created_at: '...'
})
CREATE (c:Claim)-[:BELONGS_TO]->(p:Project)
```

**Implementation Priority**: MEDIUM
**Estimated Effort**: 2-3 days
**Dependencies**: None

---

### 5. Enhanced Neo4j Visualization
**Goal**: Custom dashboard with maximum user control

**Features**:
- [  ] **Custom View Builder**: User defines what to show/hide
- [  ] **Highlighting System**: Highlight important claims
- [  ] **Citation View**: Show where claims are cited/sourced
- [  ] **Source Tracking**: Display original document for each claim
- [  ] **Filtering Controls**:
  - [ ] Filter by project
  - [ ] Filter by source document
  - [ ] Filter by claim strength
  - [ ] Filter by qualifier type
  - [ ] Filter by specificity range
- [  ] **Interactive Controls**:
  - [ ] Zoom to claim
  - [ ] Expand/collapse hierarchy
  - [ ] Show/hide relationship types
  - [ ] Export subgraph
- [  ] **Visual Enhancements**:
  - [ ] Color-code by project
  - [ ] Size by importance
  - [ ] Highlight citations
  - [ ] Show evidence strength

**Saved Views**:
- Default view (optimal claims only)
- Full hierarchy view
- Evidence network view
- Source citation view
- Project comparison view
- Quality review view (flagged claims)

**Implementation Priority**: HIGH
**Estimated Effort**: 4-6 days
**Dependencies**: Project Management System

---

### 6. Source Attribution System
**Goal**: Track where each claim originates from

**Features**:
- [  ] **Source Node Type**: Documents, URLs, Manual Input
- [  ] **Citation Relationships**: Claim → Source
- [  ] **Page/Location Tracking**: Exact location in source
- [  ] **Multi-Source Claims**: Claim found in multiple sources
- [  ] **Source Metadata**:
  - [ ] File path or URL
  - [ ] Page number
  - [ ] Line number
  - [ ] Extraction timestamp
  - [ ] Extraction quality score
- [  ] **Citation View**: "Where is this claim cited?"

**Database Schema Addition**:
```cypher
CREATE (s:Source {
    type: 'pdf|url|manual|paste',
    location: 'path/url',
    title: '...'
})
CREATE (c:Claim)-[:EXTRACTED_FROM {
    page: 5,
    quality_score: 0.95,
    timestamp: '...'
}]->(s:Source)
```

**Implementation Priority**: HIGH
**Estimated Effort**: 2-3 days
**Dependencies**: Multi-Source Input Support

---

## Implementation Order

### Phase 1: Quality & Validation (CRITICAL)
1. Text Extraction Quality Scoring
2. Claim Integrity Validation

**Rationale**: Prevent the column detection issue from happening again. Build trust in extraction quality.

### Phase 2: Input Expansion
3. Multi-Source Input Support
4. Source Attribution System

**Rationale**: Make it easy to add claims from anywhere, track their origins.

### Phase 3: Organization & Visualization
5. Project Management System
6. Enhanced Neo4j Visualization

**Rationale**: Once we have quality data from multiple sources, organize and visualize it effectively.

---

## Success Criteria

### Phase 1 (Quality & Validation)
- [  ] No nonsense claims make it into the database
- [  ] User is warned before processing low-quality documents
- [  ] Extraction quality score is accurate (>90% precision)
- [  ] Manual review queue catches edge cases

### Phase 2 (Input Expansion)
- [  ] User can drag-and-drop any file type
- [  ] User can paste URL and it downloads/processes automatically
- [  ] Entire folders can be processed with one command
- [  ] Every claim has source attribution

### Phase 3 (Organization & Visualization)
- [  ] User can filter Neo4j view by project
- [  ] Custom views save and load
- [  ] Citation view shows all sources for a claim
- [  ] Dashboard shows project health (quality scores, claim counts, etc.)

---

## Technical Notes

### For Text Quality Scoring
- Use pre-trained models (e.g., perplexity-based coherence)
- Check for encoding issues (e.g., '�' characters)
- Detect column-crossing: sudden topic shifts mid-sentence
- Grammar check: use language-tool-python

### For Multi-Format Support
- PDF: pdfplumber (already have)
- DOCX: python-docx
- HTML: BeautifulSoup
- MD: markdown parser
- URL: requests + content-type detection

### For Neo4j Custom Views
- Use Neo4j Bloom (if available) for visual query builder
- Or build custom React/Vue dashboard with Neo4j driver
- Save view configs as JSON
- Load via Python script or web interface

---

## Open Questions

1. **Web Interface**: Should we build a web UI, or stay CLI-focused?
2. **Storage**: Should we store full text in Neo4j or separate file store?
3. **Collaboration**: Multi-user support needed?
4. **Export**: What formats? CSV, JSON, graph formats?

---

**Last Updated**: 2025-11-16
**Next Review**: After Phase 1 completion
