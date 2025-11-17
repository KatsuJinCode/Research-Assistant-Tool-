"""
Real claim extraction from Szasz - The Myth of Mental Illness
Extracted by Claude directly (no external API calls)
"""

# Opening section claims
OPENING_CLAIMS = [
    {
        "text": "There is no such thing as mental illness",
        "type": "normative",
        "section": "Introduction",
        "confidence": 0.95,
        "page": 1
    },
    {
        "text": "Mental illness is not literally a thing or physical object",
        "type": "definitional",
        "section": "Introduction",
        "confidence": 0.95,
        "page": 1
    },
    {
        "text": "Mental illness can exist only in the same sort of way in which other theoretical concepts exist",
        "type": "theoretical",
        "section": "Introduction",
        "confidence": 0.90,
        "page": 1,
        "qualifiers": ["can", "only"]
    },
    {
        "text": "Familiar theories are in the habit of posing as objective truths or facts",
        "type": "methodological",
        "section": "Introduction",
        "confidence": 0.85,
        "page": 1
    },
    {
        "text": "Mental illness is widely regarded as the cause of innumerable diverse happenings",
        "type": "empirical",
        "section": "Introduction",
        "confidence": 0.90,
        "page": 1
    },
    {
        "text": "The notion of mental illness has outlived whatever usefulness it might have had",
        "type": "evaluative",
        "section": "Introduction",
        "confidence": 0.85,
        "page": 1,
        "qualifiers": ["might"]
    },
    {
        "text": "Mental illness now functions merely as a convenient myth",
        "type": "evaluative",
        "section": "Introduction",
        "confidence": 0.90,
        "page": 1
    }
]

# Brain disease section claims
BRAIN_DISEASE_CLAIMS = [
    {
        "text": "The notion of mental illness derives its main support from phenomena such as syphilis of the brain or delirious conditions",
        "type": "empirical",
        "section": "Mental Illness as a Sign of Brain Disease",
        "confidence": 0.90,
        "page": 1
    },
    {
        "text": "Syphilis of the brain and delirious conditions are diseases of the brain, not of the mind",
        "type": "definitional",
        "section": "Mental Illness as a Sign of Brain Disease",
        "confidence": 0.95,
        "page": 1
    },
    {
        "text": "Some neurological defect will ultimately be found for all disorders of thinking and behavior",
        "type": "theoretical",
        "section": "Mental Illness as a Sign of Brain Disease",
        "confidence": 0.80,
        "page": 1,
        "qualifiers": ["will", "ultimately", "all"],
        "note": "This is a position Szasz is describing, not endorsing"
    },
    {
        "text": "Many contemporary psychiatrists, physicians, and other scientists hold the view that all mental illness is brain disease",
        "type": "empirical",
        "section": "Mental Illness as a Sign of Brain Disease",
        "confidence": 0.90,
        "page": 1,
        "qualifiers": ["many"]
    },
    {
        "text": "People cannot have troubles expressed as mental illnesses because of differences in personal needs, opinions, social aspirations, or values",
        "type": "theoretical",
        "section": "Mental Illness as a Sign of Brain Disease",
        "confidence": 0.85,
        "page": 1,
        "note": "Position Szasz is critiquing"
    },
    {
        "text": "All problems in living are attributed to physicochemical processes which will be discovered by medical research",
        "type": "theoretical",
        "section": "Mental Illness as a Sign of Brain Disease",
        "confidence": 0.85,
        "page": 1,
        "qualifiers": ["all", "will"],
        "note": "Position Szasz is critiquing"
    },
    {
        "text": "Mental illnesses are regarded as basically no different than all other diseases of the body",
        "type": "theoretical",
        "section": "Mental Illness as a Sign of Brain Disease",
        "confidence": 0.90,
        "page": 1,
        "qualifiers": ["all"]
    },
    {
        "text": "Mental diseases affect the brain and manifest themselves by means of mental symptoms",
        "type": "theoretical",
        "section": "Mental Illness as a Sign of Brain Disease",
        "confidence": 0.90,
        "page": 1,
        "note": "Position being critiqued"
    },
    {
        "text": "Bodily diseases affect other organ systems and manifest themselves by means of symptoms referable to those parts of the body",
        "type": "theoretical",
        "section": "Mental Illness as a Sign of Brain Disease",
        "confidence": 0.95,
        "page": 1
    },
    {
        "text": "A disease of the brain analogous to a disease of the skin or bone is a neurological defect, not a problem",
        "type": "definitional",
        "section": "Mental Illness as a Sign of Brain Disease",
        "confidence": 0.90,
        "page": 1
    }
]

# Combined extraction
ALL_CLAIMS = OPENING_CLAIMS + BRAIN_DISEASE_CLAIMS

print(f"Total claims extracted: {len(ALL_CLAIMS)}")
print(f"Claims with qualifiers: {sum(1 for c in ALL_CLAIMS if c.get('qualifiers'))}")
print()

for i, claim in enumerate(ALL_CLAIMS, 1):
    print(f"{i}. [{claim['type'].upper()}] {claim['text']}")
    if claim.get('qualifiers'):
        print(f"   Qualifiers: {', '.join(claim['qualifiers'])}")
    if claim.get('note'):
        print(f"   Note: {claim['note']}")
    print()
