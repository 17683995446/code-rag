#!/usr/bin/env python3
"""
Code RAG v15.0 - CLI测试
测试增强型命令行界面
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def print_header(title):
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)


def test_cli_initialization():
    """测试CLI初始化"""
    print_header("🚀 测试 1: CLI初始化")
    
    from code_rag.cli_enhanced import EnhancedCLI
    
    cli = EnhancedCLI()
    
    print(f"  ✓ CLI创建成功")
    print(f"  ✓ 解析器: {type(cli.parser).__name__}")
    print(f"  ✓ 搜索索引: {type(cli.search_index).__name__}")
    print(f"  ✓ 索引状态: {cli.is_indexed}")
    
    return True


def test_cli_banner():
    """测试横幅显示"""
    print_header("🎨 测试 2: 横幅显示")
    
    from code_rag.cli_enhanced import EnhancedCLI
    
    cli = EnhancedCLI()
    
    try:
        cli.print_banner()
        print(f"  ✓ 横幅显示成功")
        return True
    except Exception as e:
        print(f"  ❌ 横幅显示失败: {e}")
        return False


def test_output_formats():
    """测试输出格式化"""
    print_header("📝 测试 3: 输出格式化")
    
    from code_rag.cli_enhanced import EnhancedCLI
    
    cli = EnhancedCLI()
    
    try:
        cli.print_info("测试信息")
        cli.print_success("测试成功")
        cli.print_warning("测试警告")
        cli.print_error("测试错误")
        
        cli.print_header("测试标题")
        
        cli.print_table(
            headers=["功能", "状态", "备注"],
            rows=[
                ["索引", "✓", "正常"],
                ["搜索", "✓", "正常"],
                ["分析", "✓", "正常"]
            ]
        )
        
        print(f"  ✓ 输出格式化测试成功")
        return True
    except Exception as e:
        print(f"  ❌ 输出格式化测试失败: {e}")
        return False


def test_search_results():
    """测试搜索结果展示"""
    print_header("🔍 测试 4: 搜索结果展示")
    
    from code_rag.cli_enhanced import EnhancedCLI
    
    cli = EnhancedCLI()
    
    mock_results = [
        {
            'score': 0.95,
            'text': 'def authenticate_user(username, password):\n    if verify_credentials(username, password):\n        return generate_token(username)\n    return None'
        },
        {
            'score': 0.85,
            'text': 'class UserAuth:\n    def login(self, credentials):\n        return self.authenticate(credentials)'
        },
        {
            'score': 0.75,
            'text': 'def validate_credentials(username, password):\n    return check_password_hash(username, password)'
        }
    ]
    
    try:
        cli.print_search_results(mock_results, "user authentication")
        print(f"  ✓ 搜索结果展示成功")
        return True
    except Exception as e:
        print(f"  ❌ 搜索结果展示失败: {e}")
        return False


def test_code_analysis():
    """测试代码分析展示"""
    print_header("📊 测试 5: 代码分析展示")
    
    from code_rag.cli_enhanced import EnhancedCLI
    
    cli = EnhancedCLI()
    
    mock_code = '''
def authenticate_user(username, password):
    if verify_credentials(username, password):
        return generate_token(username)
    return None
'''
    
    mock_analysis = {
        'detected_language': 'python',
        'intent': {
            'primary': 'authentication',
            'confidence': 0.85
        },
        'tags': [
            {'name': 'authenticate', 'category': 'keyword'},
            {'name': 'function:authenticate_user', 'category': 'function'}
        ],
        'summary': {
            'short': '包含 1 个函数'
        }
    }
    
    try:
        cli.print_code_analysis(mock_code, mock_analysis)
        print(f"  ✓ 代码分析展示成功")
        return True
    except Exception as e:
        print(f"  ❌ 代码分析展示失败: {e}")
        return False


def test_dependency_analysis():
    """测试依赖分析展示"""
    print_header("📈 测试 6: 依赖分析展示")
    
    from code_rag.cli_enhanced import EnhancedCLI
    
    cli = EnhancedCLI()
    
    mock_stats = {
        'files': 38,
        'functions': 749,
        'classes': 198,
        'total_lines': 11529,
        'imports': 276,
        'top_imported_modules': [
            ('typing', 29),
            ('dataclasses', 23),
            ('base_layer', 19),
            ('logging', 18),
            ('re', 13)
        ]
    }
    
    try:
        cli.print_dependency_analysis(mock_stats)
        print(f"  ✓ 依赖分析展示成功")
        return True
    except Exception as e:
        print(f"  ❌ 依赖分析展示失败: {e}")
        return False


def test_nl2code_integration():
    """测试NL2Code集成"""
    print_header("🔄 测试 7: NL2Code集成")
    
    from code_rag.cli_enhanced import EnhancedCLI
    
    cli = EnhancedCLI()
    
    test_queries = [
        "create user authentication",
        "connect to database",
        "validate email format"
    ]
    
    try:
        for query in test_queries:
            result = cli.nl2code_search(query)
            print(f"\n  查询: '{query}'")
            print(f"    ✓ 意图: {result.get('intent', 'N/A')}")
            print(f"    ✓ 置信度: {result.get('confidence', 0):.2f}")
        
        print(f"\n  ✓ NL2Code集成测试成功")
        return True
    except Exception as e:
        print(f"  ❌ NL2Code集成测试失败: {e}")
        return False


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("CLI初始化", test_cli_initialization),
        ("横幅显示", test_cli_banner),
        ("输出格式化", test_output_formats),
        ("搜索结果展示", test_search_results),
        ("代码分析展示", test_code_analysis),
        ("依赖分析展示", test_dependency_analysis),
        ("NL2Code集成", test_nl2code_integration),
    ]
    
    results = []
    
    print_header("🧪 Code RAG v15.0 - CLI测试套件")
    print(f"  测试数量: {len(tests)}")
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
            status = "✅" if result else "❌"
            print(f"\n  {status} {test_name} - {'通过' if result else '失败'}")
        except Exception as e:
            print(f"\n  ❌ {test_name} - 异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print_header("📋 测试总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"\n  📊 结果: {passed}/{total} 测试通过")
    print(f"  ✅ 通过率: {passed/total*100:.1f}%")
    
    print(f"\n  详细结果:")
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"    {status} - {test_name}")
    
    if passed == total:
        print(f"\n  🎉 所有测试通过! CLI v15.0 准备就绪!")
        return True
    else:
        print(f"\n  ⚠️ 部分测试失败，请检查")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
