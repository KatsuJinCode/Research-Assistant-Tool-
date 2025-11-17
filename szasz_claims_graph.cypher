// Graph export for Neo4j
// Generated: 2025-11-17T00:33:19.310287

CREATE (n:Document {title: "The Myth of Mental Illness", author: "Thomas S. Szasz", source: "sample papers/SHORT-The-Myth-of-Mental-Illness.pdf", char_count: 41293, id: "82db081e-3335-4fe2-9b48-034ab0d863a5", created_at: "2025-11-17T00:33:19.302750"})

CREATE (n:Claim {text: "There is no such thing as mental illness", type: "normative", section: "Introduction", page: 1, confidence: 0.95, has_qualifiers: false, qualifier_count: 0, id: "1affbe15-a219-40da-a2ad-ea6274af8a41", created_at: "2025-11-17T00:33:19.304495"})

CREATE (n:Claim {text: "Mental illness is not literally a thing or physical object", type: "definitional", section: "Introduction", page: 1, confidence: 0.95, has_qualifiers: false, qualifier_count: 0, id: "3d04d94f-4346-49f0-b005-ee884775930b", created_at: "2025-11-17T00:33:19.304695"})

CREATE (n:Claim {text: "Mental illness can exist only in the same sort of way in which other theoretical concepts exist", type: "theoretical", section: "Introduction", page: 1, confidence: 0.9, has_qualifiers: true, qualifier_count: 1, id: "58025af0-a178-492b-b41a-478c5b9a781a", created_at: "2025-11-17T00:33:19.304869"})

CREATE (n:Qualifier {text: "can", type: "modal", impact: "indicates_possibility", id: "62007b2a-d3f9-4b16-b781-d13a53747343", created_at: "2025-11-17T00:33:19.304899"})

CREATE (n:Claim {text: "Mental illness now functions merely as a convenient myth", type: "evaluative", section: "Introduction", page: 1, confidence: 0.9, has_qualifiers: false, qualifier_count: 0, id: "75056afb-cefa-4870-bbf5-a2cb58e54d09", created_at: "2025-11-17T00:33:19.305018"})

CREATE (n:Claim {text: "The notion of mental illness has outlived whatever usefulness it might have had", type: "evaluative", section: "Introduction", page: 1, confidence: 0.85, has_qualifiers: true, qualifier_count: 1, id: "768db988-11f8-43a9-82fb-04aa73c1ea4d", created_at: "2025-11-17T00:33:19.305139"})

CREATE (n:Qualifier {text: "might", type: "modal", impact: "indicates_low_probability", id: "555d9159-d0fe-4297-9518-6adeabb16230", created_at: "2025-11-17T00:33:19.305155"})

CREATE (n:Claim {text: "Mental illness is widely regarded as the cause of innumerable diverse happenings", type: "empirical", section: "Introduction", page: 1, confidence: 0.9, has_qualifiers: false, qualifier_count: 0, id: "00e7eaa7-27f0-4046-8721-35c105f5226e", created_at: "2025-11-17T00:33:19.305301"})

CREATE (n:Claim {text: "Syphilis of the brain and delirious conditions are diseases of the brain, not of the mind", type: "definitional", section: "Brain Disease", page: 1, confidence: 0.95, has_qualifiers: false, qualifier_count: 0, id: "fe8493dd-d0e2-4162-ac8f-fc330082a57c", created_at: "2025-11-17T00:33:19.305446"})

CREATE (n:Claim {text: "Many contemporary psychiatrists hold the view that all mental illness is brain disease", type: "empirical", section: "Brain Disease", page: 1, confidence: 0.9, has_qualifiers: true, qualifier_count: 2, id: "150d273d-5fc2-465b-8804-ca692b70c57b", created_at: "2025-11-17T00:33:19.305583"})

CREATE (n:Qualifier {text: "all", type: "quantity", impact: "universal_quantification", id: "a40f1fc6-75db-4e59-8b6f-7c793182270e", created_at: "2025-11-17T00:33:19.305598"})

CREATE (n:Qualifier {text: "many", type: "quantity", impact: "large_quantity", id: "a05b147b-8d47-4bb8-96de-0d27ee0d44cc", created_at: "2025-11-17T00:33:19.305608"})

