import os
import sys
import time
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any

sys.path.insert(0, str(Path(__file__).parent.parent))


def test_vector_db():
    print("\n=== Testing Vector Database ===")

    from optimized.vector_db import (
        VectorConfig, FlatIndex, IVFIndex, HNSWIndex,
        VectorStore, HybridVectorIndex
    )
    import numpy as np

    config = VectorConfig(dimension=128, metric="cosine")

    print("Testing FlatIndex...")
    flat_index = FlatIndex(config)
    vectors = np.random.randn(100, 128).astype(np.float32)
    ids = [f"doc_{i}" for i in range(100)]

    flat_index.add(vectors, ids)
    assert flat_index.size() == 100, "FlatIndex size mismatch"

    query = np.random.randn(128).astype(np.float32)
    result_ids, scores = flat_index.search(query, k=5)
    assert len(result_ids[0]) == 5, "FlatIndex search result count mismatch"
    print(f"  FlatIndex: {flat_index.size()} vectors, search returned {len(result_ids[0])} results")

    print("Testing IVFIndex...")
    ivf_config = VectorConfig(dimension=128, metric="cosine", nlist=10, nprobe=3)
    ivf_index = IVFIndex(ivf_config)
    ivf_index.add(vectors, ids)
    assert ivf_index.size() == 100, "IVFIndex size mismatch"

    result_ids, scores = ivf_index.search(query, k=5)
    assert len(result_ids[0]) <= 5, "IVFIndex search result count mismatch"
    print(f"  IVFIndex: {ivf_index.size()} vectors, search returned {len(result_ids[0])} results")

    print("Testing HNSWIndex...")
    hnsw_config = VectorConfig(dimension=128, metric="cosine", M=16, ef_construction=100, ef_search=50)
    hnsw_index = HNSWIndex(hnsw_config)
    hnsw_index.add(vectors[:50], ids[:50])
    assert hnsw_index.size() == 50, "HNSWIndex size mismatch"

    result_ids, scores = hnsw_index.search(query, k=5)
    print(f"  HNSWIndex: {hnsw_index.size()} vectors, search returned {len(result_ids[0])} results")

    print("Testing VectorStore...")
    with tempfile.TemporaryDirectory() as tmpdir:
        store = VectorStore(config, tmpdir)
        store.add(vectors, ids)
        assert store.size() == 100, "VectorStore size mismatch"

        stats = store.stats()
        print(f"  VectorStore stats: {stats}")

        store.save()
        store.load()
        assert store.size() == 100, "VectorStore persistence failed"

    print("Vector Database tests passed!")
    return True


