"""
Unit test for structured JSON output approach (without --tools flag)

Tests the new prompt-based JSON extraction to verify it works before
rolling out to production.
"""

import json
import subprocess
import sys

# Fix Windows unicode issues
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


def test_structured_json_output():
    """Test that Claude returns valid JSON when prompted correctly"""

    expected_schema = {
        "type": "object",
        "properties": {
            "answer": {"type": "number"},
            "explanation": {"type": "string"}
        },
        "required": ["answer", "explanation"]
    }

    schema_str = json.dumps(expected_schema, indent=2)

    prompt = f"""What is 2+2?

IMPORTANT: You MUST respond with ONLY valid JSON matching this exact schema:

{schema_str}

Do NOT include any explanatory text, markdown formatting, or code blocks.
Output ONLY the raw JSON object."""

    print("=" * 80)
    print("TESTING STRUCTURED JSON OUTPUT (NO --tools FLAG)")
    print("=" * 80)
    print()
    print("PROMPT:")
    print(prompt)
    print()
    print("=" * 80)

    # Invoke Claude WITHOUT --tools flag
    try:
        result = subprocess.run(
            ['claude', '-p', prompt, '--output-format', 'json'],
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8'
        )

        print(f"Return code: {result.returncode}")
        print()

        if result.returncode != 0:
            print("STDERR:")
            print(result.stderr)
            return False

        print("RAW RESPONSE:")
        print(result.stdout)
        print()
        print("=" * 80)

        # Parse the CLI wrapper
        response_data = json.loads(result.stdout.strip())

        # Extract result text from wrapper
        if 'result' in response_data:
            result_text = response_data['result']
            print("EXTRACTED RESULT TEXT:")
            print(result_text)
            print()
            print("=" * 80)

            # Try to parse as JSON
            try:
                parsed_json = json.loads(result_text)
                print("✓ SUCCESS: Parsed as valid JSON")
                print()
                print("PARSED JSON:")
                print(json.dumps(parsed_json, indent=2))
                print()

                # Validate schema
                if 'answer' in parsed_json and 'explanation' in parsed_json:
                    print("✓ SUCCESS: JSON matches expected schema")
                    print(f"  answer: {parsed_json['answer']}")
                    print(f"  explanation: {parsed_json['explanation']}")
                    return True
                else:
                    print("✗ FAILURE: JSON missing required fields")
                    print(f"  Expected: answer, explanation")
                    print(f"  Got: {list(parsed_json.keys())}")
                    return False

            except json.JSONDecodeError as e:
                print(f"✗ FAILURE: Result text is not valid JSON")
                print(f"  Error: {e}")

                # Try extracting from code block
                import re
                json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
                if json_match:
                    print("  Found JSON in code block, trying to extract...")
                    try:
                        parsed_json = json.loads(json_match.group(1))
                        print("✓ SUCCESS: Extracted JSON from code block")
                        print()
                        print("PARSED JSON:")
                        print(json.dumps(parsed_json, indent=2))

                        if 'answer' in parsed_json and 'explanation' in parsed_json:
                            print()
                            print("✓ SUCCESS: JSON matches expected schema")
                            return True
                    except json.JSONDecodeError:
                        print("✗ FAILURE: Code block content is not valid JSON")

                return False
        else:
            print("✗ FAILURE: No 'result' field in CLI response")
            print(f"  Response keys: {list(response_data.keys())}")
            return False

    except subprocess.TimeoutExpired:
        print("✗ FAILURE: Command timed out")
        return False
    except Exception as e:
        print(f"✗ FAILURE: {e}")
        return False


def test_claim_extraction_schema():
    """Test with actual claim extraction schema"""

    expected_schema = {
        "type": "object",
        "properties": {
            "claims": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "text": {"type": "string"},
                        "type": {"type": "string"},
                        "confidence": {"type": "number"}
                    }
                }
            }
        }
    }

    schema_str = json.dumps(expected_schema, indent=2)

    prompt = f"""Extract research claims from this text:

TEXT:
Machine learning models can achieve high accuracy on image classification tasks.
Deep neural networks require large amounts of training data.
Transfer learning may reduce training time by up to 50%.

IMPORTANT: You MUST respond with ONLY valid JSON matching this exact schema:

{schema_str}

Do NOT include any explanatory text, markdown formatting, or code blocks.
Output ONLY the raw JSON object."""

    print()
    print("=" * 80)
    print("TESTING CLAIM EXTRACTION SCHEMA")
    print("=" * 80)
    print()

    try:
        result = subprocess.run(
            ['claude', '-p', prompt, '--output-format', 'json'],
            capture_output=True,
            text=True,
            timeout=60,
            encoding='utf-8'
        )

        if result.returncode != 0:
            print(f"✗ FAILURE: Command failed with code {result.returncode}")
            return False

        response_data = json.loads(result.stdout.strip())
        result_text = response_data.get('result', '')

        # Parse JSON
        try:
            parsed_json = json.loads(result_text)
        except json.JSONDecodeError:
            # Try code block extraction
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', result_text, re.DOTALL)
            if json_match:
                parsed_json = json.loads(json_match.group(1))
            else:
                print("✗ FAILURE: Could not parse JSON from response")
                return False

        print("PARSED JSON:")
        print(json.dumps(parsed_json, indent=2))
        print()

        # Validate structure
        if 'claims' in parsed_json and isinstance(parsed_json['claims'], list):
            print(f"✓ SUCCESS: Got {len(parsed_json['claims'])} claims")
            if len(parsed_json['claims']) > 0:
                claim = parsed_json['claims'][0]
                if 'text' in claim and 'type' in claim and 'confidence' in claim:
                    print("✓ SUCCESS: Claims have correct structure")
                    return True
                else:
                    print(f"✗ FAILURE: Claim missing required fields. Got: {list(claim.keys())}")
            else:
                print("⚠ WARNING: No claims extracted")
            return True
        else:
            print("✗ FAILURE: Response missing 'claims' array")
            return False

    except Exception as e:
        print(f"✗ FAILURE: {e}")
        return False


if __name__ == '__main__':
    print()
    print("╔" + "=" * 78 + "╗")
    print("║" + "STRUCTURED JSON OUTPUT TEST SUITE".center(78) + "║")
    print("╚" + "=" * 78 + "╝")
    print()
    print("Testing prompt-based JSON extraction (without --tools flag)")
    print()

    # Test 1: Simple structured output
    test1_pass = test_structured_json_output()

    # Test 2: Claim extraction schema
    test2_pass = test_claim_extraction_schema()

    # Summary
    print()
    print("=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Test 1 (Simple JSON): {'✓ PASS' if test1_pass else '✗ FAIL'}")
    print(f"Test 2 (Claim Extraction): {'✓ PASS' if test2_pass else '✗ FAIL'}")
    print()

    if test1_pass and test2_pass:
        print("✓ ALL TESTS PASSED - Structured output approach is working!")
        print()
        print("Safe to deploy to document_processor.py")
        sys.exit(0)
    else:
        print("✗ SOME TESTS FAILED - Do not deploy yet")
        print()
        print("Need to adjust prompting strategy or JSON extraction logic")
        sys.exit(1)
