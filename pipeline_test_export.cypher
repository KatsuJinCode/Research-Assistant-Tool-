// Graph export for Neo4j
// Generated: 2025-11-20T20:02:09.834578

CREATE (n:Document {title: "Test Research Paper", author: "Test Author", id: "0934afbd-f376-49df-9d73-5228be16b509", created_at: "2025-11-20T20:02:09.833574"})

CREATE (n:Claim {text: "Some patients may respond to treatment", type: "empirical", id: "f22c62fd-e6b2-43c8-bc2a-daf6a0e299d9", created_at: "2025-11-20T20:02:09.833574"})

CREATE (n:Node {id: "CONTAINS"})

CREATE (n:Qualifier {type: "modal", text: "may", impact: "indicates_permission_or_possibility", id: "fb323e09-1174-4080-80f5-e2396dc0a148", created_at: "2025-11-20T20:02:09.833574"})

CREATE (n:Node {id: "HAS_QUALIFIER"})

CREATE (n:Qualifier {type: "quantity", text: "some", impact: "existential_quantification", id: "c697c3c6-da69-4027-9906-4772b740194c", created_at: "2025-11-20T20:02:09.833574"})

MATCH (a {id: "0934afbd-f376-49df-9d73-5228be16b509"}), (b {id: "CONTAINS"})
CREATE (a)-[:f22c62fd-e6b2-43c8-bc2a-daf6a0e299d9 {created_at: "2025-11-20T20:02:09.833574"}]->(b)

MATCH (a {id: "f22c62fd-e6b2-43c8-bc2a-daf6a0e299d9"}), (b {id: "HAS_QUALIFIER"})
CREATE (a)-[:fb323e09-1174-4080-80f5-e2396dc0a148 {created_at: "2025-11-20T20:02:09.833574"}]->(b)

MATCH (a {id: "f22c62fd-e6b2-43c8-bc2a-daf6a0e299d9"}), (b {id: "HAS_QUALIFIER"})
CREATE (a)-[:c697c3c6-da69-4027-9906-4772b740194c {created_at: "2025-11-20T20:02:09.833574"}]->(b)