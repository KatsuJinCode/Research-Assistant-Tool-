# Neo4j Visualization Guide

## Quick Start - View Your Data

### 1. Open Neo4j Browser
Open http://localhost:7474 in your web browser

Login credentials:
- Username: `neo4j`
- Password: `research123`

---

## Visualization Queries

### Query 1: See the Full Hierarchical Tree

This shows Documents → Claims → SuperClaims with all relationships:

```cypher
MATCH (d:Document)-[:CONTAINS_CLAIM]->(c:Claim)
OPTIONAL MATCH (c)-[s:SIMILAR_TO]-(c2:Claim)
OPTIONAL MATCH (c)-[m:MERGED_INTO]->(sc:SuperClaim)
RETURN d, c, s, c2, m, sc
LIMIT 100
```

**What you'll see:**
- Document nodes (blue circles)
- Claim nodes (green circles) connected to Document
- SIMILAR_TO relationships showing which claims are related
- MERGED_INTO relationships showing how claims group into SuperClaims
- SuperClaim nodes (orange circles) representing the consolidated claims

---

### Query 2: Just SuperClaims and Their Members

This shows the claim reduction/grouping clearly:

```cypher
MATCH (sc:SuperClaim)<-[m:MERGED_INTO]-(c:Claim)
RETURN sc, m, c
```

**What you'll see:**
- 20 SuperClaim nodes
- 60 Claim nodes
- MERGED_INTO relationships showing which 3 claims merged into each SuperClaim

---

### Query 3: See One SuperClaim in Detail

Pick one SuperClaim and see all its merged claims:

```cypher
MATCH (sc:SuperClaim)<-[m:MERGED_INTO]-(c:Claim)
WHERE sc.member_count = 3
WITH sc, collect(c) as claims
RETURN sc.text as SuperClaim,
       sc.member_count as Members,
       [claim IN claims | claim.text] as OriginalClaims
LIMIT 1
```

**What you'll see:**
- The SuperClaim's normalized text
- All 3 original claim texts that were merged

---

### Query 4: Find Similar Claims Network

See which claims are similar to each other:

```cypher
MATCH (c1:Claim)-[s:SIMILAR_TO]-(c2:Claim)
WHERE s.score > 0.5
RETURN c1, s, c2
LIMIT 50
```

**What you'll see:**
- Claims connected by SIMILAR_TO relationships
- Similarity scores on the relationships
- Clusters of related claims

---

### Query 5: See Claims with Their Qualifiers

```cypher
MATCH (c:Claim)-[h:HAS_QUALIFIER]->(q:Qualifier)
RETURN c, h, q
LIMIT 30
```

**What you'll see:**
- Claim nodes
- Qualifier nodes showing modal/quantity/certainty qualifiers
- HAS_QUALIFIER relationships

---

### Query 6: Complete Overview (Everything)

```cypher
MATCH (d:Document)-[:CONTAINS_CLAIM]->(c:Claim)
OPTIONAL MATCH (c)-[:HAS_QUALIFIER]->(q:Qualifier)
OPTIONAL MATCH (c)-[:MERGED_INTO]->(sc:SuperClaim)
OPTIONAL MATCH (c)-[:SIMILAR_TO]-(c2:Claim)
RETURN d, c, q, sc, c2
LIMIT 100
```

**What you'll see:**
- Complete knowledge graph structure
- All node types and relationships
- Full hierarchical tree

---

## Graph Statistics

Current graph contains:

- **161 total nodes**
  - 3 Document nodes
  - 60 Claim nodes
  - 78 Qualifier nodes
  - 20 SuperClaim nodes

- **258 total relationships**
  - 60 CONTAINS_CLAIM (Document → Claim)
  - 78 HAS_QUALIFIER (Claim → Qualifier)
  - 60 SIMILAR_TO (Claim ↔ Claim)
  - 60 MERGED_INTO (Claim → SuperClaim)

---

## Customizing the Visualization

### Change Node Colors

1. Click on any node type in the top left (e.g., "SuperClaim")
2. Click the color picker
3. Choose a new color

### Change Node Size

1. Click on node type
2. Adjust "Size" slider
3. Or set size based on property (e.g., member_count)

### Add Labels to Nodes

1. Click on node type
2. Under "Caption", select which property to display
3. Recommended:
   - Document: `title`
   - Claim: `text` (first 50 chars)
   - SuperClaim: `text` (first 50 chars)
   - Qualifier: `type`

