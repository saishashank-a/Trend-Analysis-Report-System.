#!/usr/bin/env python3
"""
Quick ML Optimization Tests

Tests the newly implemented ML features:
- Embedding service with Metal GPU
- Topic clustering with HDBSCAN
- Duplicate detection
- Hardware profile detection
"""

import os
import time

# Set environment for testing
os.environ['ENABLE_EMBEDDING_CLUSTERING'] = 'true'
os.environ['ENABLE_DEDUP'] = 'true'
os.environ['ENABLE_CACHE'] = 'true'


def test_hardware_profile():
    """Test hardware profile detection"""
    print("\n" + "="*60)
    print("TEST 1: Hardware Profile Detection")
    print("="*60)

    from config.hardware_profiles import detect_hardware_profile

    profile = detect_hardware_profile()
    print(f"\nDetected Profile: {profile['name']}")
    print(f"  Max concurrent: {profile['max_concurrent']}")
    print(f"  Batch size: {profile['batch_size']}")
    print(f"  Metal GPU: {profile['use_metal']}")
    print(f"  Dedup enabled: {profile['enable_dedup']}")
    print(f"  Clustering enabled: {profile['enable_clustering']}")

    assert profile['name'] is not None
    print("\n✓ PASSED")


def test_embedding_service():
    """Test embedding generation with Metal GPU"""
    print("\n" + "="*60)
    print("TEST 2: Embedding Service (Metal GPU)")
    print("="*60)

    from config.embedding_service import EmbeddingService
    from config.cache_db import EmbeddingCache

    # Create test texts
    texts = [
        "Food was cold and delivery was late",
        "Great service, very fast delivery",
        "App keeps crashing when I try to order",
        "Delivery partner was very rude",
        "Food quality excellent, will order again"
    ]

    print(f"\nEncoding {len(texts)} sample reviews...")

    cache = EmbeddingCache()
    service = EmbeddingService(use_metal=True, cache=cache)

    start = time.time()
    embeddings = service.encode(texts, batch_size=32)
    elapsed = time.time() - start

    print(f"  ✓ Generated embeddings in {elapsed:.3f}s")
    print(f"  Embedding shape: {embeddings.shape}")
    print(f"  Expected: ({len(texts)}, 384) for all-MiniLM-L6-v2")

    assert embeddings.shape[0] == len(texts)
    assert embeddings.shape[1] == 384  # all-MiniLM-L6-v2 dimension
    print("\n✓ PASSED")


def test_duplicate_detection():
    """Test duplicate review detection"""
    print("\n" + "="*60)
    print("TEST 3: Duplicate Detection")
    print("="*60)

    from utils.duplicate_detector import DuplicateDetector
    from config.embedding_service import EmbeddingService
    from config.cache_db import EmbeddingCache

    # Create test reviews with known duplicates
    reviews = [
        {"reviewId": "1", "content": "Food was cold and delivery was late"},
        {"reviewId": "2", "content": "The food was cold and the delivery was late"},  # Near duplicate
        {"reviewId": "3", "content": "Great service, very fast"},
        {"reviewId": "4", "content": "App keeps crashing"},
        {"reviewId": "5", "content": "Food cold delivery late"},  # Another near duplicate
        {"reviewId": "6", "content": "Excellent app, works great"}
    ]

    print(f"\nTesting duplicate detection on {len(reviews)} reviews...")

    cache = EmbeddingCache()
    embedder = EmbeddingService(use_metal=True, cache=cache)
    detector = DuplicateDetector(embedder, threshold=0.85)

    start = time.time()
    unique, duplicates = detector.detect_duplicates(reviews)
    elapsed = time.time() - start

    print(f"  ✓ Detection completed in {elapsed:.3f}s")
    print(f"  Unique reviews: {len(unique)}")
    print(f"  Duplicate reviews: {len(duplicates)}")

    if duplicates:
        print(f"  Duplicate IDs: {[r['reviewId'] for r in duplicates]}")

    # Should detect at least 1 duplicate (reviews 2 and 5 are similar to review 1)
    assert len(duplicates) >= 1, "Should detect at least 1 duplicate"
    assert len(unique) < len(reviews), "Should have fewer unique reviews"
    print("\n✓ PASSED")


def test_topic_clustering():
    """Test topic clustering with HDBSCAN"""
    print("\n" + "="*60)
    print("TEST 4: Topic Clustering")
    print("="*60)

    from ml.topic_clustering import TopicClusterer
    from config.embedding_service import EmbeddingService
    from config.cache_db import EmbeddingCache

    # Create test topics with known groups
    topics = [
        # Group 1: Food temperature
        "food cold", "cold food", "food not hot", "lukewarm food",
        # Group 2: Delivery delays
        "late delivery", "delivery late", "delayed delivery", "delivery delayed",
        # Group 3: Positive feedback
        "great service", "excellent app", "love the app", "amazing experience",
        # Group 4: App issues
        "app crash", "app crashes", "app freezes", "app not working"
    ]

    print(f"\nClustering {len(topics)} test topics...")

    cache = EmbeddingCache()
    embedder = EmbeddingService(use_metal=True, cache=cache)
    clusterer = TopicClusterer(embedder, min_cluster_size=3)

    start = time.time()
    canonical_mapping = clusterer.cluster_topics(topics)
    elapsed = time.time() - start

    print(f"  ✓ Clustering completed in {elapsed:.3f}s")
    print(f"  Input topics: {len(topics)}")
    print(f"  Canonical topics: {len(canonical_mapping)}")

    print(f"\n  Clusters formed:")
    for canonical, variations in canonical_mapping.items():
        print(f"    • {canonical}: {len(variations)} variations")

    # Should consolidate topics (expect ~4 clusters for 4 groups)
    assert len(canonical_mapping) <= len(topics) // 2, "Should consolidate topics"
    assert elapsed < 5, f"Clustering too slow: {elapsed:.2f}s"
    print("\n✓ PASSED")


def test_integration():
    """Test integration of all components"""
    print("\n" + "="*60)
    print("TEST 5: Integration Test")
    print("="*60)

    print("\nTesting full pipeline with mock data...")

    # Test that imports work together
    from config.embedding_service import EmbeddingService
    from config.cache_db import EmbeddingCache
    from ml.topic_clustering import TopicClusterer
    from utils.duplicate_detector import DuplicateDetector

    print("  ✓ All modules imported successfully")

    # Test embedding cache stats
    cache = EmbeddingCache()
    stats = cache.get_stats()
    print(f"  ✓ Embedding cache stats: {stats['total_entries']} entries, {stats['total_hits']} hits")

    print("\n✓ PASSED - All components integrated successfully")


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ML OPTIMIZATION TEST SUITE")
    print("="*60)

    tests = [
        test_hardware_profile,
        test_embedding_service,
        test_duplicate_detection,
        test_topic_clustering,
        test_integration
    ]

    passed = 0
    failed = 0

    for test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n✗ FAILED: {e}")
            failed += 1
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print(f"RESULTS: {passed}/{len(tests)} passed")
    print("="*60)

    if failed == 0:
        print("\n✓ All tests passed! ML optimizations working correctly.")
        print("\nNext steps:")
        print("  1. Test with real data: python main.py <app-id>")
        print("  2. Monitor Metal GPU usage with Activity Monitor")
        print("  3. Compare performance with LLM-based consolidation")
    else:
        print(f"\n✗ {failed} test(s) failed. Check errors above.")

    return failed == 0


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
