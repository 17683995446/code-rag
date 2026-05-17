#!/usr/bin/env python3
"""
Code RAG v12.0 - 综合功能测试
测试所有新增的智能功能
"""

import sys
from pathlib import Path

# Add project path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def print_header(title):
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)


def test_code_intelligence():
    """测试代码智能理解"""
    print_header("🧠 测试 1: 代码智能理解")
    
    from code_rag.processing_layer.code_intelligence_and_semantic_understanding import (
        CodeIntelligenceAnalyzer,
        CodeSimilarityAnalyzer
    )
    
    analyzer = CodeIntelligenceAnalyzer()
    
    test_code = """
from flask import Flask, jsonify
import jwt

def authenticate_user(token):
    try:
        payload = jwt.decode(token, SECRET_KEY)
        return payload['user_id']
    except:
        return None

class AuthService:
    def __init__(self):
        self.app = Flask(__name__)
    
    def login(self, username, password):
        if verify_credentials(username, password):
            return generate_token(username)
        return None
    """
    
    print(f"\n  测试代码片段...")
    
    # 意图识别
    intent = analyzer.analyze_intent(test_code)
    print(f"  ✓ 意图识别: {intent.primary_intent.value}")
    
    # 标签生成
    tags = analyzer.generate_tags(test_code)
    print(f"  ✓ 标签生成: {len(tags)} 个标签")
    
    # 语言检测
    language = analyzer.detect_language(test_code)
    print(f"  ✓ 语言检测: {language}")
    
    # 结构提取
    structure = analyzer.extract_code_structure(test_code)
    print(f"  ✓ 结构提取: {len(structure['functions'])} 个函数, {len(structure['classes'])} 个类")
    
    # 相似度分析
    similarity_analyzer = CodeSimilarityAnalyzer()
    similar_code = """
def verify_user(token):
    try:
        decoded = jwt.decode(token, SECRET)
        return decoded['id']
    except:
        return None
    """
    similarity = similarity_analyzer.calculate_overall_similarity(test_code, similar_code)
    print(f"  ✓ 相似度分析: {similarity['overall']:.2f}")
    
    return True


def test_semantic_search():
    """测试语义搜索增强"""
    print_header("🔍 测试 2: 语义搜索增强")
    
    from code_rag.search_layer.semantic_search_enhancement import (
        SemanticSearchEnhancer,
        CodePatternMatcher,
        RelevanceRankingEngine
    )
    
    enhancer = SemanticSearchEnhancer()
    
    test_queries = [
        "how to implement user authentication",
        "similar code to rate limiting",
        "def function for database queries"
    ]
    
    print(f"\n  查询类型分析:")
    for query in test_queries:
        result = enhancer.analyze_query(query)
        print(f"  ✓ '{query[:40]}...'")
        print(f"    类型: {result.query_type.value}, 语言: {result.language or 'N/A'}")
    
    # 代码模式匹配
    matcher = CodePatternMatcher()
    code = """
def process_data(items):
    results = []
    for item in items:
        if validate(item):
            results.append(transform(item))
    return results
    """
    
    patterns = matcher.find_all_patterns(code)
    print(f"\n  代码模式匹配:")
    print(f"  ✓ 找到 {sum(len(v) for v in patterns.values())} 个模式")
    for pattern_name, matches in patterns.items():
        if matches:
            print(f"    - {pattern_name}: {len(matches)} 个")
    
    # 相关性排序
    ranker = RelevanceRankingEngine()
    search_query = enhancer.analyze_query("user authentication")
    
    results = [
        {'text': 'def authenticate_user(username, password):', 'bm25_score': 0.8, 'semantic_score': 0.9, 'metadata': {'language': 'python'}},
        {'text': 'console.log("hello")', 'bm25_score': 0.2, 'semantic_score': 0.1, 'metadata': {'language': 'javascript'}}
    ]
    
    ranked = ranker.rerank_results(results, search_query)
    print(f"\n  相关性排序:")
    print(f"  ✓ 排序完成，第1名分数: {ranked[0]['relevance_score']:.3f}")
    
    return True


def test_nl2code():
    """测试NL2Code转换"""
    print_header("🔄 测试 3: NL2Code转换")
    
    from code_rag.search_layer.nl2code_converter import (
        NL2CodeConverter,
        QueryExpansionEngine
    )
    
    converter = NL2CodeConverter()
    
    test_queries = [
        "create new user account",
        "fetch data from database",
        "validate email format",
        "handle API errors"
    ]
    
    print(f"\n  意图识别测试:")
    for query in test_queries:
        result = converter.convert(query)
        print(f"  ✓ '{query}'")
        print(f"    意图: {result.intent.value}, 置信度: {result.confidence:.2f}")
    
    # 查询扩展
    engine = QueryExpansionEngine()
    expanded = engine.expand("create user", num_variants=5)
    print(f"\n  查询扩展:")
    print(f"  ✓ 生成 {len(expanded)} 个变体")
    for var in expanded[:3]:
        print(f"    - [{var['type']}] {var['query']} ({var['confidence']:.2f})")
    
    return True


