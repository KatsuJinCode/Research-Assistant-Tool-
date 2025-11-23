/**
 * Text Differ
 *
 * Provides word-level and character-level text diff functionality
 * using Longest Common Subsequence (LCS) algorithm
 */

class TextDiffer {
    /**
     * Generate word-level diff between two texts
     */
    static generateDiff(text1, text2) {
        const words1 = this.tokenize(text1);
        const words2 = this.tokenize(text2);

        const diff = this.lcs(words1, words2);

        return {
            added: diff.added,
            removed: diff.removed,
            common: diff.common,
            similarity: diff.common.length / Math.max(words1.length, words2.length)
        };
    }

    /**
     * Tokenize text into words
     */
    static tokenize(text) {
        return text.split(/\s+/).filter(word => word.length > 0);
    }

    /**
     * Longest Common Subsequence (LCS) algorithm
     */
    static lcs(arr1, arr2) {
        const m = arr1.length;
        const n = arr2.length;

        // Build DP table
        const dp = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

        for (let i = 1; i <= m; i++) {
            for (let j = 1; j <= n; j++) {
                if (arr1[i - 1] === arr2[j - 1]) {
                    dp[i][j] = dp[i - 1][j - 1] + 1;
                } else {
                    dp[i][j] = Math.max(dp[i - 1][j], dp[i][j - 1]);
                }
            }
        }

        // Backtrack to find sequences
        const common = [];
        const removed = [];
        const added = [];

        let i = m, j = n;
        while (i > 0 && j > 0) {
            if (arr1[i - 1] === arr2[j - 1]) {
                common.unshift(arr1[i - 1]);
                i--;
                j--;
            } else if (dp[i - 1][j] > dp[i][j - 1]) {
                removed.unshift(arr1[i - 1]);
                i--;
            } else {
                added.unshift(arr2[j - 1]);
                j--;
            }
        }

        while (i > 0) {
            removed.unshift(arr1[--i]);
        }

        while (j > 0) {
            added.unshift(arr2[--j]);
        }

        return { common, removed, added };
    }

    /**
     * Generate unified diff view (like git diff)
     */
    static generateUnifiedDiff(text1, text2, context = 3) {
        const lines1 = text1.split('\n');
        const lines2 = text2.split('\n');

        const diff = this.lcs(lines1, lines2);

        const hunks = [];
        let currentHunk = null;

        const addToHunk = (lineType, lineContent, lineNum1, lineNum2) => {
            if (!currentHunk) {
                currentHunk = {
                    oldStart: lineNum1,
                    oldCount: 0,
                    newStart: lineNum2,
                    newCount: 0,
                    lines: []
                };
                hunks.push(currentHunk);
            }

            currentHunk.lines.push({ type: lineType, content: lineContent });

            if (lineType === 'removed' || lineType === 'common') {
                currentHunk.oldCount++;
            }
            if (lineType === 'added' || lineType === 'common') {
                currentHunk.newCount++;
            }
        };

        // Generate hunks with context
        let line1 = 0, line2 = 0;

        diff.common.forEach((line, i) => {
            addToHunk('common', line, line1, line2);
            line1++;
            line2++;
        });

        diff.removed.forEach(line => {
            addToHunk('removed', line, line1, line2);
            line1++;
        });

        diff.added.forEach(line => {
            addToHunk('added', line, line1, line2);
            line2++;
        });

        return hunks;
    }

    /**
     * Render diff as HTML
     */
    static renderDiffHtml(text1, text2) {
        const diff = this.generateDiff(text1, text2);

        let html = '<div class="diff-viewer">';

        html += '<div class="diff-stats">';
        html += `<span class="added-count">+${diff.added.length}</span>`;
        html += `<span class="removed-count">-${diff.removed.length}</span>`;
        html += `<span class="similarity">${Math.round(diff.similarity * 100)}% similar</span>`;
        html += '</div>';

        html += '<div class="diff-content">';

        // Render side-by-side
        html += '<div class="diff-side-by-side">';

        html += '<div class="diff-left">';
        html += '<h4>Original</h4>';
        html += '<div class="diff-text">';
        diff.common.forEach(word => {
            html += `<span class="common">${this.escapeHtml(word)}</span> `;
        });
        diff.removed.forEach(word => {
            html += `<span class="removed">${this.escapeHtml(word)}</span> `;
        });
        html += '</div>';
        html += '</div>';

        html += '<div class="diff-right">';
        html += '<h4>Modified</h4>';
        html += '<div class="diff-text">';
        diff.common.forEach(word => {
            html += `<span class="common">${this.escapeHtml(word)}</span> `;
        });
        diff.added.forEach(word => {
            html += `<span class="added">${this.escapeHtml(word)}</span> `;
        });
        html += '</div>';
        html += '</div>';

        html += '</div>'; // diff-side-by-side

        html += '</div>'; // diff-content

        html += '</div>'; // diff-viewer

        return html;
    }