CREATE (n:Claim {text: "A disease of the brain is a neurological defect, not a problem in living", type: "definitional", section: "Brain Disease", page: 1, confidence: 0.9, has_qualifiers: false, qualifier_count: 0, id: "ee77e5cf-cd25-48aa-85d7-4680afd52a7b", created_at: "2025-11-17T00:33:19.305748"})

CREATE (n:Claim {text: "Mental illness is a theoretical concept, not a physical entity", type: "definitional", section: "Introduction", page: 1, confidence: 0.9, has_qualifiers: false, qualifier_count: 0, id: "534e7710-b89f-4809-aeb0-c0bf266e50e8", created_at: "2025-11-17T00:33:19.305883"})

CREATE (n:Claim {text: "The concept of mental illness functions as a myth", type: "evaluative", section: "Introduction", page: 1, confidence: 0.85, has_qualifiers: false, qualifier_count: 0, id: "02f3b5e4-6526-4c1e-9a53-53fed4a915d9", created_at: "2025-11-17T00:33:19.305984"})

CREATE (n:Claim {text: "Mental illness is not a literal physical object", type: "definitional", section: "Introduction", page: 1, confidence: 0.95, has_qualifiers: false, qualifier_count: 0, id: "ee5dae24-6d31-4252-8113-5139c89aad15", created_at: "2025-11-17T00:33:19.306084"})

CREATE (n:Claim {text: "People can have troubles expressed as problems in living", type: "theoretical", section: "Brain Disease", page: 2, confidence: 0.9, has_qualifiers: true, qualifier_count: 1, id: "a105ab93-cdcb-48c6-9328-d3aede248ae2", created_at: "2025-11-17T00:33:19.306188"})

CREATE (n:Qualifier {text: "can", type: "modal", impact: "indicates_possibility", id: "6f78be3b-a3b4-44e0-b1d6-6b9495a65a8f", created_at: "2025-11-17T00:33:19.306200"})

CREATE (n:Claim {text: "Problems in living differ from brain diseases", type: "definitional", section: "Brain Disease", page: 2, confidence: 0.9, has_qualifiers: false, qualifier_count: 0, id: "6327f46a-7010-484f-897d-4be9526d97f9", created_at: "2025-11-17T00:33:19.306302"})

CREATE (n:Claim {text: "Differences in personal needs, opinions, and values can cause troubles in living", type: "theoretical", section: "Brain Disease", page: 2, confidence: 0.85, has_qualifiers: true, qualifier_count: 1, id: "d842fac4-8c62-4865-9ff1-4260709942a9", created_at: "2025-11-17T00:33:19.306417"})

CREATE (n:Qualifier {text: "can", type: "modal", impact: "indicates_possibility", id: "8961e495-57c9-42cd-9a84-c461e885d0de", created_at: "2025-11-17T00:33:19.306429"})

CREATE (n:Claim {text: "Familiar theories are in the habit of posing as objective truths", type: "methodological", section: "Introduction", page: 1, confidence: 0.85, has_qualifiers: false, qualifier_count: 0, id: "31c84806-b449-4f56-9210-1420e294872a", created_at: "2025-11-17T00:33:19.306544"})

CREATE (n:Claim {text: "The notion of mental illness derives its main support from phenomena such as syphilis of the brain", type: "empirical", section: "Brain Disease", page: 1, confidence: 0.9, has_qualifiers: false, qualifier_count: 0, id: "b5e74138-32a7-409f-ad49-b1179b1b06a9", created_at: "2025-11-17T00:33:19.306665"})

CREATE (n:Claim {text: "All problems in living are erroneously attributed to physicochemical processes by some psychiatrists", type: "critical", section: "Brain Disease", page: 1, confidence: 0.85, has_qualifiers: true, qualifier_count: 2, id: "bacf70b9-836a-446d-9ff4-fd17f2565790", created_at: "2025-11-17T00:33:19.306786"})

CREATE (n:Qualifier {text: "all", type: "quantity", impact: "universal_quantification", id: "2c1f5a0c-01ce-42ae-a42c-d79fdd502f48", created_at: "2025-11-17T00:33:19.306798"})

CREATE (n:Qualifier {text: "some", type: "quantity", impact: "existential_quantification", id: "adf2fd4f-9456-4616-95e4-2ad0fada41e5", created_at: "2025-11-17T00:33:19.306808"})

