#!/bin/bash
# Demo script for CLI Research Assistant
# Shows all features of the system

set -e  # Exit on error

CLI="python3 cli_assistant_enhanced.py"

echo "=================================="
echo "CLI Research Assistant - Demo"
echo "=================================="
echo

echo "📦 Step 1: Installing dependencies..."
python3 setup_cli.py
echo

echo "📁 Step 2: Creating research projects..."
$CLI create-project "AI Research" --description "Exploring artificial intelligence and machine learning"
$CLI create-project "Climate Science" --description "Research on climate change and sustainability"
echo

echo "📄 Step 3: Adding documents..."
$CLI add-document 1 sample_documents/ai_research.txt
$CLI add-document 2 sample_documents/climate_change.txt
echo

echo "📋 Step 4: Listing projects..."
$CLI list-projects
echo

echo "🔍 Step 5: Searching documents..."
echo "Searching for 'transformer':"
$CLI search "transformer"
echo

echo "Searching for 'climate' in project 2:"
$CLI search "climate" --project 2
echo

echo "📊 Step 6: Project summary..."
$CLI summary 1
echo

echo "👀 Step 7: Viewing a document (first 20 lines)..."
$CLI view 1 | head -30
echo

echo "=================================="
echo "✅ Demo Complete!"
echo "=================================="
echo
echo "🤖 AI Features (require OpenAI API key):"
echo
echo "To use AI features, set your API key:"
echo "  export OPENAI_API_KEY='your-key-here'"
echo
echo "Then try:"
echo "  $CLI summarize 1           # Summarize document"
echo "  $CLI ask 1 'question'      # Ask questions"
echo "  $CLI keypoints 1           # Extract key points"
echo "  $CLI auto-tag 1            # Generate tags"
echo
echo "Data stored in: ./data/"
echo "To reset: rm -rf ./data/"
echo
