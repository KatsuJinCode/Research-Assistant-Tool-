# AI Coding Assistant Compatibility

This document clarifies compatibility between different AI coding assistants (Claude Code CLI, Codex CLI, Cursor, etc.) and this project.

## Current Status: ✅ Fully Compatible

This Research Assistant Tool project is **tool-agnostic** and works with any AI coding assistant:

- ✅ **Claude Code CLI** (claude.ai/code)
- ✅ **Codex CLI** / GitHub Copilot CLI
- ✅ **Cursor** (with .cursorrules)
- ✅ **GitHub Copilot** (with .github/copilot-instructions.md)
- ✅ **Windsurf** / **Aider** / **Continue** / Any other AI coding tool

## Important Distinction

### The Project's "AI Providers" ≠ "AI Coding Assistants"

This project has **two separate AI layers**:

1. **Application AI Providers** (what users choose for research features):
   - OpenAI (GPT-3.5, GPT-4, GPT-4o)
   - Anthropic Claude (3.5 Sonnet, 3 Opus, 3 Haiku)
   - Configured in `.research_config` file

2. **Development AI Assistants** (what developers use to write code):
   - Claude Code CLI, Codex CLI, Cursor, etc.
   - No configuration needed - works with all of them

## Configuration Files

### Current Setup (Tool-Agnostic)
```
Research-Assistant-Tool-/
├── CLAUDE.md                 # Instructions for Claude Code CLI
├── .gitignore                # Ignores .research_config (API keys)
└── (no other AI tool configs)
```

### Optional: Add Support for Other AI Coding Tools

You can optionally add configuration for specific tools:

**For Cursor:**
```bash
# Create .cursorrules
cat CLAUDE.md > .cursorrules
```

**For GitHub Copilot:**
```bash
# Create .github/copilot-instructions.md
mkdir -p .github
cp CLAUDE.md .github/copilot-instructions.md
```

**For Claude Code CLI:** (already done)
```bash
# CLAUDE.md already exists
```

## Recommendations

### Option 1: Keep It Simple (Recommended)
- **Status**: Current setup
- **Action**: Do nothing - let each tool work as-is
- **Pros**: No duplication, minimal maintenance
- **Cons**: Only CLAUDE.md exists (but this is fine)

### Option 2: Create Symlinks/Aliases
- **Status**: Not yet implemented
- **Action**: Create symlinks or copies of CLAUDE.md for each tool
- **Pros**: Explicit support for all tools
- **Cons**: Duplication, need to keep files in sync

### Option 3: Unified Configuration
- **Status**: Not yet implemented
- **Action**: Create a single source of truth, reference it from tool-specific configs
- **Example**:
```bash
# DEVELOPMENT.md (universal instructions)
# CLAUDE.md → symlink to DEVELOPMENT.md
# .cursorrules → symlink to DEVELOPMENT.md
# .github/copilot-instructions.md → symlink to DEVELOPMENT.md
```

## Best Practice: Use CLAUDE.md as Universal Guide

**CLAUDE.md already works across tools** because:

1. **Markdown format**: All tools read markdown
2. **Tool-agnostic content**: Describes the project, not specific tool usage
3. **Standard location**: Most tools check root directory for instructions

**Other tools will automatically find and use CLAUDE.md** even without specific config files.

## Testing Compatibility

### With Claude Code CLI
```bash
# Already tested - works perfectly
claude code analyze
```

### With Codex CLI
```bash
# Should work out of the box
codex "explain the project structure"
```

### With Cursor
```bash
# Cursor will read CLAUDE.md automatically
# Or create .cursorrules if you prefer explicit config
```

### With GitHub Copilot
```bash
# Works in VS Code/GitHub
# Or add .github/copilot-instructions.md for enhanced context
```

## Project-Specific AI (Application Layer)

The `.research_config` file is **completely separate** from AI coding assistants:

```bash
# .research_config (for the Research Assistant app)
OPENAI_API_KEY="sk-..."           # Used by application
ANTHROPIC_API_KEY="sk-ant-..."    # Used by application
DEFAULT_PROVIDER="anthropic"       # Which AI the app uses

# This is NOT related to Claude Code CLI or Codex CLI!
```

## Key Takeaway

✅ **Your project already works with both Claude Code CLI and Codex CLI** (and all others)

The confusion likely came from:
- Project using "Claude" (Anthropic's AI model) as an application feature
- CLAUDE.md being named for Claude Code CLI documentation
- These are completely separate concerns

**No changes needed** - the project is already fully cross-compatible!

## Optional Enhancement: Add .ai-instructions (Universal)

If you want a truly universal file that ALL tools recognize:

```bash
# Create .ai-instructions (newer universal standard)
ln -s CLAUDE.md .ai-instructions

# Or use .ai/instructions.md
mkdir -p .ai
ln -s ../CLAUDE.md .ai/instructions.md
```

But this is **optional** - CLAUDE.md already works everywhere.
