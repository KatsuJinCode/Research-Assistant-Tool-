# Getting Started - For Complete Beginners

Follow these simple steps to get your AI Research Assistant running!

## Step 1: Open Your Terminal/Command Prompt

### On Windows:
1. Press `Windows Key + R`
2. Type `cmd` and press Enter
3. **OR** Search for "Command Prompt" in the Start menu

### On Mac:
1. Press `Cmd + Space`
2. Type `terminal` and press Enter

### On Linux:
1. Press `Ctrl + Alt + T`

## Step 2: Get the Code

Copy and paste this command, then press Enter:

```bash
git clone https://github.com/KatsuJinCode/Research-Assistant-Tool-.git
```

**What this does:** Downloads the research assistant to your computer.

If you see an error about `git not found`:
- **Windows:** Download Git from https://git-scm.com/download/win
- **Mac:** Run `xcode-select --install` in Terminal
- **Linux:** Run `sudo apt-get install git`

## Step 3: Go Into the Folder

Copy and paste this command:

```bash
cd Research-Assistant-Tool-
```

**What this does:** Moves you into the research assistant folder.

## Step 4: Run Setup

### On Windows:
```bash
setup.bat
```

### On Mac/Linux:
```bash
./setup.sh
```

**What this does:** Installs everything and asks you a few questions.

### What You'll Be Asked:

1. **"Do you have an OpenAI API key?"**
   - Type `y` if you have one, `n` if you don't
   - If yes, paste your API key when asked

2. **"Do you have an Anthropic API key?"**
   - Type `y` if you have one, `n` if you don't
   - If yes, paste your API key when asked

3. **"Which model?"**
   - Just press Enter to use the default (recommended)

**Don't have an API key yet?** See "Getting an API Key" section below.

## Step 5: Start Using It!

### On Windows:

```bash
# Create your first research project
research.bat create-project "My Research Project"

# Add a sample document (included with the tool)
research.bat add-document 1 sample_documents\ai_research.txt

# Search for something
research.bat search "artificial intelligence"

# Get an AI summary (requires API key)
research.bat summarize 1

# Ask questions (requires API key)
research.bat ask 1 "What are the main points?"
```

### On Mac/Linux:

```bash
# Create your first research project
./research.sh create-project "My Research Project"

# Add a sample document (included with the tool)
./research.sh add-document 1 sample_documents/ai_research.txt

# Search for something
./research.sh search "artificial intelligence"

# Get an AI summary (requires API key)
./research.sh summarize 1

# Ask questions (requires API key)
./research.sh ask 1 "What are the main points?"
```

## Getting an API Key

You need an API key to use the AI features (summarization, Q&A, etc.).

### Option 1: OpenAI (ChatGPT)

1. Go to https://platform.openai.com/
2. Click "Sign up" (or "Log in" if you have an account)
3. Go to "API Keys" in the menu
4. Click "Create new secret key"
5. **Copy the key** - it starts with `sk-` or `sk-proj-`
6. Run `setup.bat` (Windows) or `./setup.sh` (Mac/Linux) again
7. Paste your key when asked

**Cost:** ~$0.001-0.01 per summary or question

### Option 2: Anthropic (Claude)

1. Go to https://console.anthropic.com/
2. Click "Sign up" (or "Log in" if you have an account)
3. Go to "API Keys"
4. Click "Create Key"
5. **Copy the key** - it starts with `sk-ant-`
6. Run `setup.bat` (Windows) or `./setup.sh` (Mac/Linux) again
7. Paste your key when asked

**Cost:** ~$0.001-0.015 per summary or question

## Common Commands Cheat Sheet

### Windows:
```bash
# Create a project
research.bat create-project "Project Name"

# List all projects
research.bat list-projects

# Add a text file
research.bat add-document 1 path\to\your\file.txt

# Search everything
research.bat search "your search term"

# View a document
research.bat view 1

# Summarize with AI
research.bat summarize 1

# Ask questions
research.bat ask 1 "Your question?"

# Get help
research.bat --help
```

### Mac/Linux:
```bash
# Create a project
./research.sh create-project "Project Name"

# List all projects
./research.sh list-projects

# Add a text file
./research.sh add-document 1 path/to/your/file.txt

# Search everything
./research.sh search "your search term"

# View a document
./research.sh view 1

# Summarize with AI
./research.sh summarize 1

# Ask questions
./research.sh ask 1 "Your question?"

# Get help
./research.sh --help
```

## Troubleshooting

### "git is not recognized" or "git: command not found"

**You need to install Git:**
- Windows: https://git-scm.com/download/win
- Mac: Open Terminal and run `xcode-select --install`
- Linux: Run `sudo apt-get install git` or `sudo yum install git`

### "python is not recognized" or "python: command not found"

**You need to install Python:**
- Download from https://www.python.org/downloads/
- **Important:** On Windows, check "Add Python to PATH" during installation

### Setup window closes immediately (Windows)

**Don't double-click!** Open Command Prompt first, then:
```bash
cd Research-Assistant-Tool-
setup.bat
```

### "No module named 'openai'" or similar error

Run the setup again:
```bash
setup.bat        # Windows
./setup.sh       # Mac/Linux
```

### Forgot where I downloaded it?

The folder is probably in your home directory. Try:

**Windows:**
```bash
cd %USERPROFILE%
dir Research-Assistant-Tool-
```

**Mac/Linux:**
```bash
cd ~
ls Research-Assistant-Tool-
```

## What Can I Do Without an API Key?

Even without an API key, you can:
- ✅ Create research projects
- ✅ Add and organize documents (.txt and .md files)
- ✅ Search across all your documents
- ✅ View documents
- ✅ Manage your research library

**AI features need an API key:**
- ❌ Summarization
- ❌ Question answering
- ❌ Key point extraction
- ❌ Auto-tagging

## Next Steps

1. **Add your own documents:**
   ```bash
   research.bat add-document 1 C:\path\to\your\document.txt
   ```

2. **Try different AI features:**
   - Summarize: Get a quick overview
   - Ask: Get specific questions answered
   - Keypoints: Extract main ideas
   - Auto-tag: Organize automatically

3. **Read more documentation:**
   - [QUICKSTART.md](QUICKSTART.md) - Quick reference
   - [MULTI_PROVIDER_GUIDE.md](MULTI_PROVIDER_GUIDE.md) - OpenAI vs Anthropic
   - [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) - Advanced examples

## Still Stuck?

1. Make sure you're in the right folder:
   ```bash
   cd Research-Assistant-Tool-
   ```

2. Check if Python is installed:
   ```bash
   python --version
   ```

3. Re-run the setup:
   ```bash
   setup.bat        # Windows
   ./setup.sh       # Mac/Linux
   ```

4. Check the troubleshooting section above

---

**You're all set!** Start organizing your research with AI assistance! 🚀
