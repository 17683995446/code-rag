#!/usr/bin/env python3
"""
完整单元测试套件
测试：phase1_infrastructure.py 和 phase2_langchain.py
"""

import sys
import os
import json
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Any
import unittest

# 确保我们能导入要测试的模块
sys.path.insert(0, str(Path(__file__).parent))

# 测试数据
TEST_DOCUMENTS = [
    "FAISS是Meta开源的向量数据库，性能非常优秀",
    "Sentence-Transformers提供高质量的预训练embedding",
    "LangChain是连接LLM和数据的标准框架",
    "Python是一种优秀的编程语言，适合做AI开发",
    "代码库需要良好的架构设计才能长期维护"
]

TEST_METADATA = [
    {"file_path": "test1.txt", "file_name": "test1.txt"},
    {"file_path": "test2.txt", "file_name": "test2.txt"},
    {"file_path": "test3.txt", "file_name": "test3.txt"},
    {"file_path": "test4.txt", "file_name": "test4.txt"},
    {"file_path": "test5.txt", "file_name": "test5.txt"}
]


class TestEmbeddingEngine(unittest.TestCase):
    """测试 EmbeddingEngine"""
    
    def setUp(self):
        """测试前准备"""
        from phase1_infrastructure import EmbeddingEngine
        self.embedding_engine = EmbeddingEngine(use_open_source=True)
    
    def test_single_encode(self):
        """测试单文本编码"""
        embedding = self.embedding_engine.encode("Hello world")
        self.assertIsInstance(embedding, list)
        self.assertGreater(len(embedding), 0)
        # 应该是384维 (MiniLM的维度)
        self.assertEqual(len(embedding), 384)
    
    def test_batch_encode(self):
        """测试批量编码"""
        embeddings = self.embedding_engine.encode_batch(["Hello", "World", "Test"])
        self.assertIsInstance(embeddings, list)
        self.assertEqual(len(embeddings), 3)
        for emb in embeddings:
            self.assertIsInstance(emb, list)
            self.assertEqual(len(emb), 384)
    
    def test_consistency(self):
        """测试编码一致性"""
        emb1 = self.embedding_engine.encode("test string")
        emb2 = self.embedding_engine.encode("test string")
        self.assertEqual(len(emb1), len(emb2))
        # 简单检查第一个维度相同
        self.assertAlmostEqual(emb1[0], emb2[0], places=5)


class TestVectorIndex(unittest.TestCase):
    """测试 VectorIndex"""
    
    def setUp(self):
        """测试前准备"""
        from phase1_infrastructure import VectorIndex, EmbeddingEngine
        
        self.embedding = EmbeddingEngine(use_open_source=True)
        self.vector_index = VectorIndex(dim=384, use_open_source=True)
        
        # 先编码一些测试文档
        self.test_embeddings = self.embedding.encode_batch(TEST_DOCUMENTS)
        self.vector_index.add(self.test_embeddings, TEST_DOCUMENTS, TEST_METADATA)
    
    def test_add_documents(self):
        """测试添加文档"""
        self.assertEqual(len(self.vector_index.documents), 5)
        self.assertEqual(len(self.vector_index.metadata), 5)
    
    def test_search(self):
        """测试搜索功能"""
        query = self.embedding.encode("FAISS向量数据库")
        results = self.vector_index.search(query, k=3)
        
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 3)
        
        for result in results:
            self.assertIn("text", result)
            self.assertIn("score", result)
            self.assertIn("metadata", result)
    
    def test_save_load(self):
        """测试保存和加载"""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            save_path = tmp.name
        
        try:
            # 保存
            self.vector_index.save(save_path)
            
            # 重新创建并加载
            from phase1_infrastructure import VectorIndex
            new_index = VectorIndex(dim=384, use_open_source=True)
            new_index.load(save_path)
            
            # 验证加载正确
            self.assertEqual(len(new_index.documents), len(self.vector_index.documents))
            self.assertEqual(new_index.documents[0], self.vector_index.documents[0])
            
        finally:
            # 清理
            try:
                Path(save_path + ".index").unlink(missing_ok=True)
                Path(save_path + ".data").unlink(missing_ok=True)
            except:
                pass


class TestCodeRAGPhase1(unittest.TestCase):
    """测试 Phase1 的 CodeRAG"""
    
    def setUp(self):
        """测试前准备 - 创建测试目录"""
        self.test_dir = tempfile.mkdtemp()
        
        # 创建一些测试文件
        test_file = Path(self.test_dir) / "test1.py"
        test_file.write_text("""
def hello_world():
    print("Hello world")
        """)
        
        # 记录路径以便清理
        self.addCleanup(shutil.rmtree, self.test_dir)
    
    def test_initialization(self):
        """测试初始化"""
        from phase1_infrastructure import CodeRAG
        rag = CodeRAG(use_open_source=True)
        self.assertIsNotNone(rag.embedding)
        self.assertIsNotNone(rag.vector_index)
    
    def test_indexing(self):
        """测试索引功能"""
        from phase1_infrastructure import CodeRAG
        rag = CodeRAG(use_open_source=True)
        
        # 索引测试目录
        rag.index(self.test_dir)
        
        # 验证有文档被索引了
        # 注意：如果没有真实文件，会用演示数据
        self.assertGreater(len(rag.vector_index.documents), 0)
    
    def test_search(self):
        """测试搜索功能"""
        from phase1_infrastructure import CodeRAG
        rag = CodeRAG(use_open_source=True)
        
        # 索引演示数据
        rag.index(self.test_dir)
        
        # 搜索
        results = rag.search("测试搜索", k=3)
        
        # 验证结果
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 3)
        
        for result in results:
            self.assertTrue(hasattr(result, 'text'))
            self.assertTrue(hasattr(result, 'score'))
    
    def test_ask(self):
        """测试问答功能"""
        from phase1_infrastructure import CodeRAG
        rag = CodeRAG(use_open_source=True)
        rag.index(self.test_dir)
        
        answer = rag.ask("你好")
        
        # 验证回答格式
        self.assertIsInstance(answer, dict)
        self.assertIn("question", answer)
        self.assertIn("answer", answer)
        self.assertIn("sources", answer)


