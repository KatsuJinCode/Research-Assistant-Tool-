"""
Comprehensive test for single claim showing:
1. Full source text (no truncation)
2. Full clarified version
3. All 3 full simplified candidates with ratings
4. Retry logic if validator requests new candidates
5. Exact timing in milliseconds for each operation
"""

import sys
import io
import time
from web_ui.document_processor import LiveDocumentProcessor
from research_agent.neo4j_database import Neo4jDatabase

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_single_claim_comprehensive():
    """Test one claim with full transparency and timing."""

    # Initialize
    processor = LiveDocumentProcessor(progress_callback=None)

    # Use Example 3 - the problematic case
    claim_text = "Mental illness derives its main support from syphilis of the brain in which persons manifest various peculiarities or disorders of thinking"

    print("=" * 100)
    print("COMPREHENSIVE CLAIM SIMPLIFICATION TEST")
    print("=" * 100)
    print()

    print("SOURCE TEXT (FULL):")
    print("-" * 100)
    print(claim_text)
    print()
    print(f"Length: {len(claim_text)} characters, {len(claim_text.split())} words")
    print()

    # STAGE 1: CLARIFICATION
    print("=" * 100)
    print("STAGE 1: CLARIFICATION")
    print("=" * 100)

    start_clarify = time.perf_counter()
    clarified = processor._clarify_claim(claim_text)
    time_clarify = (time.perf_counter() - start_clarify) * 1000  # Convert to ms

    print()
    print("CLARIFIED TEXT (FULL):")
    print("-" * 100)
    print(clarified)
    print()
    print(f"Length: {len(clarified)} characters, {len(clarified.split())} words")
    print(f"Time: {time_clarify:.1f} ms ({time_clarify/1000:.2f} seconds)")
    print()

    # STAGE 2: CANDIDATE GENERATION (with retry logic)
    print("=" * 100)
    print("STAGE 2: CANDIDATE GENERATION")
    print("=" * 100)
    print()

    max_attempts = 3
    all_attempts = []

    for attempt in range(max_attempts):
        print(f"--- Attempt {attempt + 1} ---")
        print()

        start_gen = time.perf_counter()
        candidates = processor._generate_candidate_summaries(clarified)
        time_gen = (time.perf_counter() - start_gen) * 1000

        print(f"Generation time: {time_gen:.1f} ms ({time_gen/1000:.2f} seconds)")
        print()

        print("CANDIDATE 1 (BREVITY - 5-8 words):")
        print("-" * 100)
        print(candidates['candidate_1'])
        print(f"Length: {len(candidates['candidate_1'].split())} words")
        print()

        print("CANDIDATE 2 (BALANCED - 8-10 words):")
        print("-" * 100)
        print(candidates['candidate_2'])
        print(f"Length: {len(candidates['candidate_2'].split())} words")
        print()

        print("CANDIDATE 3 (COMPLETE - 10-12 words):")
        print("-" * 100)
        print(candidates['candidate_3'])
        print(f"Length: {len(candidates['candidate_3'].split())} words")
        print()

        # STAGE 3: VALIDATION
        print("=" * 100)
        print("STAGE 3: VALIDATION")
        print("=" * 100)
        print()

        start_val = time.perf_counter()
        validation = processor._validate_candidates(claim_text, clarified, candidates)
        time_val = (time.perf_counter() - start_val) * 1000

        print(f"Validation time: {time_val:.1f} ms ({time_val/1000:.2f} seconds)")
        print()

        print("VALIDATION RESULTS:")
        print("-" * 100)
        print(f"Candidate 1 score: {validation['score_1']:.2f}")
        print(f"Candidate 2 score: {validation['score_2']:.2f}")
        print(f"Candidate 3 score: {validation['score_3']:.2f}")
        print()
        print(f"Best candidate: {validation['best_candidate']}")

        if validation['best_candidate'] != 'none':
            best_num = int(validation['best_candidate'])
            best_score = validation[f'score_{best_num}']
            print(f"Best score: {best_score:.2f}")

        print()

        # Check if we need to retry
        if validation['best_candidate'] == 'none':
            print("⚠️  VALIDATOR REJECTED ALL CANDIDATES - Score threshold not met")
            print(f"Specific issues: {validation.get('specific_issues', 'Not specified')}")
            print()

            if attempt < max_attempts - 1:
                print("🔄 RETRYING with new candidate generation...")
                print()
            else:
                print("❌ MAX RETRIES REACHED - Using fallback")
                print()
        else:
            print("✅ VALIDATOR ACCEPTED CANDIDATE")
            print()

            # Store this attempt's data
            all_attempts.append({
                'attempt': attempt + 1,
                'candidates': candidates,
                'validation': validation,
                'time_gen': time_gen,
                'time_val': time_val
            })
            break

        all_attempts.append({
            'attempt': attempt + 1,
            'candidates': candidates,
            'validation': validation,
            'time_gen': time_gen,
            'time_val': time_val
        })

    # FINAL SUMMARY
    print("=" * 100)
    print("FINAL SUMMARY")
    print("=" * 100)
    print()

    if all_attempts and all_attempts[-1]['validation']['best_candidate'] != 'none':
        final = all_attempts[-1]
        best_num = int(final['validation']['best_candidate'])
        best_candidate = final['candidates'][f'candidate_{best_num}']
        best_score = final['validation'][f'score_{best_num}']

        print(f"Selected: Candidate {best_num}")
        print(f"Score: {best_score:.2f}")
        print()
        print("FINAL TEXT:")
        print("-" * 100)
        print(best_candidate)
        print()
    else:
        print("❌ NO CANDIDATE SELECTED - All attempts failed")
        print()

    # TIMING BREAKDOWN
    print("=" * 100)
    print("TIMING BREAKDOWN")
    print("=" * 100)
    print()

    total_time = time_clarify

    print(f"Stage 1 - Clarification:     {time_clarify:7.1f} ms ({time_clarify/1000:6.2f} s)")

    for i, attempt_data in enumerate(all_attempts, 1):
        print(f"Stage 2 - Generation (#{i}):  {attempt_data['time_gen']:7.1f} ms ({attempt_data['time_gen']/1000:6.2f} s)")
        print(f"Stage 3 - Validation (#{i}):  {attempt_data['time_val']:7.1f} ms ({attempt_data['time_val']/1000:6.2f} s)")
        total_time += attempt_data['time_gen'] + attempt_data['time_val']

    print("-" * 100)
    print(f"TOTAL:                       {total_time:7.1f} ms ({total_time/1000:6.2f} s)")
    print()

    # COMPARISON
    print("=" * 100)
    print("SOURCE vs CLARIFIED vs FINAL")
    print("=" * 100)
    print()

    print("SOURCE:")
    print(claim_text)
    print()

    print("CLARIFIED:")
    print(clarified)
    print()

    if all_attempts and all_attempts[-1]['validation']['best_candidate'] != 'none':
        final = all_attempts[-1]
        best_num = int(final['validation']['best_candidate'])
        best_candidate = final['candidates'][f'candidate_{best_num}']

        print("FINAL:")
        print(best_candidate)
    else:
        print("FINAL:")
        print("(none - fallback to truncated original)")

    print()

if __name__ == '__main__':
    test_single_claim_comprehensive()
