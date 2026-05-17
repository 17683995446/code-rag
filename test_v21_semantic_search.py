#!/usr/bin/env python3
"""
Code RAG v21.0 - 语义搜索增强测试
测试 TF-IDF、语义匹配、代码搜索引擎
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v21.0 - 语义搜索增强测试")
print("="*80)

from code_rag.processing_layer.semantic_search import (
    Document,
    SearchResult,
    TFIDFIndex,
    SemanticMatcher,
    CodeSearchEngine,
    QueryExpander,
    create_search_engine
)


def test_tfidf_index():
    """测试 TF-IDF 索引"""
    print("\n" + "="*70)
    print("测试 1: TF-IDF 索引")
    print("="*70)
    
    index = TFIDFIndex()
    
    doc1 = Document(id="doc1", content="Python is a great programming language for data science")
    doc2 = Document(id="doc2", content="JavaScript is popular for web development")
    doc3 = Document(id="doc3", content="Python is also used in machine learning")
    
    index.add_document(doc1)
    index.add_document(doc2)
    index.add_document(doc3)
    
    print(f"  ✅ 添加 {len(index.documents)} 个文档")
    print(f"  ✅ 词汇表大小: {len(index.vocabulary)}")
    
    results = index.search("Python programming", top_k=3)
    assert len(results) > 0
    print(f"  ✅ 搜索 'Python programming' 返回 {len(results)} 个结果")
    print(f"  ✅ 最佳匹配: {results[0].document.id} (分数: {results[0].score:.2f})")
    
    return True


def test_semantic_matcher():
    """测试语义匹配器"""
    print("\n" + "="*70)
    print("测试 2: 语义匹配器")
    print("="*70)
    
    matcher = SemanticMatcher()
    
    docs = [
        Document(id="func1", content="def calculate_sum(numbers): return sum(numbers)"),
        Document(id="func2", content="def calculate_average(items): return sum(items) / len(items)"),
        Document(id="func3", content="class DataProcessor: pass"),
    ]
    
    for doc in docs:
        matcher.add_document(doc)
    
    print(f"  ✅ 索引 {len(docs)} 个代码文档")
    
    matches = matcher.find_semantic_matches("function to compute average", threshold=0.1)
    
    print(f"  ✅ 语义匹配找到 {len(matches)} 个相关文档")
    if len(matches) > 0:
        print(f"  ✅ 最佳匹配: {matches[0][0].id} (相似度: {matches[0][1]:.2f})")
    
    suggestions = matcher.suggest_related("function")
    print(f"  ✅ 相关术语建议: {suggestions}")
    
    return True


def test_code_search_engine():
    """测试代码搜索引擎"""
    print("\n" + "="*70)
    print("测试 3: 代码搜索引擎")
    print("="*70)
    
    engine = create_search_engine()
    
    code_snippets = [
        ("calc1", "def add(a, b): return a + b", "python"),
        ("calc2", "def subtract(a, b): return a - b", "python"),
        ("calc3", "def multiply(a, b): return a * b", "python"),
        ("calc4", "class Calculator: def divide(self, a, b): return a / b", "python"),
        ("calc5", "function addNumbers(a, b) { return a + b; }", "javascript"),
    ]
    
    for code_id, content, lang in code_snippets:
        engine.index_code(code_id, content, lang)
    
    print(f"  ✅ 索引 {len(code_snippets)} 个代码片段")
    
    results = engine.search_by_keyword("add numbers")
    print(f"  ✅ 关键词搜索找到 {len(results)} 个结果")
    
    semantic_results = engine.search_by_semantics("function to add two numbers", threshold=0.1)
    print(f"  ✅ 语义搜索找到 {len(semantic_results)} 个结果")
    
    combined = engine.combined_search("calculator function")
    print(f"  ✅ 组合搜索找到 {len(combined)} 个结果")
    
    stats = engine.get_statistics()
    print(f"  ✅ 索引统计: {stats['total_documents']} 文档, {stats['vocabulary_size']} 词汇")
    
    return True


def test_query_expander():
    """测试查询扩展器"""
    print("\n" + "="*70)
    print("测试 4: 查询扩展器")
    print("="*70)
    
    expander = QueryExpander()
    
    expanded = expander.expand_query("function to process data")
    
    assert len(expanded) > 0
    print(f"  ✅ 查询扩展: '{expanded[0]}' -> {len(expanded)} 个变体")
    
    for ex in expanded[1:]:
        print(f"     - {ex}")
    
    alternatives = expander.suggest_alternatives("function")
    print(f"  ✅ 替代建议: {alternatives}")
    
    return True


def test_multilanguage_search():
    """测试多语言搜索"""
    print("\n" + "="*70)
    print("测试 5: 多语言代码搜索")
    print("="*70)
    
    engine = create_search_engine()
    
    multilang_code = [
        ("py_add", "def add(a, b): return a + b", "python"),
        ("js_add", "function add(a, b) { return a + b; }", "javascript"),
        ("java_add", "public int add(int a, int b) { return a + b; }", "java"),
        ("cpp_add", "int add(int a, int b) { return a + b; }", "cpp"),
        ("go_add", "func add(a, b int) int { return a + b }", "go"),
    ]
    
    for code_id, content, lang in multilang_code:
        engine.index_code(code_id, content, lang)
    
    print(f"  ✅ 索引 {len(multilang_code)} 种语言的代码")
    
    results = engine.search_by_keyword("add function")
    print(f"  ✅ 搜索 'add function' 找到 {len(results)} 个结果")
    
    for result in results[:3]:
        print(f"     - {result.document.id} ({result.document.language}): 分数 {result.score:.2f}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("TF-IDF 索引", test_tfidf_index),
        ("语义匹配器", test_semantic_matcher),
        ("代码搜索引擎", test_code_search_engine),
        ("查询扩展器", test_query_expander),
        ("多语言搜索", test_multilanguage_search),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n[{passed+1+failed}/{len(tests)}] 执行: {name}")
            if test_func():
                passed += 1
                print(f"\n✅ {name} - 通过")
            else:
                failed += 1
                print(f"\n❌ {name} - 失败")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} - 异常: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("📋 语义搜索增强测试总结")
    print("="*80)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有语义搜索测试通过！")
        return True
    else:
        print(f"\n⚠️ {failed}个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
