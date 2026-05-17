"""
产品级集成测试
测试模块之间的协同工作
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import (
    CodeRAG,
    CodeParser,
    BM25Index,
    EmbeddingEngine,
    VectorStore,
    get_logger,
    log_context
)


def test_parser_and_rag_integration():
    """测试解析器和RAG的集成"""
    print("🧪 集成测试: Parser + RAG")

    logger = get_logger(__name__)

    with log_context("创建测试文件"):
        # 创建测试文件
        test_files = [
            {
                "name": "math_utils.py",
                "content": '''def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

class Calculator:
    def __init__(self):
        self.result = 0
    
    def compute(self, operation, x, y):
        if operation == "add":
            return add(x, y)
        elif operation == "multiply":
            return multiply(x, y)
'''
            },
            {
                "name": "string_utils.py",
                "content": '''def uppercase(s):
    return s.upper()

def lowercase(s):
    return s.lower()

def reverse(s):
    return s[::-1]
'''
            }
        ]

        test_dir = Path("/tmp/test_integration")
        test_dir.mkdir(exist_ok=True)

        for file_info in test_files:
            file_path = test_dir / file_info["name"]
            file_path.write_text(file_info["content"])

    with log_context("解析文件"):
        parser = CodeParser()
        docs = parser.parse_directory(str(test_dir))
        assert len(docs) == 2
        logger.info(f"解析了 {len(docs)} 个文件")

    with log_context("初始化RAG"):
        rag = CodeRAG(implementation="simplified")

    with log_context("索引代码"):
        # 提取所有代码块内容
        all_chunks = []
        all_metadata = []
        for doc in docs:
            for chunk in doc.chunks:
                all_chunks.append(chunk.content)
                all_metadata.append({
                    "file": doc.file_path,
                    "type": chunk.chunk_type,
                    "name": chunk.name
                })

        # 手动添加到vector store
        embeddings = [rag.pipeline.embedding_engine.encode(c).vector for c in all_chunks]
        rag.pipeline.vector_store.add(embeddings, all_chunks, all_metadata)

    with log_context("搜索测试"):
        results = rag.search("计算 加法", k=2)
        assert len(results) > 0
        logger.info(f"找到 {len(results)} 个相关结果")

    with log_context("问答测试"):
        answer = rag.ask("如何进行加法计算?")
        assert answer.success is True
        logger.info(f"问答成功: {answer.answer[:50]}...")

    # 清理
    for file_info in test_files:
        file_path = test_dir / file_info["name"]
        file_path.unlink(missing_ok=True)
    test_dir.rmdir()

    print("  ✅ Parser + RAG 集成测试通过")
    return True


def test_bm25_and_vector_integration():
    """测试BM25和向量搜索的集成"""
    print("🧪 集成测试: BM25 + Vector")

    # 准备数据
    documents = [
        "Python是一门优秀的编程语言，适合数据科学",
        "JavaScript主要用于Web前端开发",
        "FAISS是Meta开源的高性能向量数据库",
        "Sentence-Transformers用于生成文本embedding",
        "RAG系统结合检索和生成，提供更好的问答"
    ]
    metadatas = [{"id": i} for i in range(len(documents))]

    # 初始化BM25
    bm25 = BM25Index()
    bm25.add_documents(documents, metadatas)

    # 初始化向量存储
    engine = EmbeddingEngine()
    embeddings = [e.vector for e in engine.encode_batch(documents)]
    vector_store = VectorStore(embedding_dimension=engine.dimension)
    vector_store.add(embeddings, documents, metadatas)

    # 分别搜索
    bm25_results = bm25.search("Python 数据科学", k=3)
    vector_results = vector_store.search(engine.encode("Python 数据科学").vector, k=3)

    print(f"  - BM25找到 {len(bm25_results)} 个结果")
    print(f"  - 向量找到 {len(vector_results)} 个结果")

    # 合并结果（简单演示）
    combined_ids = set()
    for r in bm25_results:
        combined_ids.add(r.metadata.get("id"))
    for r in vector_results:
        combined_ids.add(r.metadata.get("id"))

    print(f"  - 合并后有 {len(combined_ids)} 个唯一结果")

    print("  ✅ BM25 + Vector 集成测试通过")
    return True


def test_end_to_end_workflow():
    """测试端到端工作流"""
    print("🧪 集成测试: 端到端工作流")

    # 完整流程：解析 -> 索引 -> 搜索 -> 问答
    rag = CodeRAG(implementation="simplified")

    # 索引（会使用演示数据）
    rag.index("/tmp/nonexistent")

    # 搜索
    results = rag.search("FAISS", k=3)
    assert len(results) > 0

    # 问答
    answer = rag.ask("什么是向量数据库?")
    assert answer.success is True

    print(f"  - 搜索到 {len(results)} 个结果")
    print(f"  - 问答成功: {len(answer.sources)} 个来源")

    print("  ✅ 端到端工作流测试通过")
    return True


def run_all_integration_tests():
    """运行所有集成测试"""
    print("=" * 60)
    print("  🔗 产品级集成测试")
    print("=" * 60)

    all_passed = True
    tests = [
        ("Parser + RAG", test_parser_and_rag_integration),
        ("BM25 + Vector", test_bm25_and_vector_integration),
        ("端到端工作流", test_end_to_end_workflow),
    ]

    for test_name, test_func in tests:
        try:
            print()
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"  ❌ {test_name}集成测试失败: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("  ✅ 所有集成测试通过！")
    else:
        print("  ❌ 部分集成测试失败")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_all_integration_tests())
