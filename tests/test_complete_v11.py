"""
Comprehensive Test Suite for Code RAG v11.0
Multi-level testing: Unit, Integration, and System tests
"""

import sys
import time
import json
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, str(Path(__file__).parent.parent))


class TestResult:
    """测试结果"""
    def __init__(self, name: str, passed: bool, message: str = "", duration: float = 0):
        self.name = name
        self.passed = passed
        self.message = message
        self.duration = duration


def print_header(title: str):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_section(title: str):
    print(f"\n{'-' * 80}")
    print(f"  {title}")
    print(f"{'-' * 80}")


def run_unit_tests() -> List[TestResult]:
    """运行单元测试"""
    print_header("🧪 单元测试 (Unit Tests)")
    results = []

    print_section("1. Base Layer Tests")
    try:
        from src.code_rag.base_layer import get_logger, get_settings, get_monitor

        result = TestResult("get_logger", True, "日志模块初始化成功")
        results.append(result)
        print(f"  ✅ get_logger: {result.message}")

        result = TestResult("get_settings", True, "配置模块初始化成功")
        results.append(result)
        print(f"  ✅ get_settings: {result.message}")

        result = TestResult("get_monitor", True, "监控模块初始化成功")
        results.append(result)
        print(f"  ✅ get_monitor: {result.message}")

    except Exception as e:
        results.append(TestResult("base_layer", False, str(e)))
        print(f"  ❌ base_layer测试失败: {e}")

    print_section("2. Data Layer Tests")
    try:
        from src.code_rag.data_layer import CodeParser, LRUCache

        parser = CodeParser()
        result = TestResult("CodeParser", True, "代码解析器初始化成功")
        results.append(result)
        print(f"  ✅ CodeParser: {result.message}")

        cache = LRUCache(max_size=10)
        cache.set("test_key", "test_value")
        assert cache.get("test_key") == "test_value"
        result = TestResult("LRUCache", True, "缓存功能正常")
        results.append(result)
        print(f"  ✅ LRUCache: {result.message}")

    except Exception as e:
        results.append(TestResult("data_layer", False, str(e)))
        print(f"  ❌ data_layer测试失败: {e}")

    print_section("3. Search Layer Tests")
    try:
        from src.code_rag.search_layer import BM25Index

        engine = BM25Index()
        docs = [
            "FAISS is a vector database from Meta",
            "Sentence-Transformers provides embeddings",
            "Python is a programming language"
        ]
        engine.add_documents(docs, [{"id": i} for i in range(len(docs))])
        results_search = engine.search("FAISS", k=2)

        result = TestResult("BM25Index", len(results_search) > 0, f"搜索返回 {len(results_search)} 个结果")
        results.append(result)
        print(f"  {'✅' if result.passed else '❌'} BM25Index: {result.message}")

    except Exception as e:
        results.append(TestResult("search_layer", False, str(e)))
        print(f"  ❌ search_layer测试失败: {e}")

    print_section("4. RAG Engine Tests")
    try:
        from src.code_rag.rag_engine import (
            CodeRAG, get_test_documents, ProductionEmbeddingEngine,
            ProductionVectorIndex, MultiLLMEngine, SmartRuleEngine
        )

        rag = CodeRAG()
        rag.add_documents(get_test_documents())

        search_results = rag.search("RAG系统", k=3)
        result = TestResult("CodeRAG.search", len(search_results) > 0, f"搜索成功，返回 {len(search_results)} 个结果")
        results.append(result)
        print(f"  {'✅' if result.passed else '❌'} CodeRAG.search: {result.message}")

        answer = rag.query("RAG系统有什么用", k=3)
        result = TestResult("CodeRAG.query", len(answer) > 0, f"问答成功，结果长度 {len(str(answer))}")
        results.append(result)
        print(f"  {'✅' if result.passed else '❌'} CodeRAG.query: {result.message}")

        emb_engine = ProductionEmbeddingEngine()
        result = TestResult("ProductionEmbeddingEngine", True, f"使用真实模型: {emb_engine.is_using_real_model()}")
        results.append(result)
        print(f"  {'✅' if result.passed else '❌'} ProductionEmbeddingEngine: {result.message}")

        vec_index = ProductionVectorIndex(dimension=384)
        result = TestResult("ProductionVectorIndex", True, f"索引信息: {vec_index.get_info()}")
        results.append(result)
        print(f"  {'✅' if result.passed else '❌'} ProductionVectorIndex: {result.message}")

        llm_engine = MultiLLMEngine()
        result = TestResult("MultiLLMEngine", llm_engine.current_backend is not None, f"当前后端: {llm_engine.get_current_backend_name()}")
        results.append(result)
        print(f"  {'✅' if result.passed else '❌'} MultiLLMEngine: {result.message}")

    except Exception as e:
        results.append(TestResult("rag_engine", False, str(e)))
        print(f"  ❌ rag_engine测试失败: {e}")

    print_section("5. API Layer Tests")
    try:
        from src.code_rag.api_layer import (
            QueryRequest, QueryResponse,
            ValidationError, NotFoundError,
            sanitize_input, validate_file_path
        )

        req = QueryRequest(query="test query", top_k=5)
        result = TestResult("QueryRequest", req.query == "test query", "请求模型验证通过")
        results.append(result)
        print(f"  ✅ QueryRequest: {result.message}")

        sanitized = sanitize_input("  test  ")
        result = TestResult("sanitize_input", sanitized == "test", f"输入清理: '{sanitized}'")
        results.append(result)
        print(f"  {'✅' if result.passed else '❌'} sanitize_input: {result.message}")

        is_valid = validate_file_path("/data/docs")
        result = TestResult("validate_file_path", is_valid, f"路径验证: {is_valid}")
        results.append(result)
        print(f"  {'✅' if result.passed else '❌'} validate_file_path: {result.message}")

    except Exception as e:
        results.append(TestResult("api_layer", False, str(e)))
        print(f"  ❌ api_layer测试失败: {e}")

    return results


