"""
Diagnostic script to check what claims exist in Neo4j database
"""
import sys
sys.path.insert(0, 'C:\\Users\\jpswi\\Research-Assistant-Tool-')
from research_agent.neo4j_database import Neo4jDatabase

db = Neo4jDatabase()

print("\n=== DATABASE DIAGNOSTIC ===\n")

# 1. Check all documents
print("1. Documents:")
doc_query = "MATCH (d:Document) RETURN d.id as id, d.title as title, d.status as status"
with db.driver.session(database=db.database) as session:
    result = session.run(doc_query)
    docs = [dict(r) for r in result]
    for doc in docs:
        print(f"   - {doc['id'][:8]}... : {doc['title']} (status: {doc['status']})")

# 2. Check all claims
print("\n2. Claims:")
claim_query = """
MATCH (c:Claim)
RETURN c.id as id, c.text as text, c.summary as summary, c.status as status, c.disposition as disposition
"""
with db.driver.session(database=db.database) as session:
    result = session.run(claim_query)
    claims = [dict(r) for r in result]
    print(f"   Total claims: {len(claims)}")
    for claim in claims[:10]:  # Show first 10
        text = claim.get('summary') or claim.get('text', '')
        text_preview = text[:50] + '...' if len(text) > 50 else text
        print(f"   - {claim['id'][:8]}... : {text_preview}")
        print(f"      status={claim.get('status')}, disposition={claim.get('disposition')}")

# 3. Check CONTAINS_CLAIM relationships
print("\n3. Document -> Claim relationships (CONTAINS_CLAIM):")
rel_query = """
MATCH (d:Document)-[r:CONTAINS_CLAIM]->(c:Claim)
RETURN d.id as doc_id, d.title as doc_title, c.id as claim_id, c.text as claim_text
"""
with db.driver.session(database=db.database) as session:
    result = session.run(rel_query)
    rels = [dict(r) for r in result]
    print(f"   Total relationships: {len(rels)}")
    for rel in rels[:10]:  # Show first 10
        text_preview = rel['claim_text'][:40] + '...' if len(rel['claim_text']) > 40 else rel['claim_text']
        print(f"   - Doc: {rel['doc_title']}")
        print(f"     → Claim: {text_preview}")

# 4. Check HAS_SUB_CLAIM relationships (used by get_full_graph)
print("\n4. Claim -> Claim relationships (HAS_SUB_CLAIM):")
sub_claim_query = """
MATCH (c:Claim)-[r:HAS_SUB_CLAIM]->(child:Claim)
RETURN count(r) as count
"""
with db.driver.session(database=db.database) as session:
    result = session.run(sub_claim_query)
    count = result.single()['count']
    print(f"   Total HAS_SUB_CLAIM relationships: {count}")

# 5. Show what get_full_graph would return
print("\n5. What get_full_graph() would return:")
doc_claim_query = """
MATCH (d:Document)-[:CONTAINS_CLAIM]->(c:Claim)
RETURN d.id as doc_id, collect(c.id) as claim_ids
"""
with db.driver.session(database=db.database) as session:
    result = session.run(doc_claim_query)
    doc_claims = [dict(r) for r in result]
    for dc in doc_claims:
        print(f"   Doc {dc['doc_id'][:8]}... has {len(dc['claim_ids'])} claims")
        print(f"      Claim IDs: {[cid[:8] + '...' for cid in dc['claim_ids']]}")

db.close()
print("\n=== END DIAGNOSTIC ===\n")
