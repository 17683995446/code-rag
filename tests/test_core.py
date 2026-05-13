"""
产品级单元测试
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import (
    CodeRAG,
    EmbeddingEngine,
    VectorStore,
    RAGImplementation,
    get_settings
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


def run_all_tests():
    """运行所有测试"""
    print("="*60)
    print("  🧪 产品级单元测试")
    print("="*60)
    
    all_passed = True
    
    try:
        if not test_embedding_engine():
            all_passed = False
    except Exception as e:
        print(f"  ❌ EmbeddingEngine测试失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print()
    
    try:
        if not test_vector_store():
            all_passed = False
    except Exception as e:
        print(f"  ❌ VectorStore测试失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print()
    
    try:
        if not test_code_rag():
            all_passed = False
    except Exception as e:
        print(f"  ❌ CodeRAG测试失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False
    
    print("\n" + "="*60)
    if all_passed:
        print("  ✅ 所有测试通过！")
    else:
        print("  ❌ 部分测试失败")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