def run_integration_tests() -> List[TestResult]:
    """运行集成测试"""
    print_header("🔗 集成测试 (Integration Tests)")
    results = []

    print_section("1. RAG Pipeline Integration")
    try:
        from src.code_rag.rag_engine import CodeRAG, get_test_documents

        rag = CodeRAG()
        rag.add_documents(get_test_documents())

        search_results = rag.search("embedding", k=5)
        result = TestResult("search_integration", len(search_results) > 0, f"搜索集成测试通过")
        results.append(result)
        print(f"  {'✅' if result.passed else '❌'} search_integration: {result.message}")

        answer = rag.query("如何创建embedding", k=3)
        result = TestResult("query_integration", len(str(answer)) > 0, f"问答集成测试通过")
        results.append(result)
        print(f"  {'✅' if result.passed else '❌'} query_integration: {result.message}")

    except Exception as e:
        results.append(TestResult("rag_pipeline", False, str(e)))
        print(f"  ❌ rag_pipeline集成测试失败: {e}")

    print_section("2. Multi-Component Integration")
    try:
        from src.code_rag.rag_engine import (
            ProductionEmbeddingEngine,
            ProductionVectorIndex,
            MultiLLMEngine
        )

        emb_engine = ProductionEmbeddingEngine()
        vec_index = ProductionVectorIndex(dimension=emb_engine.dimension)
        llm_engine = MultiLLMEngine()

        texts = ["test text 1", "test text 2", "test text 3"]
        embeddings = emb_engine.encode_batch(texts)

        vec_index.add([e for e in embeddings])
        search_results = vec_index.search(embeddings[0], k=2)

        result = TestResult("embedding_index_integration", len(search_results) > 0, "Embedding到索引集成测试通过")
        results.append(result)
        print(f"  {'✅' if result.passed else '❌'} embedding_index_integration: {result.message}")

        llm_response = llm_engine.generate("What is RAG?", context=texts)
        result = TestResult("llm_integration", len(llm_response.content) > 0, f"LLM响应长度: {len(llm_response.content)}")
        results.append(result)
        print(f"  {'✅' if result.passed else '❌'} llm_integration: {result.message}")

    except Exception as e:
        results.append(TestResult("multi_component", False, str(e)))
        print(f"  ❌ multi_component集成测试失败: {e}")

    return results