### Relationship Labels

1. Click on relationship type
2. Under "Caption", select property to show
3. Recommended:
   - SIMILAR_TO: `score`
   - MERGED_INTO: (no label)

---

## Understanding the Hierarchy

### How Claim Reduction Works

1. **Claim Extraction**: 60 claims extracted from PDF
2. **Similarity Analysis**: Each claim compared to all others
3. **Clustering**: Claims with 50%+ similarity grouped together
4. **SuperClaim Creation**: Each cluster of 3 claims → 1 SuperClaim
5. **Result**: 60 claims reduced to 20 SuperClaims (3:1 ratio)

### Example

**Original 3 Claims** (similar but not identical):
1. "Mental illness is not a disease of the brain, but a problem in living"
2. "Mental illness is not literally a 'thing' but rather a problem in living"
3. "Mental illness is a problem in living, not a physicochemical process"

**Merged into 1 SuperClaim:**
"Mental illness is not literally a 'thing' but rather a problem in living"

This SuperClaim represents all 3 claims while preserving the core meaning.

---

## Next Steps: Adding Evidence Relationships

To build a complete hierarchical tree with supporting/contradicting evidence, you can add:

### 1. Research Evidence Nodes

```cypher
CREATE (e:Evidence {
  id: 'uuid',
  text: 'Research finding text',
  source: 'arXiv paper title',
  url: 'https://arxiv.org/...'
})
```

### 2. SUPPORTS Relationship

```cypher
MATCH (e:Evidence {id: 'evidence-uuid'})
MATCH (sc:SuperClaim {id: 'superclaim-uuid'})
CREATE (e)-[:SUPPORTS {strength: 0.8}]->(sc)
```

### 3. CONTRADICTS Relationship

```cypher
MATCH (e:Evidence {id: 'evidence-uuid'})
MATCH (sc:SuperClaim {id: 'superclaim-uuid'})
CREATE (e)-[:CONTRADICTS {strength: 0.9}]->(sc)
```

### 4. Agent Research Results

```cypher
CREATE (r:ResearchResult {
  id: 'uuid',
  agent_name: 'Investigation Agent 1',
  findings: 'Detailed findings text',
  confidence: 0.85,
  timestamp: '2025-01-16T10:30:00Z'
})

MATCH (r:ResearchResult {id: 'result-uuid'})
MATCH (sc:SuperClaim {id: 'superclaim-uuid'})
CREATE (r)-[:INVESTIGATES]->(sc)
```

---

## Exporting Visualizations

### Export as PNG

1. Run your query
2. Click the download icon in top right
3. Select "PNG"
4. Save image

### Export as SVG (Vector Graphics)

1. Run query
2. Click download icon
3. Select "SVG"
4. Save for editing in design tools

### Export Graph Data

```cypher
// Export to JSON format
MATCH (n)
OPTIONAL MATCH (n)-[r]->(m)
RETURN n, r, m
```

Copy results and save as JSON.

---

## Tips for Large Graphs

If you have hundreds of claims:

1. **Use LIMIT**: Always add `LIMIT 100` to queries
2. **Filter by Properties**: Add `WHERE` clauses
   ```cypher
   WHERE sc.confidence > 0.7
   ```
3. **Focus on Clusters**: View one SuperClaim at a time
4. **Use Paths**: Show specific paths through the graph
   ```cypher
   MATCH path = (d:Document)-[*1..3]-(sc:SuperClaim)
   RETURN path
   LIMIT 10
   ```

---

## Troubleshooting

### Graph looks messy
- Add `LIMIT` to show fewer nodes
- Use "Force-directed" layout (drag nodes to organize)
- Filter to specific node types

### Can't see relationship labels
- Click on relationship type in top left
- Select "Caption" property
- Adjust "Size" if text too small

### Nodes overlap
- Click and drag nodes to separate them
- Use mouse wheel to zoom in/out
- Right-click + drag to pan

---

## Running the Hierarchy Builder

If you process new documents and want to rebuild the hierarchy:

```bash
python build_claim_hierarchy.py
```

This will:
1. Analyze all claims in Neo4j
2. Find similar claims
3. Create SuperClaim clusters
4. Build hierarchical relationships

You can adjust similarity thresholds in the script.

---

**Your hierarchical tree is ready to explore!**

Open http://localhost:7474 and start with Query 2 to see the claim reduction clearly.
