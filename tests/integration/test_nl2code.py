#!/usr/bin/env python3
"""
Code RAG v12.0 - NL2Code转换器测试
测试自然语言到代码搜索的转换功能
"""

import sys
from pathlib import Path

# Add project path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from code_rag.search_layer.nl2code_converter import (
    NL2CodeConverter,
    QueryExpansionEngine,
    IntentCategory,
    nl2code,
    expand_queries
)


def print_header(title):
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)


def test_basic_nl2code():
    """测试基本NL2Code转换"""
    print_header("🔄 测试 1: 基本NL2Code转换")
    
    converter = NL2CodeConverter()
    
    test_queries = [
        "how to create a new user in Python",
        "get user data from database",
        "update user profile information",
        "delete user account",
        "authenticate user with JWT token",
        "validate email address format",
        "convert JSON to Python object",
        "handle database connection error",
        "setup Flask application",
        "write unit test for authentication"
    ]
    
    for query in test_queries:
        result = converter.convert(query)
        print(f"\n  查询: '{query}'")
        print(f"    意图: {result.intent.value}")
        print(f"    置信度: {result.confidence:.2f}")
        print(f"    关键词: {result.code_keywords[:5]}")
        print(f"    推理: {result.reasoning[:80]}...")


def test_intent_detection():
    """测试意图检测"""
    print_header("🎯 测试 2: 意图检测")
    
    converter = NL2CodeConverter()
    
    test_cases = [
        ("create database table", IntentCategory.CREATE),
        ("fetch user information", IntentCategory.READ),
        ("modify configuration file", IntentCategory.UPDATE),
        ("remove old records", IntentCategory.DELETE),
        ("login with OAuth", IntentCategory.AUTHENTICATE),
        ("check input validity", IntentCategory.VALIDATE),
        ("parse XML data", IntentCategory.TRANSFORM),
        ("catch exceptions properly", IntentCategory.HANDLE_ERROR),
        ("configure logging system", IntentCategory.CONFIGURE),
        ("write test cases", IntentCategory.TEST),
    ]
    
    correct = 0
    total = len(test_cases)
    
    for query, expected_intent in test_cases:
        result = converter.convert(query)
        detected = result.intent
        is_correct = detected == expected_intent
        status = "✅" if is_correct else "❌"
        
        if is_correct:
            correct += 1
        
        print(f"\n  {status} 查询: '{query}'")
        print(f"     期望: {expected_intent.value}")
        print(f"     检测: {detected.value}")
    
    accuracy = (correct / total) * 100
    print(f"\n  意图检测准确率: {accuracy:.1f}% ({correct}/{total})")


def test_code_pattern_generation():
    """测试代码模式生成"""
    print_header("🔧 测试 3: 代码模式生成")
    
    converter = NL2CodeConverter()
    
    queries = [
        "create user authentication",
        "fetch data from API",
        "validate input parameters",
        "cache expensive computations"
    ]
    
    for query in queries:
        result = converter.convert(query)
        print(f"\n  查询: '{query}'")
        print(f"  生成的代码模式:")
        for i, pattern in enumerate(result.code_patterns[:5], 1):
            print(f"    {i}. {pattern}")


def test_search_query_generation():
    """测试搜索查询生成"""
    print_header("🔍 测试 4: 搜索查询生成")
    
    converter = NL2CodeConverter()
    
    queries = [
        "implement user registration",
        "handle form validation",
        "optimize slow queries"
    ]
    
    for query in queries:
        result = converter.convert(query)
        print(f"\n  查询: '{query}'")
        print(f"  生成的搜索查询:")
        for i, search_query in enumerate(result.search_queries, 1):
            print(f"    {i}. {search_query}")


def test_query_expansion():
    """测试查询扩展"""
    print_header("🚀 测试 5: 查询扩展")
    
    engine = QueryExpansionEngine()
    
    query = "create user account"
    variants = engine.expand(query, num_variants=10)
    
    print(f"\n  原始查询: '{query}'")
    print(f"\n  扩展查询 ({len(variants)} 个):")
    
    for i, variant in enumerate(variants, 1):
        print(f"\n  {i}. [{variant['type']}] {variant['query']}")
        print(f"     置信度: {variant['confidence']:.2f}")


def test_nl2code_function():
    """测试便捷函数"""
    print_header("✨ 测试 6: 便捷函数")
    
    query = "how to implement caching mechanism"
    result = nl2code(query)
    
    print(f"\n  查询: '{query}'")
    print(f"\n  转换结果:")
    print(f"    意图: {result['intent']}")
    print(f"    置信度: {result['confidence']:.2f}")
    print(f"    代码关键词: {result['code_keywords']}")
    print(f"    推理: {result['reasoning']}")
    print(f"\n  生成的搜索查询:")
    for i, q in enumerate(result['search_queries'], 1):
        print(f"    {i}. {q}")


def test_complex_queries():
    """测试复杂查询"""
    print_header("💪 测试 7: 复杂查询处理")
    
    converter = NL2CodeConverter()
    
    complex_queries = [
        "how to implement rate limiting for REST API endpoints in Python Flask with JWT authentication",
        "best practices for handling concurrent database transactions with error retry logic",
        "optimizing performance of expensive database queries with caching strategy",
        "implementing secure user authentication with OAuth2 and refresh tokens",
        "setting up CI/CD pipeline for automated testing and deployment"
    ]
    
    for query in complex_queries:
        result = converter.convert(query)
        print(f"\n  查询: '{query[:60]}...'")
        print(f"    意图: {result.intent.value}")
        print(f"    关键词: {', '.join(result.code_keywords[:5])}")
        print(f"    置信度: {result.confidence:.2f}")


def main():
    print_header("🧪 Code RAG v12.0 - NL2Code转换器测试")
    
    try:
        test_basic_nl2code()
        test_intent_detection()
        test_code_pattern_generation()
        test_search_query_generation()
        test_query_expansion()
        test_nl2code_function()
        test_complex_queries()
        
        print_header("📋 测试总结")
        print("\n  ✅ 所有测试完成!")
        print("\n  NL2Code核心能力:")
        print("    1. 意图识别 - 15种代码意图分类")
        print("    2. 关键词提取 - 自动识别代码相关关键词")
        print("    3. 模式生成 - 生成代码搜索模式")
        print("    4. 查询扩展 - 多维度扩展搜索查询")
        print("    5. 置信度评估 - 量化转换质量")
        
        print("\n  支持的意图类型:")
        for intent in IntentCategory:
            print(f"    • {intent.value}")
        
        print("\n  应用场景:")
        print("    • 自然语言代码搜索")
        print("    • 代码智能补全")
        print("    • 代码问答系统")
        print("    • 开发者搜索引擎")
        print("    • 文档自动生成")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
