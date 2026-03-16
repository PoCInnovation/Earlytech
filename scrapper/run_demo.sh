#!/bin/bash

# Quick Demo - Article Dispatch System
# Shows that articles are dispatched to users correctly

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🚀 QUICK DEMO - Article Dispatch System"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "This script will demonstrate that articles are dispatched"
echo "automatically to users based on keyword matching via embeddings."
echo ""
echo "Press Enter to continue..."
read

echo ""
echo "──────────────────────────────────────────────────────────────"
echo "Step 1/3: Setup users with keywords"
echo "──────────────────────────────────────────────────────────────"
echo ""

python3 examples_user_keywords.py setup

echo ""
echo "Press Enter to continue to demo..."
read

echo ""
echo "──────────────────────────────────────────────────────────────"
echo "Step 2/3: Run complete dispatch demonstration"
echo "──────────────────────────────────────────────────────────────"
echo ""

python3 demo_dispatch.py

echo ""
echo "Press Enter to continue to verification..."
read

echo ""
echo "──────────────────────────────────────────────────────────────"
echo "Step 3/3: Quick verification test"
echo "──────────────────────────────────────────────────────────────"
echo ""

python3 quick_test_dispatch.py

echo ""
echo "════════════════════════════════════════════════════════════════"
echo "✅ DEMO COMPLETE!"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "What you just saw:"
echo "  ✅ Articles embedded"
echo "  ✅ Compared with user keywords (cosine similarity)"
echo "  ✅ Matched articles dispatched to users"
echo "  ✅ Users can access their personalized feeds"
echo ""
echo "To see a user's feed:"
echo "  python3 examples_user_keywords.py feed 1"
echo ""
echo "To monitor dispatches in real-time:"
echo "  python3 monitor_dispatch.py monitor"
echo ""
echo "To view statistics:"
echo "  python3 monitor_dispatch.py stats"
echo ""
echo "To start the scraper (articles auto-dispatched):"
echo "  python3 main.py watch"
echo ""
echo "Documentation:"
echo "  • START_HERE.md - Quick start guide"
echo "  • README_DISPATCH.md - Complete overview"
echo "  • INDEX.md - Index of all files"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo "🎉 The system is working and ready for production!"
echo "════════════════════════════════════════════════════════════════"
echo ""