    /**
     * Calculate character-level edit distance (Levenshtein)
     */
    static levenshteinDistance(str1, str2) {
        const m = str1.length;
        const n = str2.length;

        const dp = Array(m + 1).fill(null).map(() => Array(n + 1).fill(0));

        for (let i = 0; i <= m; i++) dp[i][0] = i;
        for (let j = 0; j <= n; j++) dp[0][j] = j;

        for (let i = 1; i <= m; i++) {
            for (let j = 1; j <= n; j++) {
                if (str1[i - 1] === str2[j - 1]) {
                    dp[i][j] = dp[i - 1][j - 1];
                } else {
                    dp[i][j] = 1 + Math.min(
                        dp[i - 1][j],     // deletion
                        dp[i][j - 1],     // insertion
                        dp[i - 1][j - 1]  // substitution
                    );
                }
            }
        }

        return dp[m][n];
    }

    /**
     * Calculate normalized similarity (0-1) based on Levenshtein
     */
    static similarity(str1, str2) {
        const distance = this.levenshteinDistance(str1, str2);
        const maxLen = Math.max(str1.length, str2.length);
        return maxLen === 0 ? 1 : 1 - (distance / maxLen);
    }

    /**
     * Highlight differences inline
     */
    static highlightDifferences(text1, text2) {
        const words1 = this.tokenize(text1);
        const words2 = this.tokenize(text2);

        const diff = this.lcs(words1, words2);

        // Reconstruct with highlighting
        let highlighted1 = '';
        let highlighted2 = '';

        let i1 = 0, i2 = 0;
        let commonIndex = 0;

        while (i1 < words1.length || i2 < words2.length) {
            // Check if current words are in common
            if (commonIndex < diff.common.length &&
                words1[i1] === diff.common[commonIndex] &&
                words2[i2] === diff.common[commonIndex]) {
                highlighted1 += `<span class="common">${this.escapeHtml(words1[i1])}</span> `;
                highlighted2 += `<span class="common">${this.escapeHtml(words2[i2])}</span> `;
                i1++;
                i2++;
                commonIndex++;
            } else if (i1 < words1.length && diff.removed.includes(words1[i1])) {
                highlighted1 += `<span class="removed">${this.escapeHtml(words1[i1])}</span> `;
                i1++;
            } else if (i2 < words2.length && diff.added.includes(words2[i2])) {
                highlighted2 += `<span class="added">${this.escapeHtml(words2[i2])}</span> `;
                i2++;
            } else {
                // Fallback
                if (i1 < words1.length) {
                    highlighted1 += `${this.escapeHtml(words1[i1])} `;
                    i1++;
                }
                if (i2 < words2.length) {
                    highlighted2 += `${this.escapeHtml(words2[i2])} `;
                    i2++;
                }
            }
        }

        return {
            text1: highlighted1,
            text2: highlighted2,
            similarity: diff.similarity
        };
    }

    /**
     * Generate compact diff summary
     */
    static diffSummary(text1, text2) {
        const diff = this.generateDiff(text1, text2);

        return {
            addedWords: diff.added.length,
            removedWords: diff.removed.length,
            commonWords: diff.common.length,
            similarity: Math.round(diff.similarity * 100),
            addedText: diff.added.join(' '),
            removedText: diff.removed.join(' ')
        };
    }

    /**
     * Escape HTML
     */
    static escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Calculate Jaccard similarity
     */
    static jaccardSimilarity(text1, text2) {
        const words1 = new Set(this.tokenize(text1.toLowerCase()));
        const words2 = new Set(this.tokenize(text2.toLowerCase()));

        const intersection = new Set([...words1].filter(x => words2.has(x)));
        const union = new Set([...words1, ...words2]);

        return union.size === 0 ? 0 : intersection.size / union.size;
    }

    /**
     * Calculate cosine similarity (requires word vectors - simplified version)
     */
    static cosineSimilarity(text1, text2) {
        // Simplified: use word frequencies as vectors
        const words1 = this.tokenize(text1.toLowerCase());
        const words2 = this.tokenize(text2.toLowerCase());

        // Build vocabulary
        const vocab = new Set([...words1, ...words2]);

        // Create frequency vectors
        const vec1 = Array.from(vocab).map(word =>
            words1.filter(w => w === word).length
        );
        const vec2 = Array.from(vocab).map(word =>
            words2.filter(w => w === word).length
        );

        // Calculate cosine
        const dotProduct = vec1.reduce((sum, v, i) => sum + v * vec2[i], 0);
        const mag1 = Math.sqrt(vec1.reduce((sum, v) => sum + v * v, 0));
        const mag2 = Math.sqrt(vec2.reduce((sum, v) => sum + v * v, 0));

        return (mag1 === 0 || mag2 === 0) ? 0 : dotProduct / (mag1 * mag2);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = TextDiffer;
}