def test_sharding():
    print("\n=== Testing Sharding ===")

    from optimized.sharding import (
        ShardingConfig, DirectoryAnalyzer, ShardPlanner,
        ShardManager, ShardingFacade
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_project"
        test_dir.mkdir()

        (test_dir / "module1").mkdir()
        (test_dir / "module1" / "file1.py").write_text("def func1(): pass\n" * 100)
        (test_dir / "module1" / "file2.py").write_text("def func2(): pass\n" * 100)

        (test_dir / "module2").mkdir()
        (test_dir / "module2" / "file3.py").write_text("class Class1: pass\n" * 100)

        print("Testing DirectoryAnalyzer...")
        analyzer = DirectoryAnalyzer()
        structure = analyzer.analyze(test_dir)
        print(f"  Found {len(structure)} modules: {list(structure.keys())}")

        print("Testing ShardPlanner...")
        config = ShardingConfig(max_files_per_shard=2, max_shard_size=1024*1024)
        planner = ShardPlanner(config)
        shards = planner.plan(test_dir)
        print(f"  Planned {len(shards)} shards")
        for shard in shards:
            print(f"    - {shard.shard_id}: {shard.file_count} files")

        print("Testing ShardManager...")
        shard_storage = Path(tmpdir) / "shards"
        manager = ShardManager(str(shard_storage), config)

        shard_id = manager.assign_file("test_file.py", chunk_count=10, size_bytes=1000)
        print(f"  Assigned file to shard: {shard_id}")

        stats = manager.stats()
        print(f"  ShardManager stats: {stats}")

        print("Sharding tests passed!")
    return True


def test_cache():
    print("\n=== Testing Cache ===")

    from optimized.cache import (
        CacheConfig, LRUCache, LFUCache, PersistentCache,
        QueryCacheManager, CacheFacade
    )

    print("Testing LRUCache...")
    lru = LRUCache(max_size=5)
    for i in range(10):
        lru.put(f"key_{i}", f"value_{i}")

    assert lru.get("key_0") is None, "LRU should have evicted key_0"
    assert lru.get("key_9") == "value_9", "LRU should have key_9"

    stats = lru.stats()
    print(f"  LRUCache stats: {stats}")

    print("Testing LFUCache...")
    lfu = LFUCache(max_size=5)
    for i in range(5):
        lfu.put(f"key_{i}", f"value_{i}")

    for _ in range(10):
        lfu.get("key_0")
    lfu.get("key_1")

    lfu.put("key_new", "value_new")

    assert lfu.get("key_0") == "value_0", "LFU should keep frequently accessed key_0"
    print(f"  LFUCache stats: {lfu.stats()}")

    print("Testing PersistentCache...")
    with tempfile.TemporaryDirectory() as tmpdir:
        pc = PersistentCache(tmpdir)
        pc.put("test_key", {"data": "test_value"}, ttl_seconds=3600)

        result = pc.get("test_key")
        assert result == {"data": "test_value"}, "PersistentCache retrieval failed"
        print(f"  PersistentCache: stored and retrieved data successfully")

        stats = pc.stats()
        print(f"  PersistentCache stats: {stats}")

    print("Testing QueryCacheManager...")
    config = CacheConfig(max_size=100, ttl_seconds=3600)
    with tempfile.TemporaryDirectory() as tmpdir:
        config.persistence_path = tmpdir
        manager = QueryCacheManager(config)

        manager.put("test query", [{"id": "1", "score": 0.9}], top_k=10)
        result = manager.get("test query", top_k=10)
        assert result is not None, "QueryCacheManager retrieval failed"
        print(f"  QueryCacheManager: cached and retrieved query results")

        popular = manager.get_popular_queries()
        print(f"  Popular queries: {popular}")

    print("Cache tests passed!")
    return True


def test_incremental():
    print("\n=== Testing Incremental Updates ===")

    from optimized.incremental import (
        IncrementalConfig, FileHasher, ChangeDetector,
        ChangeBatcher, FileChange
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "test_project"
        test_dir.mkdir()

        test_file = test_dir / "test.py"
        test_file.write_text("def hello(): pass\n")

        state_file = Path(tmpdir) / "state.json"

        print("Testing FileHasher...")
        hasher = FileHasher()
        hash1 = hasher.compute("content1")
        hash2 = hasher.compute("content2")
        assert hash1 != hash2, "Hashes should be different"
        print(f"  FileHasher: computed hashes {hash1[:8]}... and {hash2[:8]}...")

        print("Testing ChangeDetector...")
        detector = ChangeDetector(str(state_file))

        extensions = {'.py'}
        added, modified, deleted = detector.detect_changes(test_dir, extensions)
        assert len(added) == 1, f"Should detect 1 added file, got {len(added)}"
        print(f"  Detected {len(added)} new files")

        content_hash = hasher.compute_file(test_file)
        detector.update_state(test_file, content_hash)
        print(f"  Updated state for {test_file}")

        added, modified, deleted = detector.detect_changes(test_dir, extensions)
        assert len(added) == 0 and len(modified) == 0, "No changes should be detected"
        print(f"  After state update: no changes detected")

        test_file.write_text("def hello(): print('hello')\n")
        added, modified, deleted = detector.detect_changes(test_dir, extensions)
        assert len(modified) == 1, "Should detect 1 modified file"
        print(f"  Detected {len(modified)} modified files")

        print("Testing ChangeBatcher...")
        batcher = ChangeBatcher()
        batcher.add_change(FileChange(path="file1.py", change_type="added"))
        batcher.add_change(FileChange(path="file2.py", change_type="modified"))

        batch = batcher.get_batch()
        assert len(batch.changes) == 2, "Batch should contain 2 changes"
        print(f"  Batched {len(batch.changes)} changes")

    print("Incremental update tests passed!")
    return True


def test_config():
    print("\n=== Testing Configuration ===")

    from optimized.config import (
        AppConfig, ConfigLoader, get_config,
        EmbeddingConfig, IndexConfig, ChunkConfig, YAML_AVAILABLE
    )

    print("Testing default config...")
    config = AppConfig()
    assert config.embedding.dimension == 384, "Default embedding dimension should be 384"
    assert config.chunk.max_size == 512, "Default chunk max_size should be 512"
    print(f"  Default config created: embedding.dim={config.embedding.dimension}")

    print("Testing config from environment...")
    os.environ["CODE_RAG_EMBEDDING_DIMENSION"] = "768"
    os.environ["CODE_RAG_CHUNK_MAX_SIZE"] = "1024"

    loader = ConfigLoader()
    config = loader.load()
    print(f"  Config from env: embedding.dimension={config.embedding.dimension}, chunk.max_size={config.chunk.max_size}")

    del os.environ["CODE_RAG_EMBEDDING_DIMENSION"]
    del os.environ["CODE_RAG_CHUNK_MAX_SIZE"]

    print("Testing config save/load...")
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / ("config.yaml" if YAML_AVAILABLE else "config.json")
        config = AppConfig()
        config.embedding.model = "test-model"
        config.chunk.max_size = 256

        loader = ConfigLoader(str(config_path))
        loader.config = config
        loader.save()

        loader2 = ConfigLoader(str(config_path))
        loaded_config = loader2.load()
        assert loaded_config.embedding.model == "test-model", "Config save/load failed"
        assert loaded_config.chunk.max_size == 256, "Config save/load failed"
        print(f"  Config saved and loaded successfully")

    print("Configuration tests passed!")
    return True


def test_monitoring():
    print("\n=== Testing Monitoring ===")

    from optimized.monitoring import (
        MetricsCollector, StructuredLogger, PerformanceMonitor,
        HealthChecker, Tracer
    )

    print("Testing MetricsCollector...")
    metrics = MetricsCollector("test")
    metrics.counter("requests", 5)
    metrics.counter("requests", 3)
    metrics.gauge("memory_mb", 512)
    metrics.histogram("latency", 0.1)
    metrics.histogram("latency", 0.2)
    metrics.histogram("latency", 0.15)

    all_metrics = metrics.get_metrics()
    assert "test_requests" in all_metrics, "Counter not found"
    assert all_metrics["test_requests"]["value"] == 8, "Counter value mismatch"
    print(f"  Metrics: {list(all_metrics.keys())}")

    prometheus_output = metrics.export_prometheus()
    assert "test_requests 8" in prometheus_output, "Prometheus export failed"
    print(f"  Prometheus export: {len(prometheus_output)} chars")

    print("Testing StructuredLogger...")
    with tempfile.TemporaryDirectory() as tmpdir:
        log_file = Path(tmpdir) / "test.log"
        logger = StructuredLogger("test", str(log_file))
        logger.info("Test message", key="value")

        content = log_file.read_text()
        assert "Test message" in content, "Log message not found"
        print(f"  Logged message to {log_file}")

    print("Testing PerformanceMonitor...")
    monitor = PerformanceMonitor(metrics)
    with monitor.track_time("test_operation"):
        time.sleep(0.01)

    print(f"  Tracked operation time")

    print("Testing HealthChecker...")
    checker = HealthChecker()
    checker.register_check("test_check", lambda: (True, "OK"))
    results = checker.run_checks()
    assert results["overall"] == "healthy", "Health check failed"
    print(f"  Health check results: {results['overall']}")

    print("Testing Tracer...")
    tracer = Tracer("test-service")
    span_id = tracer.start_span("operation1")
    tracer.add_tag("key", "value")
    tracer.end_span(span_id)

    trace = tracer.get_trace()
    assert len(trace) == 1, "Trace should have 1 span"
    print(f"  Created trace with {len(trace)} span(s)")

    print("Monitoring tests passed!")
    return True


def run_all_tests():
    print("=" * 60)
    print("Running Optimization Module Tests")
    print("=" * 60)

    results = {}

    tests = [
        ("Vector Database", test_vector_db),
        ("Sharding", test_sharding),
        ("Cache", test_cache),
        ("Incremental Updates", test_incremental),
        ("Configuration", test_config),
        ("Monitoring", test_monitoring),
    ]

    for name, test_func in tests:
        try:
            start_time = time.time()
            passed = test_func()
            elapsed = time.time() - start_time
            results[name] = {
                "passed": passed,
                "time_seconds": round(elapsed, 3)
            }
        except Exception as e:
            results[name] = {
                "passed": False,
                "error": str(e)
            }
            print(f"\n!!! {name} FAILED: {e}")

    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    total_passed = sum(1 for r in results.values() if r.get("passed", False))
    total_tests = len(results)

    for name, result in results.items():
        status = "✓ PASSED" if result.get("passed") else "✗ FAILED"
        time_str = f"({result.get('time_seconds', 0)}s)" if result.get("passed") else f"({result.get('error', 'error')})"
        print(f"  {name}: {status} {time_str}")

    print(f"\nTotal: {total_passed}/{total_tests} tests passed")

    return results


if __name__ == "__main__":
    run_all_tests()