CREATE (n:Claim {text: "Mental illness exists only as a theoretical concept", type: "theoretical", section: "Introduction", page: 1, confidence: 0.9, has_qualifiers: false, qualifier_count: 0, id: "fcb68d9a-b232-4eee-a53a-80d60a0c98b4", created_at: "2025-11-17T00:33:19.306918"})

CREATE (n:Claim {text: "The myth of mental illness has become widely accepted", type: "empirical", section: "Introduction", page: 1, confidence: 0.85, has_qualifiers: false, qualifier_count: 0, id: "9eee2e94-7684-46e8-bfbe-478a35d48453", created_at: "2025-11-17T00:33:19.307017"})

CREATE (n:Claim {text: "Brain diseases are neurological, not psychiatric", type: "definitional", section: "Brain Disease", page: 1, confidence: 0.9, has_qualifiers: false, qualifier_count: 0, id: "9895fa41-2385-4871-894d-847a0089d7d9", created_at: "2025-11-17T00:33:19.307129"})

CREATE (n:SuperClaim {text: "Mental illness is not a physical object or literal thing", confidence: 0.95, member_count: 4, id: "d3ebf78f-441f-440c-a361-ee42c832981b", created_at: "2025-11-17T00:33:19.309072"})

CREATE (n:SuperClaim {text: "Mental illness functions as a theoretical concept or myth", confidence: 0.95, member_count: 3, id: "0084bf34-e644-425e-9df7-c1712fded025", created_at: "2025-11-17T00:33:19.309197"})

CREATE (n:SuperClaim {text: "Brain diseases are neurological conditions, not mental illnesses", confidence: 0.95, member_count: 2, id: "c36c4aba-0064-4f41-b6d7-c5b11c486901", created_at: "2025-11-17T00:33:19.309296"})

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "1affbe15-a219-40da-a2ad-ea6274af8a41"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.304506"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "3d04d94f-4346-49f0-b005-ee884775930b"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.304702"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "58025af0-a178-492b-b41a-478c5b9a781a"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.304877"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "75056afb-cefa-4870-bbf5-a2cb58e54d09"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.305024"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "768db988-11f8-43a9-82fb-04aa73c1ea4d"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.305144"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "00e7eaa7-27f0-4046-8721-35c105f5226e"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.305308"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "fe8493dd-d0e2-4162-ac8f-fc330082a57c"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.305452"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "150d273d-5fc2-465b-8804-ca692b70c57b"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.305589"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "ee77e5cf-cd25-48aa-85d7-4680afd52a7b"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.305752"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "534e7710-b89f-4809-aeb0-c0bf266e50e8"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.305887"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "02f3b5e4-6526-4c1e-9a53-53fed4a915d9"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.305987"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "ee5dae24-6d31-4252-8113-5139c89aad15"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.306087"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "a105ab93-cdcb-48c6-9328-d3aede248ae2"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.306191"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "6327f46a-7010-484f-897d-4be9526d97f9"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.306306"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "d842fac4-8c62-4865-9ff1-4260709942a9"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.306421"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "31c84806-b449-4f56-9210-1420e294872a"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.306547"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "b5e74138-32a7-409f-ad49-b1179b1b06a9"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.306668"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "bacf70b9-836a-446d-9ff4-fd17f2565790"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.306790"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "fcb68d9a-b232-4eee-a53a-80d60a0c98b4"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.306921"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "9eee2e94-7684-46e8-bfbe-478a35d48453"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.307021"}]->(b)

MATCH (a {id: "82db081e-3335-4fe2-9b48-034ab0d863a5"}), (b {id: "9895fa41-2385-4871-894d-847a0089d7d9"})
CREATE (a)-[:CONTAINS {created_at: "2025-11-17T00:33:19.307132"}]->(b)

MATCH (a {id: "3d04d94f-4346-49f0-b005-ee884775930b"}), (b {id: "58025af0-a178-492b-b41a-478c5b9a781a"})
CREATE (a)-[:SIMILAR_TO {score: 0.95, created_at: "2025-11-17T00:33:19.307411"}]->(b)

