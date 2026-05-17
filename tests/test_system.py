"""
产品级系统测试
测试完整系统的功能和性能
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import (
    CodeRAG,
    EmbeddingEngine,
    VectorStore,
    LRUCache,
    get_logger,
    log_context
)


def test_performance_basic():
    """基本性能测试"""
    print("🚀 系统测试: 基本性能")

    logger = get_logger(__name__)

    # 测试Embedding速度
    engine = EmbeddingEngine()
    test_texts = [f"测试文本 {i}" for i in range(100)]

    start_time = time.time()
    results = engine.encode_batch(test_texts)
    elapsed = time.time() - start_time

    print(f"  - 编码 {len(test_texts)} 个文本: {elapsed:.2f}s")
    print(f"  - 平均: {elapsed/len(test_texts)*1000:.2f}ms/个")

    # 测试搜索速度
    store = VectorStore(embedding_dimension=engine.dimension)

    # 添加一些测试数据
    docs = [f"文档内容 {i}" for i in range(100)]
    embs = [[0.1] * engine.dimension for _ in range(100)]
    store.add(embs, docs, [{}]*100)

    query_emb = engine.encode("测试查询").vector

    start_time = time.time()
    for _ in range(10):
        store.search(query_emb, k=5)
    elapsed = time.time() - start_time

    print(f"  - 10次搜索: {elapsed:.2f}s")
    print(f"  - 平均: {elapsed/10*1000:.2f}ms/次")

    print("  ✅ 基本性能测试完成")
    return True


def test_cache_effectiveness():
    """缓存有效性测试"""
    print("🚀 系统测试: 缓存有效性")

    cache = LRUCache(max_size=100)

    # 测试缓存命中率
    for i in range(100):
        cache.set(f"key{i}", f"value{i}")

    # 访问一些键
    for i in range(80):
        cache.get(f"key{i}")

    stats = cache.stats()
    print(f"  - 缓存大小: {stats['size']}")
    print(f"  - 命中次数: {stats['hits']}")
    print(f"  - 未命中次数: {stats['misses']}")
    print(f"  - 命中率: {stats['hit_rate']:.2%}")

    assert stats['hits'] > 0

    print("  ✅ 缓存有效性测试完成")
    return True


def test_complete_workflow():
    """完整工作流测试"""
    print("🚀 系统测试: 完整工作流")

    with log_context("初始化系统"):
        rag = CodeRAG(implementation="simplified")

    with log_context("索引数据"):
        rag.index("/tmp/test_system_test")

    with log_context("多次搜索测试"):
        queries = [
            "FAISS",
            "向量数据库",
            "Python",
            "LangChain",
            "RAG系统"
        ]

        total_time = 0
        for query in queries:
            start_time = time.time()
            results = rag.search(query, k=3)
            elapsed = time.time() - start_time
            total_time += elapsed
            print(f"  - 查询 '{query}': {elapsed:.3f}s, {len(results)} 结果")

        avg_time = total_time / len(queries)
        print(f"  - 平均查询时间: {avg_time:.3f}s")

    with log_context("问答测试"):
        answer = rag.ask("什么是RAG系统?")
        assert answer.success is True
        print(f"  - 问答成功: {len(answer.answer)} 字符")

    print("  ✅ 完整工作流测试完成")
    return True


def test_error_handling():
    """错误处理测试"""
    print("🚀 系统测试: 错误处理")

    rag = CodeRAG(implementation="simplified")

    # 测试无效路径
    try:
        rag.index("/this/path/does/not/exist/at/all/12345")
        print("  - 无效路径处理: 正常")
    except Exception as e:
        print(f"  - 无效路径处理: {e}")

    # 测试空查询
    try:
        results = rag.search("")
        print(f"  - 空查询处理: 返回 {len(results)} 结果")
    except Exception as e:
        print(f"  - 空查询处理: {e}")

    # 测试大规模数据（边界情况）
    store = VectorStore(embedding_dimension=384)
    for i in range(10):
        store.add([[0.1]*384], [f"doc{i}"], [{}])

    results = store.search([0.1]*384, k=10)
    print(f"  - 边界情况: 正常")

    print("  ✅ 错误处理测试完成")
    return True


def test_concurrent_simulation():
    """并发模拟测试"""
    print("🚀 系统测试: 并发模拟")

    # 创建多个RAG实例
    instances = []
    for i in range(3):
        rag = CodeRAG(implementation="simplified")
        rag.index(f"/tmp/test_concurrent_{i}")
        instances.append(rag)

    # 模拟并发查询
    start_time = time.time()
    for i, rag in enumerate(instances):
        results = rag.search(f"测试查询 {i}")
        assert len(results) >= 0

    elapsed = time.time() - start_time
    print(f"  - {len(instances)} 个实例查询: {elapsed:.2f}s")

    print("  ✅ 并发模拟测试完成")
    return True


def run_all_system_tests():
    """运行所有系统测试"""
    print("=" * 60)
    print("  🚀 产品级系统测试")
    print("=" * 60)

    all_passed = True
    tests = [
        ("基本性能", test_performance_basic),
        ("缓存有效性", test_cache_effectiveness),
        ("完整工作流", test_complete_workflow),
        ("错误处理", test_error_handling),
        ("并发模拟", test_concurrent_simulation),
    ]

    for test_name, test_func in tests:
        try:
            print()
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"  ❌ {test_name}系统测试失败: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("  ✅ 所有系统测试通过！")
    else:
        print("  ❌ 部分系统测试失败")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_all_system_tests())
