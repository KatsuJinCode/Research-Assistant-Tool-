# Neo4j Graph Navigation Guide

## Vision: Navigable Research Graph

You want to see:
1. **Top-level claims** as root nodes
2. **Sub-claims** expanding from each root
3. **Click any claim** → See where exact wording appears
4. **Evidence & sources** connected to claims
5. **Research results** from agents investigating claims
6. **Rich, growing graph** as research progresses

## Using Neo4j Browser

### Access
1. Open: http://localhost:7474
2. Login: neo4j / research123

### Current Graph Views

#### 1. See All Top-Level (Root) Claims
```cypher
MATCH (c:Claim)
WHERE c.is_optimal = true
  AND NOT ()-[:PARENT_OF]->(c)
RETURN c
LIMIT 25
```

**What you see**: Root nodes (blue circles) representing the most general claims

**Click any node**: Shows its properties (text, specificity, etc.)

---

#### 2. Expand Full Hierarchy from a Root Claim
```cypher
MATCH path = (root:Claim)-[:PARENT_OF*]->(child:Claim)
WHERE root.is_optimal = true
  AND NOT ()-[:PARENT_OF]->(root)
RETURN path
LIMIT 100
```

**What you see**: Tree structure with root → child → grandchild relationships

**Interact**: Click any node to see its text and properties

---

#### 3. See a Specific Claim and ALL Its Connections
```cypher
MATCH (c:Claim {text: "Mental illness is not literally a 'thing'"})
OPTIONAL MATCH (c)-[r]-(connected)
RETURN c, r, connected
```

**What you see**:
- Center node: The claim
- Connected nodes: Parent claims, child claims, supporting claims, documents, qualifiers

**Click**: Any connected node to explore further

---

#### 4. Find Where Exact Wording Appears (Future Feature)
```cypher
// This will work once we add Sentence nodes
MATCH (claim:Claim)
WHERE claim.text CONTAINS "mental illness"
MATCH (claim)-[:EXTRACTED_FROM]->(sentence:Sentence)
MATCH (sentence)-[:IN_DOCUMENT]->(doc:Document)
RETURN claim, sentence, doc
```

**What you see**: Claim → Sentences containing it → Source documents

---

#### 5. Navigate the Full Research Graph
```cypher
MATCH (c:Claim)
WHERE c.is_optimal = true
OPTIONAL MATCH (c)-[r:PARENT_OF|SUPPORTS|OVERLAPS]-(other:Claim)
OPTIONAL MATCH (c)-[:HAS_QUALIFIER]->(q:Qualifier)
OPTIONAL MATCH (c)<-[:CONTAINS_CLAIM]-(doc:Document)
RETURN c, r, other, q, doc
LIMIT 50
```

**What you see**: Rich graph with:
- Claims (nodes)
- Relationships (arrows): PARENT_OF, SUPPORTS, OVERLAPS
- Qualifiers (small nodes): may, might, all, some
- Source documents (document icons)

---

## Interactive Navigation

### 1. Expand a Node
- **Click a node** → See its properties
- **Double-click a node** → Expand its connections
- **Right-click → Expand** → Choose relationship type to expand

### 2. Filter by Relationship
In the sidebar:
- **Relationship types**: Toggle PARENT_OF, SUPPORTS, etc.
- Shows/hides specific relationship arrows

### 3. Search for Text
Top search bar:
- Type keywords (e.g., "mental illness")
- Shows matching claims

### 4. Visual Styling
Bottom controls:
- **Size**: By specificity, qualifier count, etc.
- **Color**: By claim strength, project, etc.
- **Caption**: What to display on nodes

---

## Future Enhancements (Roadmap)

### 1. Sentence-Level Tracking
```cypher
CREATE (s:Sentence {
    text: "Mental illness is not literally a 'thing'...",
    page: 5,
    line: 12
})
CREATE (s)-[:IN_DOCUMENT]->(doc:Document)
CREATE (claim)-[:EXTRACTED_FROM]->(s)
```

**Benefit**: Click claim → See exact location in source

---

### 2. Evidence Integration
```cypher
CREATE (e:Evidence {
    type: 'research_paper',
    title: 'Study of Mental Illness Classifications',
    url: 'https://...'
})
CREATE (e)-[:SUPPORTS {strength: 0.9}]->(claim)
```

**Benefit**: See which evidence supports/contradicts each claim

---

### 3. Agent Research Tracking
```cypher
CREATE (r:ResearchResult {
    agent: 'Agent-1',
    findings: '...',
    timestamp: '...'
})
CREATE (r)-[:INVESTIGATES]->(claim)
CREATE (r)-[:FOUND_EVIDENCE]->(evidence)
```

**Benefit**: Track which agent researched what, when

---

### 4. Counter-Claims
```cypher
CREATE (counter_claim:Claim {text: '...'})
CREATE (counter_claim)-[:CONTRADICTS {strength: 0.8}]->(original_claim)
```

**Benefit**: See conflicting claims connected in graph

---

### 5. Citation Network
```cypher
CREATE (claim1)-[:CITES]->(claim2)
CREATE (claim1)-[:CITED_IN {location: 'page 5'}]->(doc)
```

**Benefit**: See how claims reference each other

---

## Current Graph Structure

### Nodes
- **Claim** (40 nodes): Individual assertions
  - Properties: text, specificity_score, is_optimal, is_redundant
- **Qualifier** (34 nodes): Modal/quantity/certainty markers
  - Properties: type, text, impact
- **Document** (2 nodes): Source papers
  - Properties: title, author, page_count

### Relationships
- **PARENT_OF** (69): General claim → Specific claim
- **SUPPORTS** (292): Claim → Claim (evidence)
- **OVERLAPS** (192): Claim → Claim (similarity)
- **REFINES** (153): Claim → Claim (more specific version)
- **CONTAINS_CLAIM** (40): Document → Claim
- **HAS_QUALIFIER** (34): Claim → Qualifier

---

## Tips for Exploration

1. **Start with roots**: Run query #1 to see top-level claims
2. **Expand one root**: Double-click a root to see its children
3. **Filter relationships**: Hide OVERLAPS to reduce clutter
4. **Search**: Find claims by keyword
5. **Export subgraph**: Right-click → Export → JSON/CSV

---

## Customization

### Change Node Colors
```cypher
// Color by specificity
MATCH (c:Claim)
RETURN c,
  CASE
    WHEN c.specificity_score < 0.4 THEN 'blue'   // General
    WHEN c.specificity_score < 0.7 THEN 'orange' // Medium
    ELSE 'purple'                                 // Specific
  END as color
```

### Change Node Size
```cypher
// Size by number of connections
MATCH (c:Claim)
OPTIONAL MATCH (c)-[r]-()
WITH c, count(r) as connections
RETURN c, connections
```

---

## Next Steps

To make this truly navigable, we need to add:

1. **Sentence nodes** - Track exact locations
2. **Source attribution** - Link claims to documents/pages
3. **Evidence nodes** - External research papers
4. **Agent tracking** - Which agent researched what
5. **Citation links** - How claims reference each other

See: `FEATURE_ROADMAP.md` for implementation plan.

---

**Current State**: Foundation is built (claims, hierarchy, relationships)
**Next Phase**: Add sentence tracking and source attribution
**Goal**: Rich, navigable research graph