MATCH (a {id: "3d04d94f-4346-49f0-b005-ee884775930b"}), (b {id: "534e7710-b89f-4809-aeb0-c0bf266e50e8"})
CREATE (a)-[:SIMILAR_TO {score: 0.9, created_at: "2025-11-17T00:33:19.307446"}]->(b)

MATCH (a {id: "3d04d94f-4346-49f0-b005-ee884775930b"}), (b {id: "ee5dae24-6d31-4252-8113-5139c89aad15"})
CREATE (a)-[:SIMILAR_TO {score: 0.98, created_at: "2025-11-17T00:33:19.307465"}]->(b)

MATCH (a {id: "3d04d94f-4346-49f0-b005-ee884775930b"}), (b {id: "d3ebf78f-441f-440c-a361-ee42c832981b"})
CREATE (a)-[:MERGED_INTO {verbatim: "Mental illness is not literally a thing or physical object", original_confidence: 0.95, created_at: "2025-11-17T00:33:19.309082"}]->(b)

MATCH (a {id: "58025af0-a178-492b-b41a-478c5b9a781a"}), (b {id: "62007b2a-d3f9-4b16-b781-d13a53747343"})
CREATE (a)-[:HAS_QUALIFIER {created_at: "2025-11-17T00:33:19.304904"}]->(b)

MATCH (a {id: "58025af0-a178-492b-b41a-478c5b9a781a"}), (b {id: "534e7710-b89f-4809-aeb0-c0bf266e50e8"})
CREATE (a)-[:SIMILAR_TO {score: 0.92, created_at: "2025-11-17T00:33:19.307484"}]->(b)

MATCH (a {id: "58025af0-a178-492b-b41a-478c5b9a781a"}), (b {id: "ee5dae24-6d31-4252-8113-5139c89aad15"})
CREATE (a)-[:SIMILAR_TO {score: 0.95, created_at: "2025-11-17T00:33:19.307497"}]->(b)

MATCH (a {id: "58025af0-a178-492b-b41a-478c5b9a781a"}), (b {id: "d3ebf78f-441f-440c-a361-ee42c832981b"})
CREATE (a)-[:MERGED_INTO {verbatim: "Mental illness can exist only in the same sort of way in which other theoretical concepts exist", original_confidence: 0.9, created_at: "2025-11-17T00:33:19.309096"}]->(b)

MATCH (a {id: "75056afb-cefa-4870-bbf5-a2cb58e54d09"}), (b {id: "02f3b5e4-6526-4c1e-9a53-53fed4a915d9"})
CREATE (a)-[:SIMILAR_TO {score: 0.88, created_at: "2025-11-17T00:33:19.307524"}]->(b)

MATCH (a {id: "75056afb-cefa-4870-bbf5-a2cb58e54d09"}), (b {id: "fcb68d9a-b232-4eee-a53a-80d60a0c98b4"})
CREATE (a)-[:SIMILAR_TO {score: 0.85, created_at: "2025-11-17T00:33:19.307542"}]->(b)

MATCH (a {id: "75056afb-cefa-4870-bbf5-a2cb58e54d09"}), (b {id: "0084bf34-e644-425e-9df7-c1712fded025"})
CREATE (a)-[:MERGED_INTO {verbatim: "Mental illness now functions merely as a convenient myth", original_confidence: 0.9, created_at: "2025-11-17T00:33:19.309207"}]->(b)

MATCH (a {id: "768db988-11f8-43a9-82fb-04aa73c1ea4d"}), (b {id: "555d9159-d0fe-4297-9518-6adeabb16230"})
CREATE (a)-[:HAS_QUALIFIER {created_at: "2025-11-17T00:33:19.305161"}]->(b)

MATCH (a {id: "fe8493dd-d0e2-4162-ac8f-fc330082a57c"}), (b {id: "9eee2e94-7684-46e8-bfbe-478a35d48453"})
CREATE (a)-[:SIMILAR_TO {score: 0.87, created_at: "2025-11-17T00:33:19.307552"}]->(b)

MATCH (a {id: "fe8493dd-d0e2-4162-ac8f-fc330082a57c"}), (b {id: "c36c4aba-0064-4f41-b6d7-c5b11c486901"})
CREATE (a)-[:MERGED_INTO {verbatim: "Syphilis of the brain and delirious conditions are diseases of the brain, not of the mind", original_confidence: 0.95, created_at: "2025-11-17T00:33:19.309305"}]->(b)

