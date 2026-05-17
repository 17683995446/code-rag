"""
产品级单元测试
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import (
    CodeRAG,
    EmbeddingEngine,
    VectorStore,
    RAGImplementation,
    get_settings,
    CodeParser,
    BM25Index,
    HybridSearch,
    LRUCache,
    TTLCache
)


def test_embedding_engine():
    """测试EmbeddingEngine"""
    print("🧪 测试: EmbeddingEngine")

    engine = EmbeddingEngine()

    # 单文本编码
    result = engine.encode("Hello world")
    assert result is not None
    assert len(result.vector) > 0
    assert result.dimension > 0

    print(f"  - 单文本编码: 维度 {result.dimension}, 模型: {result.model}")

    # 批量编码
    results = engine.encode_batch(["Hello", "World", "Test"])
    assert len(results) == 3
    for r in results:
        assert len(r.vector) == result.dimension

    print("  ✅ EmbeddingEngine测试通过")
    return True


def test_vector_store():
    """测试VectorStore"""
    print("🧪 测试: VectorStore")

    store = VectorStore(embedding_dimension=384)

    # 添加文档
    embeddings = [[0.1] * 384, [0.2] * 384, [0.3] * 384]
    documents = ["文档1", "文档2", "文档3"]
    metadatas = [{"id": i} for i in range(3)]

    store.add(embeddings, documents, metadatas)
    assert len(store.documents) == 3

    # 搜索
    results = store.search([0.15] * 384, k=2)
    assert len(results) <= 2

    print(f"  - 添加文档: {len(documents)} 个")
    print(f"  - 搜索结果: {len(results)} 个")

    print("  ✅ VectorStore测试通过")
    return True


def test_code_rag():
    """测试CodeRAG"""
    print("🧪 测试: CodeRAG")

    rag = CodeRAG(implementation="simplified")

    # 索引
    rag.index("/tmp/demo_code")

    # 搜索
    results = rag.search("FAISS向量数据库", k=3)
    assert len(results) > 0

    print(f"  - 搜索结果: {len(results)} 个")

    # 问答
    answer = rag.ask("什么是FAISS?")
    assert answer.success is True
    assert len(answer.answer) > 0
    assert len(answer.sources) > 0

    print(f"  - 问答成功: {len(answer.sources)} 个来源")

    print("  ✅ CodeRAG测试通过")
    return True


def test_code_parser():
    """测试代码解析器"""
    print("🧪 测试: CodeParser")

    parser = CodeParser()

    # 创建测试文件
    test_code = '''class TestClass:
    def __init__(self):
        self.value = 0
    
    def test_method(self, x):
        return x * 2

def test_function():
    return "hello"
'''

    test_file = Path("/tmp/test_code.py")
    test_file.write_text(test_code)

    # 解析文件
    doc = parser.parse_file(str(test_file))
    assert doc is not None
    assert len(doc.chunks) > 0

    print(f"  - 解析文件: {doc.file_path}")
    print(f"  - 语言: {doc.language}")
    print(f"  - 代码块数量: {len(doc.chunks)}")

    # 清理
    test_file.unlink(missing_ok=True)

    print("  ✅ CodeParser测试通过")
    return True


def test_bm25_index():
    """测试BM25索引"""
    print("🧪 测试: BM25Index")

    index = BM25Index()

    # 添加文档（使用英文，因为当前分词器对中文支持有限）
    docs = [
        "FAISS is a high-performance vector database from Meta",
        "Sentence-Transformers provides high-quality text embeddings",
        "Python is an excellent programming language",
        "JavaScript is used for frontend development"
    ]
    metadatas = [{"id": i} for i in range(len(docs))]

    index.add_documents(docs, metadatas)
    assert len(index) == 4

    # 搜索
    results = index.search("FAISS vector database", k=2)
    print(f"  - 搜索结果数量: {len(results)}")
    for r in results:
        print(f"    - {r.score:.4f}: {r.text[:50]}")

    print(f"  - 添加文档: {len(docs)} 个")
    print(f"  - 搜索结果: {len(results)} 个")

    print("  ✅ BM25Index测试通过")
    return True


def test_hybrid_search():
    """测试混合搜索"""
    print("🧪 测试: HybridSearch")

    hybrid = HybridSearch(bm25_weight=0.5, vector_weight=0.5)

    # 添加文档
    docs = [
        "FAISS是Meta开源的高性能向量数据库",
        "Sentence-Transformers提供高质量的文本embedding"
    ]
    hybrid.add_documents(docs)

    # 创建模拟的向量搜索结果
    class MockVectorResult:
        def __init__(self, text, score):
            self.text = text
            self.score = score
            self.metadata = {}

    vector_results = [
        MockVectorResult(docs[0], 0.9),
        MockVectorResult(docs[1], 0.8)
    ]

    # 混合搜索
    results = hybrid.search("FAISS", vector_results, k=2)
    assert len(results) > 0

    print(f"  - 混合搜索结果: {len(results)} 个")

    print("  ✅ HybridSearch测试通过")
    return True


def test_lru_cache():
    """测试LRU缓存"""
    print("🧪 测试: LRUCache")

    cache = LRUCache(max_size=3)

    # 添加条目
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")

    assert len(cache) == 3

    # 获取
    assert cache.get("key1") == "value1"
    assert cache.get("key2") == "value2"

    # 添加新条目，应该淘汰最旧的
    cache.set("key4", "value4")
    assert len(cache) == 3
    assert cache.get("key3") is None  # key3被淘汰

    # 统计
    stats = cache.stats()
    assert stats['hits'] > 0

    print(f"  - 缓存大小: {len(cache)}")
    print(f"  - 命中率: {stats['hit_rate']:.2%}")

    print("  ✅ LRUCache测试通过")
    return True


def test_ttl_cache():
    """测试TTL缓存"""
    print("🧪 测试: TTLCache")

    cache = TTLCache(default_ttl=0.1)

    # 添加条目
    cache.set("key1", "value1")
    cache.set("key2", "value2", ttl=10)  # 永不过期

    assert cache.get("key1") == "value1"

    # 等待过期
    time.sleep(0.15)
    assert cache.get("key1") is None  # 已过期
    assert cache.get("key2") == "value2"  # 未过期

    # 清理过期
    cleaned = cache.cleanup_expired()
    print(f"  - 清理过期条目: {cleaned} 个")

    print("  ✅ TTLCache测试通过")
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("  🧪 产品级单元测试")
    print("=" * 60)

    all_passed = True
    tests = [
        ("EmbeddingEngine", test_embedding_engine),
        ("VectorStore", test_vector_store),
        ("CodeRAG", test_code_rag),
        ("CodeParser", test_code_parser),
        ("BM25Index", test_bm25_index),
        ("HybridSearch", test_hybrid_search),
        ("LRUCache", test_lru_cache),
        ("TTLCache", test_ttl_cache),
    ]

    for test_name, test_func in tests:
        try:
            print()
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"  ❌ {test_name}测试失败: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("  ✅ 所有测试通过！")
    else:
        print("  ❌ 部分测试失败")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