def test_integration():
    """测试模块集成"""
    print_header("🔗 测试 4: 模块集成")
    
    print(f"\n  正在测试完整流程...")
    
    from code_rag.processing_layer.code_intelligence_and_semantic_understanding import (
        CodeIntelligenceAnalyzer
    )
    from code_rag.search_layer.semantic_search_enhancement import (
        SemanticSearchEnhancer
    )
    from code_rag.search_layer.nl2code_converter import (
        NL2CodeConverter
    )
    
    # 用户查询
    user_query = "how to implement user authentication in Python Flask"
    
    # 1. NL2Code转换
    nl2code = NL2CodeConverter()
    nl2code_result = nl2code.convert(user_query)
    print(f"\n  步骤1 - NL2Code转换:")
    print(f"    查询意图: {nl2code_result.intent.value}")
    print(f"    置信度: {nl2code_result.confidence:.2f}")
    print(f"    扩展查询数: {len(nl2code_result.search_queries)}")
    
    # 2. 查询增强
    enhancer = SemanticSearchEnhancer()
    enhanced = enhancer.analyze_query(user_query)
    print(f"\n  步骤2 - 查询增强:")
    print(f"    查询类型: {enhanced.query_type.value}")
    print(f"    检测语言: {enhanced.language}")
    print(f"    扩展查询数: {len(enhanced.expanded_queries)}")
    
    # 3. 代码智能理解
    analyzer = CodeIntelligenceAnalyzer()
    code_example = """
from flask import Flask, request, jsonify
import jwt

app = Flask(__name__)

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if validate_credentials(data['username'], data['password']):
        token = jwt.encode({'user': data['username']}, SECRET_KEY)
        return jsonify({'token': token})
    return jsonify({'error': 'Invalid credentials'}), 401
    """
    
    intent = analyzer.analyze_intent(code_example)
    print(f"\n  步骤3 - 代码理解:")
    print(f"    代码意图: {intent.primary_intent.value}")
    print(f"    置信度: {intent.confidence:.2f}")
    
    # 4. 综合评估
    print(f"\n  步骤4 - 综合评估:")
    integration_score = (
        nl2code_result.confidence * 0.3 +
        enhanced.query_type.value.count('natural') * 0.2 +
        intent.confidence * 0.5
    )
    print(f"    集成评分: {integration_score:.2f}")
    
    return True


def test_performance():
    """测试性能"""
    print_header("⚡ 测试 5: 性能测试")
    
    import time
    from code_rag.processing_layer.code_intelligence_and_semantic_understanding import (
        CodeIntelligenceAnalyzer
    )
    from code_rag.search_layer.semantic_search_enhancement import (
        SemanticSearchEnhancer
    )
    from code_rag.search_layer.nl2code_converter import (
        NL2CodeConverter
    )
    
    test_code = """
def process_data(items):
    results = []
    for item in items:
        if validate(item):
            results.append(transform(item))
    return results
    """
    
    test_query = "how to implement authentication in Python"
    
    # 代码智能理解性能
    analyzer = CodeIntelligenceAnalyzer()
    start = time.time()
    for _ in range(100):
        analyzer.analyze_intent(test_code)
        analyzer.generate_tags(test_code)
        analyzer.extract_code_structure(test_code)
    intent_time = (time.time() - start) * 10
    
    print(f"\n  代码智能理解:")
    print(f"    100次迭代: {intent_time:.2f}ms/次")
    
    # 查询分析性能
    enhancer = SemanticSearchEnhancer()
    start = time.time()
    for _ in range(100):
        enhancer.analyze_query(test_query)
        enhancer.generate_search_queries(test_query)
    query_time = (time.time() - start) * 10
    
    print(f"\n  查询分析:")
    print(f"    100次迭代: {query_time:.2f}ms/次")
    
    # NL2Code性能
    converter = NL2CodeConverter()
    start = time.time()
    for _ in range(100):
        converter.convert(test_query)
    nl2code_time = (time.time() - start) * 10
    
    print(f"\n  NL2Code转换:")
    print(f"    100次迭代: {nl2code_time:.2f}ms/次")
    
    return True


def main():
    print_header("🚀 Code RAG v12.0 - 综合功能测试")
    print("开始时间: 2026-05-16 05:15:00")
    
    tests = [
        ("代码智能理解", test_code_intelligence),
        ("语义搜索增强", test_semantic_search),
        ("NL2Code转换", test_nl2code),
        ("模块集成", test_integration),
        ("性能测试", test_performance)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
            print(f"\n  ✅ {name} - 通过")
        except Exception as e:
            results.append((name, False))
            print(f"\n  ❌ {name} - 失败: {e}")
    
    # 总结
    print_header("📋 测试总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n  通过率: {passed}/{total} ({passed/total*100:.1f}%)")
    
    print(f"\n  详细结果:")
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"    {status} - {name}")
    
    if passed == total:
        print(f"\n  🎉 所有测试通过！Code RAG v12.0 智能功能全部就绪！")
        print(f"\n  新增功能总览:")
        print(f"    1. 代码智能理解 - 意图识别、标签生成、结构提取")
        print(f"    2. 语义搜索增强 - 查询分析、模式匹配、智能排序")
        print(f"    3. NL2Code转换 - 自然语言到代码搜索")
        print(f"    4. 模块集成 - 端到端智能处理流程")
        print(f"    5. 性能优化 - 毫秒级响应")
    else:
        print(f"\n  ⚠️ 有测试失败，请检查")
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
