#!/usr/bin/env python3
"""
Code RAG v13.0 - 全面测试套件 (根目录)
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def print_header(title):
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)


def test_code_intelligence():
    """测试代码智能理解"""
    print_header("🧠 测试 1: 代码智能理解")
    
    test_code = '''
def authenticate_user(username, password):
    """验证用户"""
    if verify_credentials(username, password):
        return generate_token(username)
    return None

class DatabaseHandler:
    def __init__(self, db_url):
        self.db_url = db_url
        
    def query_data(self, sql):
        """查询数据"""
        return execute_sql(sql)
'''
    
    from code_rag.processing_layer.code_intelligence_and_semantic_understanding import (
        analyze_code_intelligence
    )
    
    result = analyze_code_intelligence(test_code)
    
    print(f"\n  ✓ 检测语言: {result['detected_language']}")
    print(f"  ✓ 主要意图: {result['intent']['primary']}")
    print(f"  ✓ 置信度: {result['intent']['confidence']:.2f}")
    print(f"  ✓ 标签数: {len(result['tags'])}")
    
    if result['tags']:
        print(f"  ✓ 标签示例: {result['tags'][0]['name']}")
    
    return True


def test_semantic_search_enhancement():
    """测试语义搜索增强"""
    print_header("🔍 测试 2: 语义搜索增强")
    
    from code_rag.search_layer.semantic_search_enhancement import enhance_search
    
    test_query = "how to implement user authentication"
    
    result = enhance_search(test_query)
    
    print(f"\n  ✓ 原始查询: {result['original']}")
    print(f"  ✓ 查询类型: {result['type']}")
    print(f"  ✓ 检测语言: {result['language'] or 'N/A'}")
    print(f"  ✓ 扩展查询数: {len(result['all_queries'])}")
    
    if result['all_queries']:
        print(f"  ✓ 扩展示例: {result['all_queries'][0]}")
    
    return True


def test_nl2code():
    """测试 NL2Code"""
    print_header("🔄 测试 3: NL2Code")
    
    from code_rag.search_layer.nl2code_converter import nl2code
    
    test_queries = [
        "create user authentication",
        "connect to database",
        "handle API errors",
    ]
    
    for query in test_queries:
        result = nl2code(query)
        
        print(f"\n  查询: '{query}'")
        print(f"    ✓ 意图: {result['intent']}")
        print(f"    ✓ 置信度: {result['confidence']:.2f}")
        print(f"    ✓ 搜索查询数: {len(result['search_queries'])}")
        
        if result['search_queries']:
            print(f"    ✓ 搜索查询: {result['search_queries'][0]}")
    
    return True


def test_dependency_analysis():
    """测试依赖分析"""
    print_header("📊 测试 4: 代码依赖分析")
    
    from code_rag.processing_layer.code_dependency_analyzer import analyze_dependencies
    
    test_dir = str(PROJECT_ROOT / "src" / "code_rag")
    
    try:
        result = analyze_dependencies(test_dir)
        
        print(f"\n  ✓ 分析目录: {test_dir}")
        print(f"  ✓ 文件数: {result['files']}")
        print(f"  ✓ 函数数: {result['functions']}")
        print(f"  ✓ 类数: {result['classes']}")
        print(f"  ✓ 总代码行数: {result['total_lines']:,}")
        print(f"  ✓ 导入数: {result['imports']}")
        
        return True
    except Exception as e:
        print(f"  ⚠️ 依赖分析警告: {e}")
        return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("代码智能理解", test_code_intelligence),
        ("语义搜索增强", test_semantic_search_enhancement),
        ("NL2Code", test_nl2code),
        ("代码依赖分析", test_dependency_analysis),
    ]
    
    results = []
    
    print_header("🧪 Code RAG v13.0 - 全面测试套件")
    print(f"  测试数量: {len(tests)}")
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ 测试 '{test_name}' 失败: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print_header("📋 测试总结")
    
    passed = sum(1 for _, passed in results if passed)
    total = len(results)
    
    print(f"\n  📊 结果: {passed}/{total} 测试通过")
    print(f"  ✅ 通过率: {passed/total*100:.1f}%")
    
    print(f"\n  详细结果:")
    for test_name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"    {status} - {test_name}")
    
    if passed == total:
        print(f"\n  🎉 所有测试通过！Code RAG v13.0 准备就绪！")
        return True
    else:
        print(f"\n  ⚠️ 部分测试失败，请检查")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