MATCH (a {id: "150d273d-5fc2-465b-8804-ca692b70c57b"}), (b {id: "a40f1fc6-75db-4e59-8b6f-7c793182270e"})
CREATE (a)-[:HAS_QUALIFIER {created_at: "2025-11-17T00:33:19.305601"}]->(b)

MATCH (a {id: "150d273d-5fc2-465b-8804-ca692b70c57b"}), (b {id: "a05b147b-8d47-4bb8-96de-0d27ee0d44cc"})
CREATE (a)-[:HAS_QUALIFIER {created_at: "2025-11-17T00:33:19.305611"}]->(b)

MATCH (a {id: "534e7710-b89f-4809-aeb0-c0bf266e50e8"}), (b {id: "ee5dae24-6d31-4252-8113-5139c89aad15"})
CREATE (a)-[:SIMILAR_TO {score: 0.93, created_at: "2025-11-17T00:33:19.307512"}]->(b)

MATCH (a {id: "534e7710-b89f-4809-aeb0-c0bf266e50e8"}), (b {id: "d3ebf78f-441f-440c-a361-ee42c832981b"})
CREATE (a)-[:MERGED_INTO {verbatim: "Mental illness is a theoretical concept, not a physical entity", original_confidence: 0.9, created_at: "2025-11-17T00:33:19.309093"}]->(b)

MATCH (a {id: "02f3b5e4-6526-4c1e-9a53-53fed4a915d9"}), (b {id: "0084bf34-e644-425e-9df7-c1712fded025"})
CREATE (a)-[:MERGED_INTO {verbatim: "The concept of mental illness functions as a myth", original_confidence: 0.85, created_at: "2025-11-17T00:33:19.309202"}]->(b)

MATCH (a {id: "ee5dae24-6d31-4252-8113-5139c89aad15"}), (b {id: "d3ebf78f-441f-440c-a361-ee42c832981b"})
CREATE (a)-[:MERGED_INTO {verbatim: "Mental illness is not a literal physical object", original_confidence: 0.95, created_at: "2025-11-17T00:33:19.309089"}]->(b)

MATCH (a {id: "a105ab93-cdcb-48c6-9328-d3aede248ae2"}), (b {id: "6f78be3b-a3b4-44e0-b1d6-6b9495a65a8f"})
CREATE (a)-[:HAS_QUALIFIER {created_at: "2025-11-17T00:33:19.306203"}]->(b)

MATCH (a {id: "d842fac4-8c62-4865-9ff1-4260709942a9"}), (b {id: "8961e495-57c9-42cd-9a84-c461e885d0de"})
CREATE (a)-[:HAS_QUALIFIER {created_at: "2025-11-17T00:33:19.306434"}]->(b)

MATCH (a {id: "bacf70b9-836a-446d-9ff4-fd17f2565790"}), (b {id: "2c1f5a0c-01ce-42ae-a42c-d79fdd502f48"})
CREATE (a)-[:HAS_QUALIFIER {created_at: "2025-11-17T00:33:19.306801"}]->(b)

MATCH (a {id: "bacf70b9-836a-446d-9ff4-fd17f2565790"}), (b {id: "adf2fd4f-9456-4616-95e4-2ad0fada41e5"})
CREATE (a)-[:HAS_QUALIFIER {created_at: "2025-11-17T00:33:19.306811"}]->(b)

MATCH (a {id: "fcb68d9a-b232-4eee-a53a-80d60a0c98b4"}), (b {id: "0084bf34-e644-425e-9df7-c1712fded025"})
CREATE (a)-[:MERGED_INTO {verbatim: "Mental illness exists only as a theoretical concept", original_confidence: 0.9, created_at: "2025-11-17T00:33:19.309211"}]->(b)

MATCH (a {id: "9eee2e94-7684-46e8-bfbe-478a35d48453"}), (b {id: "c36c4aba-0064-4f41-b6d7-c5b11c486901"})
CREATE (a)-[:MERGED_INTO {verbatim: "The myth of mental illness has become widely accepted", original_confidence: 0.85, created_at: "2025-11-17T00:33:19.309301"}]->(b)