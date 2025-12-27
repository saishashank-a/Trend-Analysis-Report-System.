#!/bin/bash
# Clear topic-related caches to ensure app-specific analysis
# Run this before analyzing a new app to get accurate, app-specific topics

echo "Clearing topic-related caches..."

# Clear embedding cache (topics get cached here)
if [ -f "cache/embedding_cache.db" ]; then
    echo "  Clearing embedding cache..."
    rm cache/embedding_cache.db
    echo "  ✓ Embedding cache cleared"
fi

# Clear LLM response cache (topic extraction responses cached here)
if [ -f "cache/llm_cache.db" ]; then
    echo "  Clearing LLM cache..."
    rm cache/llm_cache.db
    echo "  ✓ LLM cache cleared"
fi

# Keep jobs.db and review caches (those are app-specific already)
echo ""
echo "✓ Topic caches cleared!"
echo "  Jobs database preserved"
echo "  Review caches preserved"
echo ""
echo "You can now analyze a new app and get app-specific topics."
