# Database Research Findings for Claim Verification System

## Research Question
What database technologies do state-of-the-art research claim verification and knowledge graph systems use?

## Key Findings

### 1. Open Research Knowledge Graph (ORKG)
**Purpose**: Infrastructure for representing, curating and exploring scholarly knowledge in machine-actionable manner

**Technology Stack**:
- **Database**: Neo4j Labeled Property Graph (LPG)
- **Backend**: Kotlin with Spring Boot 2
- **Data Access**: Spring Data Neo4j's Object Graph Mapper (OGM)
- **Query Language**: Cypher (Neo4j's native query language)
- **API**: JSON RESTful API

**Data Model**:
- Graph-based model centered around "statements" (triples)
- Similar to RDF: two nodes (resources) connected by directed edge
- Designed specifically for scholarly knowledge relationships

**Source**: arXiv paper "Open Research Knowledge Graph: Next Generation" (1901.10816)

---

### 2. Microsoft Academic Knowledge Graph (MAKG)
**Purpose**: Organize scholarly activities and entities

**Technology Stack**:
- **Format**: RDF (Resource Description Framework)
- **Scale**: 8+ billion triples
- **Graph Type**: Heterogeneous entity graph

**Data Model**:
- 6 core entity types: field of study, author, institution, paper, venue, event
- Nodes represent entities, edges represent relationships
- Uses linked data standards

**Key Insight**: One of the largest scholarly knowledge graphs, demonstrates RDF can scale to billions of triples

---

### 3. Semantic Scholar Academic Graph (S2AG)
**Purpose**: Largest open scientific literature graph

**Technology Stack**:
- **Graph database** for relationships
- AI-powered extraction for knowledge graph construction
- Structured storage for semantic features

**Scale**:
- 200M+ papers
- 80M+ authors
- 550M+ paper-authorship edges
- 2.4B+ citation edges

**Advanced Features**:
- Structurally parsed text
- Natural language summaries
- Vector embeddings for semantic search

---

### 4. Fact-Checking Knowledge Graph Systems (ACM Survey 2024)
**Key Requirements Identified**:
- Near real-time verification capability
- Conflict detection between new and existing knowledge
- Uncertainty handling for inferred knowledge
- Trust and provenance tracking

**Architecture Pattern**:
- Knowledge graphs as trust infrastructure
- Formal framework for query validation
- Governed and trusted data access
- Explanation/provenance support

---

## Common Patterns Across All Systems

### 1. **Graph Databases Are Standard**
- **Neo4j** is the most common choice for property graphs
- **RDF triples** used for linked open data approaches
- Both support complex relationship queries efficiently

### 2. **Key Advantages of Graph DBs**
✅ Native relationship storage (not joins)
✅ Efficient multi-hop traversals
✅ Fast queries on complex (many-to-many) relationships
✅ Hierarchical and cross-linked data support
✅ Scales to billions of relationships

### 3. **Query Languages**
- **Cypher** (Neo4j): Declarative, pattern-matching, easy to learn
- **SPARQL** (RDF): Standard for semantic web queries

### 4. **Integration Patterns**
- RESTful APIs for data access
- Object Graph Mappers (OGM) for application layer
- GraphRAG for LLM integration (emerging 2024-2025)

---

## Recommendation for Our System

### Primary Choice: **Neo4j Graph Database**

**Rationale**:
1. ✅ **Proven in research domain** - ORKG uses it successfully
2. ✅ **Handles our use cases**:
   - Hierarchical claims (parent → child)
   - Cross-linking (similar claims, evidence relationships)
   - Clustering (claims → super-claim)
   - Fast traversal ("find all related claims")
3. ✅ **Developer-friendly**:
   - Cypher is easier than SQL for graph queries
   - Good Python support (py2neo, neo4j-driver)
   - Great visualization tools (Neo4j Browser, Bloom)
4. ✅ **Open source** with commercial support
5. ✅ **Scales well** - proven at 100TB+ scale (Infinigraph 2025)

**Alternative**: PostgreSQL with ltree/recursive queries
- ✅ We already have the schema
- ✅ Good for hierarchical data
- ❌ Not optimized for graph traversals
- ❌ Complex queries harder to write
- ❌ Not the industry standard for this problem

---

## Our Data Model in Neo4j

### Node Types
```cypher
(:Document)        // Research papers
(:Claim)           // Individual claims from papers
(:SuperClaim)      // Normalized merged claims
(:Qualifier)       // Modal/frequency/quantity qualifiers
(:Evidence)        // Supporting/contradicting evidence
(:Investigation)   // Investigation records
(:Source)          // External sources (URLs, papers)
```

### Relationship Types
```cypher
(:Document)-[:CONTAINS]->(:Claim)
(:Claim)-[:SIMILAR_TO {score: 0.85}]->(:Claim)
(:Claim)-[:MERGED_INTO]->(:SuperClaim)
(:Claim)-[:HAS_QUALIFIER]->(:Qualifier)
(:Claim)-[:PARENT_OF]->(:Claim)           // Hierarchical
(:Claim)-[:SUPPORTS]->(:Claim)
(:Claim)-[:CONTRADICTS]->(:Claim)
(:Investigation)-[:FOUND]->(:Evidence)
(:Evidence)-[:REFERENCES]->(:Source)
```

### Example Queries

**Find all related claims:**
```cypher
MATCH (c:Claim {id: 'claim-123'})-[r*1..3]-(related:Claim)
RETURN c, r, related
```

**Cluster similar claims:**
```cypher
MATCH (c1:Claim)-[s:SIMILAR_TO]-(c2:Claim)
WHERE s.score > 0.8
RETURN c1, c2
ORDER BY s.score DESC
```

**Create super-claim from cluster:**
```cypher
MATCH (claims:Claim)-[:SIMILAR_TO*]-(cluster)
WHERE cluster.id IN $cluster_ids
CREATE (super:SuperClaim {
  text: $normalized_text,
  created: datetime()
})
FOREACH (c IN claims |
  CREATE (c)-[:MERGED_INTO {verbatim: c.text}]->(super)
)
RETURN super
```

**Find evidence chain:**
```cypher
MATCH path = (claim:Claim)-[:SUPPORTS|CONTRADICTS*1..5]-(evidence:Evidence)
RETURN path
```

---

## Implementation Plan

### Phase 1: Setup (Today)
1. Install Neo4j (Community Edition)
2. Create initial schema (nodes + relationships)
3. Test with Szasz paper claims

### Phase 2: Migration
1. Keep PostgreSQL for:
   - User accounts
   - System configuration
   - Audit logs
2. Use Neo4j for:
   - Claims and relationships
   - Knowledge graph
   - Investigation results

### Phase 3: Integration
1. Python driver: `pip install neo4j`
2. Create database layer for Neo4j
3. Migrate claim extraction to Neo4j storage
4. Build visualization tools

---

## Key Insights from Research

1. **Graph databases are not overkill** - they're the standard for this problem
2. **ORKG proves it works** for research claim management
3. **Cypher is expressive** - complex queries are simpler than SQL
4. **Relationships are first-class** - not foreign keys, actual graph edges
5. **Industry trend** - GraphRAG, knowledge graphs for LLMs growing rapidly

---

## Questions Answered

**Q: Is PostgreSQL good enough?**
A: It CAN work, but graph databases are optimized for this. We'd be fighting PostgreSQL's relational model.

**Q: Is Neo4j too complex?**
A: No - ORKG, MAKG, and major research systems use graph databases. It's actually simpler for relationship queries.

**Q: Can we start with PostgreSQL and migrate later?**
A: Yes, but better to start right. Graph database design is different from relational.

**Q: What about performance?**
A: Neo4j has demonstrated 100TB+ scale, our system will be <1TB for years.

---

## Recommendation Summary

**Use Neo4j Community Edition**

**Why**:
- Industry standard for knowledge graphs
- Proven in research domain (ORKG)
- Optimized for our exact use case
- Better developer experience for graph queries
- Future-proof (GraphRAG integration)

**Migration Path**:
1. Start Neo4j container
2. Create schema (nodes/relationships)
3. Extract claims → store in Neo4j
4. Build clustering logic
5. Visualize claim networks

**Next Steps**:
1. Install Neo4j
2. Design complete schema
3. Extract all Szasz claims
4. Test clustering algorithm
5. Build first pipeline demo
