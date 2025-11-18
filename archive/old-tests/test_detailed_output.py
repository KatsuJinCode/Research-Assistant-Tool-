"""
Clean test output showing exactly what was requested:
- Source quote
- Clarified version
- All 3 candidates with ratings
- Time for each step
"""

import time
from web_ui.document_processor import LiveDocumentProcessor

processor = LiveDocumentProcessor(progress_callback=None)

examples = [
    "A person's belief cannot be explained by a defect or disease of the nervous system",
    "The study suggests that some users who regularly utilize the system might experience improved performance metrics",
    "Mental illness derives its main support from syphilis of the brain in which persons manifest various peculiarities or disorders of thinking"
]

for i, claim in enumerate(examples, 1):
    print(f"\n{'='*80}")
    print(f"EXAMPLE {i}")
    print(f"{'='*80}\n")

    print(f"SOURCE:\n{claim}\n")

    # Time the whole process
    start_total = time.time()
    result = processor._simplify_claim_with_agent(claim)
    total_time = time.time() - start_total

    print(f"CLARIFIED:\n{result['clarified']}\n")

    print("CANDIDATES:")
    print(f"  1. {result['candidate_1']}")
    print(f"     Rating: {result['score_1']:.2f}\n")

    print(f"  2. {result['candidate_2']}")
    print(f"     Rating: {result['score_2']:.2f}\n")

    print(f"  3. {result['candidate_3']}")
    print(f"     Rating: {result['score_3']:.2f}\n")

    selected_num = result['selected_candidate']
    selected_score = result[f'score_{selected_num}']
    print(f"SELECTED: Candidate {selected_num} (Rating: {selected_score:.2f})")
    print(f"SUMMARY: {result['summary']}\n")

    print(f"TOTAL TIME: {total_time:.1f} seconds")
