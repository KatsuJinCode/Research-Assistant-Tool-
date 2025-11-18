"""
Test the new 4-stage pipeline on 3 random claims:
Stage 1: Analysis (verbose understanding)
Stage 2: Clarification (reword to be explicit, similar length)
Stage 3: Simplification (3 optimal attempts)
Stage 4: Validation (check against all stages)
"""

import sys
import io
import time
from web_ui.document_processor import LiveDocumentProcessor

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 3 test claims
claims = [
    "A person's belief cannot be explained by a defect or disease of the nervous system",
    "The study suggests that some users who regularly utilize the system might experience improved performance metrics",
    "Mental illness derives its main support from syphilis of the brain in which persons manifest various peculiarities or disorders of thinking"
]

processor = LiveDocumentProcessor(progress_callback=None)

for i, claim in enumerate(claims, 1):
    print("=" * 100)
    print(f"CLAIM {i}")
    print("=" * 100)
    print()

    print("SOURCE:")
    print(claim)
    print(f"({len(claim.split())} words)")
    print()

    # STAGE 1: Analysis
    print("-" * 100)
    print("STAGE 1: ANALYSIS")
    print("-" * 100)
    start = time.perf_counter()
    try:
        analysis = processor._analyze_claim(claim)
        time_analysis = (time.perf_counter() - start) * 1000
        print(analysis)
        print(f"({len(analysis.split())} words, {time_analysis:.1f}ms)")
        print()
    except Exception as e:
        print(f"ERROR: {e}")
        continue

    # STAGE 2: Clarification
    print("-" * 100)
    print("STAGE 2: CLARIFICATION")
    print("-" * 100)
    start = time.perf_counter()
    try:
        clarified = processor._clarify_claim(claim, analysis)
        time_clarify = (time.perf_counter() - start) * 1000
        print(clarified)
        print(f"({len(clarified.split())} words, {time_clarify:.1f}ms)")
        print()
    except Exception as e:
        print(f"ERROR: {e}")
        continue

    # STAGE 3: Simplification
    print("-" * 100)
    print("STAGE 3: SIMPLIFICATION (3 attempts)")
    print("-" * 100)
    start = time.perf_counter()
    try:
        candidates = processor._simplify_claim_candidates(clarified)
        time_simplify = (time.perf_counter() - start) * 1000
        print(f"1. {candidates['candidate_1']} ({len(candidates['candidate_1'].split())} words)")
        print(f"2. {candidates['candidate_2']} ({len(candidates['candidate_2'].split())} words)")
        print(f"3. {candidates['candidate_3']} ({len(candidates['candidate_3'].split())} words)")
        print(f"({time_simplify:.1f}ms)")
        print()
    except Exception as e:
        print(f"ERROR: {e}")
        continue

    # STAGE 4: Validation
    print("-" * 100)
    print("STAGE 4: VALIDATION")
    print("-" * 100)
    start = time.perf_counter()
    try:
        validation = processor._validate_final(claim, analysis, clarified, candidates)
        time_validate = (time.perf_counter() - start) * 1000
        print(f"Candidate 1: {validation['score_1']:.2f}")
        print(f"Candidate 2: {validation['score_2']:.2f}")
        print(f"Candidate 3: {validation['score_3']:.2f}")
        print(f"Best: {validation['best_candidate']}")
        print(f"Reason: {validation['reason']}")
        print(f"({time_validate:.1f}ms)")
        print()
    except Exception as e:
        print(f"ERROR: {e}")
        continue

    # Summary
    print("-" * 100)
    print("FINAL")
    print("-" * 100)
    if validation['best_candidate'] != 'none':
        best = int(validation['best_candidate'])
        final = candidates[f'candidate_{best}']
        print(f"Selected: Candidate {best}")
        print(final)
        print()
    else:
        print("REJECTED - No candidate passed validation")
        print()

    total = time_analysis + time_clarify + time_simplify + time_validate
    print(f"Total time: {total:.1f}ms ({total/1000:.2f}s)")
    print()
    print()
