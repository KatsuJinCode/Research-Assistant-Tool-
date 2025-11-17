"""
Text Post-Processor

Fixes common text extraction issues:
- Missing first letter (drop caps)
- Broken words across lines
- Encoding artifacts
- Garbled text detection
"""

import re
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)


class TextPostProcessor:
    """Post-processes extracted text to fix common issues."""

    def __init__(self):
        """Initialize text post-processor."""
        # Common words that might be missing first letter
        self.common_words = {
            'y': 'My',      # "Y aim" -> "My aim"
            's': 'As',      # "S I mentioned" -> "As I mentioned"
            'n': 'In',      # "N this paper" -> "In this paper"
            't': 'It',      # "T is clear" -> "It is clear"
            'he': 'The',    # "he paper" -> "The paper"
            'his': 'This',  # "his shows" -> "This shows"
        }

    def fix_drop_cap(self, text: str) -> Tuple[str, bool]:
        """
        Fix missing first letter (drop cap issue).

        Pattern 1: "Y aim" -> "My aim" (first letter missing)
        Pattern 2: Line with single capital letter, next line starts with lowercase
                  "M\nY aim" -> "My aim" (drop cap on own line)

        Args:
            text: Text to fix

        Returns:
            (fixed_text, was_fixed)
        """
        was_fixed = False
        lines = text.split('\n')

        # Pattern 2: Drop cap on own line
        # Look for a line that's just a single capital letter
        # followed by a line starting with lowercase
        for i in range(len(lines) - 1):
            line = lines[i].strip()

            # Check if this line is a single capital letter
            if len(line) == 1 and line.isupper():
                next_line = lines[i + 1].strip()

                # Check if next line exists and has words
                if next_line and next_line.split():
                    first_word = next_line.split()[0]

                    # Try to combine them
                    combined_word = line + first_word

                    # Check if this makes a known word (case-insensitive)
                    if combined_word.lower() in ['my', 'in', 'as', 'it', 'is']:
                        # Combine drop cap with rest of line into single line
                        next_line_rest = ' '.join(next_line.split()[1:])
                        combined_line = combined_word + ' ' + next_line_rest if next_line_rest else combined_word

                        # Remove the drop cap line and replace next line with combined
                        lines[i] = ''  # Remove drop cap line
                        lines[i + 1] = combined_line

                        # Remove empty lines
                        lines = [l for l in lines if l != '']

                        fixed_text = '\n'.join(lines)
                        logger.info(f"Fixed drop cap: '{line}' + '{first_word}' -> '{combined_word}'")
                        return fixed_text, True

        # Pattern 1: Simple missing first letter in first word
        words = text.split()
        if not words:
            return text, False

        first_word = words[0]

        # Check if first word matches a known pattern
        first_word_lower = first_word.lower()
        if first_word_lower in self.common_words:
            replacement = self.common_words[first_word_lower]

            # Preserve original case if it was uppercase
            if first_word[0].isupper():
                words[0] = replacement
            else:
                words[0] = replacement.lower()

            fixed_text = ' '.join(words)
            logger.info(f"Fixed drop cap: '{text[:50]}...' -> '{fixed_text[:50]}...'")
            return fixed_text, True

        return text, was_fixed

    def fix_broken_words(self, text: str) -> Tuple[str, int]:
        """
        Fix words broken by hyphens across lines.

        Examples:
            "ques- tion" -> "question"
            "men- tal" -> "mental"

        Args:
            text: Text to fix

        Returns:
            (fixed_text, num_fixes)
        """
        # Pattern: word- \n word
        pattern = r'(\w+)-\s+(\w+)'

        fixes = 0
        def replacer(match):
            nonlocal fixes
            fixes += 1
            return match.group(1) + match.group(2)

        fixed_text = re.sub(pattern, replacer, text)

        if fixes > 0:
            logger.info(f"Fixed {fixes} broken words")

        return fixed_text, fixes

    def detect_garbled_text(self, text: str) -> Dict[str, any]:
        """
        Detect garbled or nonsense text.

        Indicators:
            - High ratio of special characters
            - Very short "words" (< 2 chars)
            - Unusual character sequences
            - Mid-sentence topic shifts (column crossing)

        Args:
            text: Text to analyze

        Returns:
            {
                'is_garbled': bool,
                'confidence': 0.0-1.0,
                'issues': [list of detected issues],
                'score': quality score 0.0-1.0
            }
        """
        issues = []

        # Count special characters
        special_chars = sum(1 for c in text if not c.isalnum() and not c.isspace())
        special_ratio = special_chars / len(text) if text else 0

        if special_ratio > 0.15:  # More than 15% special chars
            issues.append(f"High special character ratio: {special_ratio:.2%}")

        # Check for encoding artifacts
        encoding_artifacts = ['�', '\x00', '\ufffd']
        for artifact in encoding_artifacts:
            if artifact in text:
                issues.append(f"Encoding artifact found: {repr(artifact)}")

        # Check word lengths
        words = re.findall(r'\b\w+\b', text)
        if words:
            avg_word_length = sum(len(w) for w in words) / len(words)
            short_words = sum(1 for w in words if len(w) < 2)
            short_word_ratio = short_words / len(words)

            if avg_word_length < 3:
                issues.append(f"Very short average word length: {avg_word_length:.1f}")

            if short_word_ratio > 0.4:  # More than 40% single-char words
                issues.append(f"High ratio of short words: {short_word_ratio:.2%}")

        # Check for column crossing (mid-sentence topic shift)
        # Look for patterns like "ques- trists" (question interrupted by psychiatrists)
        sentences = re.split(r'[.!?]+', text)
        for sent in sentences[:5]:  # Check first 5 sentences
            # Look for abrupt word changes mid-sentence
            if re.search(r'\w+-\s+[A-Z]\w+', sent):
                issues.append("Possible column crossing detected (mid-sentence capitalization)")
                break

        # Calculate quality score
        score = 1.0
        score -= min(special_ratio * 2, 0.3)  # Penalize special chars
        score -= len([i for i in issues if 'artifact' in i]) * 0.2
        score -= min(short_word_ratio, 0.3) if words else 0
        score = max(0.0, score)

        is_garbled = score < 0.7 or len(issues) >= 3
        confidence = 1.0 - score if is_garbled else score

        return {
            'is_garbled': is_garbled,
            'confidence': confidence,
            'issues': issues,
            'score': score
        }

    def process(self, text: str) -> Dict[str, any]:
        """
        Process text to fix common extraction issues.

        Args:
            text: Extracted text

        Returns:
            {
                'original_text': str,
                'fixed_text': str,
                'fixes_applied': [list of fixes],
                'quality_analysis': dict,
                'needs_review': bool
            }
        """
        original_text = text
        fixes_applied = []

        # Fix drop cap
        text, was_fixed = self.fix_drop_cap(text)
        if was_fixed:
            fixes_applied.append("Fixed drop cap (missing first letter)")

        # Fix broken words
        text, num_fixes = self.fix_broken_words(text)
        if num_fixes > 0:
            fixes_applied.append(f"Fixed {num_fixes} broken words across lines")

        # Analyze quality
        quality_analysis = self.detect_garbled_text(text)

        # Determine if needs manual review
        needs_review = (
            quality_analysis['is_garbled'] or
            quality_analysis['score'] < 0.8 or
            len(quality_analysis['issues']) >= 2
        )

        return {
            'original_text': original_text,
            'fixed_text': text,
            'fixes_applied': fixes_applied,
            'quality_analysis': quality_analysis,
            'needs_review': needs_review,
            'changed': text != original_text
        }


def quick_quality_check(text: str) -> float:
    """
    Quick quality check for extracted text.

    Args:
        text: Text to check

    Returns:
        Quality score 0.0-1.0
    """
    processor = TextPostProcessor()
    analysis = processor.detect_garbled_text(text)
    return analysis['score']