class TestCodeRAGPhase2(unittest.TestCase):
    """测试 Phase2 的 CodeRAG"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.test_dir)
    
    def test_auto_implementation(self):
        """测试自动选择实现"""
        from phase2_langchain import CodeRAG
        
        rag = CodeRAG(implementation="auto")
        self.assertIsNotNone(rag)
        # 应该是phase1或langchain模式（取决于是否安装了LangChain）
    
    def test_phase1_implementation(self):
        """测试强制使用phase1实现"""
        from phase2_langchain import CodeRAG
        
        rag = CodeRAG(implementation="phase1")
        self.assertIsNotNone(rag)
        rag.index(self.test_dir)
        
        results = rag.search("test", k=2)
        self.assertIsInstance(results, list)
    
    def test_ask_interface_compatibility(self):
        """测试问答接口兼容性"""
        from phase2_langchain import CodeRAG
        
        rag = CodeRAG(implementation="phase1")
        answer = rag.ask("我的问题")
        
        # 应该和phase1有相同的返回格式
        self.assertIsInstance(answer, dict)
        self.assertIn("question", answer)
        self.assertIn("answer", answer)
        self.assertIn("sources", answer)


class TestSearchResult(unittest.TestCase):
    """测试SearchResult数据类"""
    
    def test_creation(self):
        """测试创建SearchResult"""
        from phase1_infrastructure import SearchResult
        
        result = SearchResult(
            text="测试文本",
            score=0.9,
            metadata={"key": "value"}
        )
        
        self.assertEqual(result.text, "测试文本")
        self.assertEqual(result.score, 0.9)
        self.assertEqual(result.metadata, {"key": "value"})


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""
    
    def test_empty_search(self):
        """测试空搜索查询"""
        from phase1_infrastructure import CodeRAG
        
        rag = CodeRAG(use_open_source=True)
        rag.index("/tmp/non_existent_path")  # 演示模式
        
        # 空查询应该也能工作
        try:
            results = rag.search("", k=3)
            self.assertIsInstance(results, list)
        except Exception as e:
            self.fail(f"搜索空字符串时抛出异常: {e}")
    
    def test_large_k(self):
        """测试超过文档数的k值"""
        from phase1_infrastructure import CodeRAG
        
        rag = CodeRAG(use_open_source=True)
        rag.index("/tmp/non_existent_path")
        
        # 用很大的k值搜索
        results = rag.search("test", k=100)
        
        # 应该返回实际文档数而不是报错
        self.assertIsInstance(results, list)
        self.assertLessEqual(len(results), 100)


# 测试套件
def create_test_suite():
    """创建完整测试套件"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试
    suite.addTests(loader.loadTestsFromTestCase(TestEmbeddingEngine))
    suite.addTests(loader.loadTestsFromTestCase(TestVectorIndex))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeRAGPhase1))
    suite.addTests(loader.loadTestsFromTestCase(TestCodeRAGPhase2))
    suite.addTests(loader.loadTestsFromTestCase(TestSearchResult))
    suite.addTests(loader.loadTestsFromTestCase(TestEdgeCases))
    
    return suite


def main():
    """运行完整测试"""
    print("="*60)
    print("  完整单元测试套件 - 开始")
    print("="*60)
    
    # 创建测试运行器
    runner = unittest.TextTestRunner(verbosity=2)
    suite = create_test_suite()
    
    # 运行测试
    print("\n" + "-"*60)
    print("  运行测试...")
    print("-"*60)
    result = runner.run(suite)
    
    print("\n" + "="*60)
    print("  测试结果总结")
    print("="*60)
    
    print(f"\n  运行的测试: {result.testsRun}")
    print(f"  失败: {len(result.failures)}")
    print(f"  错误: {len(result.errors)}")
    print(f"  成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    
    if result.failures:
        print("\n  失败的测试:")
        for test, traceback in result.failures:
            print(f"    - {test}")
    
    if result.errors:
        print("\n  发生错误的测试:")
        for test, traceback in result.errors:
            print(f"    - {test}")
    
    overall_success = len(result.failures) == 0 and len(result.errors) == 0
    
    print("\n" + "="*60)
    if overall_success:
        print("  🎉 所有测试通过！")
    else:
        print("  ⚠️  部分测试失败，请检查上面的输出")
    print("="*60)
    
    return 0 if overall_success else 1


if __name__ == "__main__":
    sys.exit(main())