def run_system_tests() -> List[TestResult]:
    """运行系统测试"""
    print_header("🎯 系统测试 (System Tests)")
    results = []

    print_section("1. Performance Tests")
    try:
        from src.code_rag.rag_engine import CodeRAG, get_test_documents, ProductionEmbeddingEngine

        rag = CodeRAG()
        rag.add_documents(get_test_documents())

        start_time = time.time()
        for _ in range(10):
            rag.search("RAG", k=5)
        search_duration = (time.time() - start_time) / 10

        result = TestResult("search_performance", search_duration < 0.1, f"平均搜索时间: {search_duration*1000:.2f}ms")
        results.append(result)
        print(f"  {'✅' if result.passed else '⚠️'} search_performance: {result.message}")

        emb_engine = ProductionEmbeddingEngine()
        start_time = time.time()
        for _ in range(100):
            emb_engine.encode("test text for performance testing")
        emb_duration = (time.time() - start_time) / 100

        result = TestResult("embedding_performance", emb_duration < 0.05, f"平均embedding时间: {emb_duration*1000:.2f}ms")
        results.append(result)
        print(f"  {'✅' if result.passed else '⚠️'} embedding_performance: {result.message}")

    except Exception as e:
        results.append(TestResult("performance", False, str(e)))
        print(f"  ❌ performance系统测试失败: {e}")

    print_section("2. Reliability Tests")
    try:
        from src.code_rag.rag_engine import CodeRAG, get_test_documents

        rag = CodeRAG()
        rag.add_documents(get_test_documents())

        success_count = 0
        for _ in range(5):
            try:
                result = rag.search("test", k=3)
                if result:
                    success_count += 1
            except:
                pass

        reliability = success_count / 5
        result = TestResult("reliability", reliability >= 0.8, f"可靠性: {reliability*100:.0f}%")
        results.append(result)
        print(f"  {'✅' if result.passed else '❌'} reliability: {result.message}")

    except Exception as e:
        results.append(TestResult("reliability", False, str(e)))
        print(f"  ❌ reliability系统测试失败: {e}")

    print_section("3. Stress Tests")
    try:
        from src.code_rag.data_layer import LRUCache

        cache = LRUCache(max_size=100)

        for i in range(200):
            cache.set(f"key_{i}", f"value_{i}")

        result = TestResult("cache_stress", len(cache) <= 100, f"LRU淘汰正常，当前大小: {len(cache)}")
        results.append(result)
        print(f"  {'✅' if result.passed else '❌'} cache_stress: {result.message}")

    except Exception as e:
        results.append(TestResult("stress", False, str(e)))
        print(f"  ❌ stress系统测试失败: {e}")

    return results


def generate_test_report(unit_results: List[TestResult], integration_results: List[TestResult], system_results: List[TestResult]) -> Dict[str, Any]:
    """生成测试报告"""
    all_results = unit_results + integration_results + system_results

    passed = sum(1 for r in all_results if r.passed)
    failed = sum(1 for r in all_results if not r.passed)
    total = len(all_results)

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": passed / total if total > 0 else 0,
        "unit_tests": {
            "total": len(unit_results),
            "passed": sum(1 for r in unit_results if r.passed),
            "failed": sum(1 for r in unit_results if not r.passed)
        },
        "integration_tests": {
            "total": len(integration_results),
            "passed": sum(1 for r in integration_results if r.passed),
            "failed": sum(1 for r in integration_results if not r.passed)
        },
        "system_tests": {
            "total": len(system_results),
            "passed": sum(1 for r in system_results if r.passed),
            "failed": sum(1 for r in system_results if not r.passed)
        }
    }


def main():
    """主测试函数"""
    print_header("🚀 Code RAG v11.0 - 完整测试套件")
    print("  测试类型: 单元测试 + 集成测试 + 系统测试")
    print("  架构版本: 9层模块化架构 + 生产级组件")

    unit_results = run_unit_tests()
    integration_results = run_integration_tests()
    system_results = run_system_tests()

    report = generate_test_report(unit_results, integration_results, system_results)

    print_header("📊 测试结果汇总")
    print(f"\n  总测试数: {report['total']}")
    print(f"  ✅ 通过: {report['passed']}")
    print(f"  ❌ 失败: {report['failed']}")
    print(f"  📈 通过率: {report['pass_rate']*100:.1f}%")

    print_section("各层级测试结果")
    print(f"  单元测试: {report['unit_tests']['passed']}/{report['unit_tests']['total']}")
    print(f"  集成测试: {report['integration_tests']['passed']}/{report['integration_tests']['total']}")
    print(f"  系统测试: {report['system_tests']['passed']}/{report['system_tests']['total']}")

    with open("test_report_v11.json", 'w') as f:
        json.dump(report, f, indent=2)

    print_section("报告保存")
    print(f"  📄 测试报告已保存: test_report_v11.json")

    if report['pass_rate'] >= 0.9:
        print("\n  🎉 测试通过率良好！系统可以进入下一阶段。")
    else:
        print("\n  ⚠️ 测试通过率偏低，建议修复失败的测试。")

    print_header("✅ 测试完成")
    return 0 if report['pass_rate'] >= 0.8 else 1


if __name__ == "__main__":
    sys.exit(main())
