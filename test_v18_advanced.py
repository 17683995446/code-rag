#!/usr/bin/env python3
"""
Code RAG v18.0 - 高级审查功能测试
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_advanced_reviewer():
    """测试高级审查器"""
    print_header("🔍 测试: 高级代码审查")
    
    from code_rag.service_layer.advanced_code_reviewer import (
        AdvancedCodeReviewer,
        PerformanceChecker,
        BestPracticeChecker
    )
    
    print("\n  创建高级审查器...")
    reviewer = AdvancedCodeReviewer()
    
    test_code = '''
import logging
logger = logging.getLogger(__name__)

def inefficient_function():
    result = []
    for i in range(100):
        for j in range(100):
            result.append(i * j)
    return result

def bad_function():
    try:
        x = 1 / 0
    except:
        pass

def good_function(x: int) -> str:
    """
    这是一个好函数
    
    Args:
        x: 输入参数
        
    Returns:
        字符串结果
    """
    return str(x)
'''
    
    print("\n  高级审查测试代码...")
    issues = reviewer.review_file_advanced("advanced_test.py", test_code)
    
    print(f"\n  ✓ 发现 {len(issues)} 个问题")
    
    for i, issue in enumerate(issues[:10], 1):
        print(f"\n  {i}. [{issue.issue_type.value}] {issue.message}")
        print(f"     严重性: {issue.severity.value}")
        if issue.suggestion:
            print(f"     建议: {issue.suggestion}")
    
    return True


def test_performance_checker():
    """测试性能检查"""
    print_header("⚡ 测试: 性能检查")
    
    from code_rag.service_layer.advanced_code_reviewer import PerformanceChecker
    
    checker = PerformanceChecker()
    
    test_code = '''
def nested_loop():
    for i in range(100):
        for j in range(100):
            print(i, j)

def bad_query():
    users = db.query(User).all()
    return users

def read_file():
    content = open('file.txt').read()
    return content
'''
    
    print("\n  检查性能问题...")
    issues = checker.check_performance(test_code)
    issues.extend(checker.check_database_queries(test_code))
    issues.extend(checker.check_memory_usage(test_code))
    
    print(f"\n  ✓ 发现 {len(issues)} 个性能问题")
    
    for i, issue in enumerate(issues, 1):
        print(f"\n  {i}. [{issue.severity.value}] {issue.message}")
        print(f"     建议: {issue.suggestion}")
    
    return True


def test_best_practice_checker():
    """测试最佳实践检查"""
    print_header("✨ 测试: 最佳实践检查")
    
    from code_rag.service_layer.advanced_code_reviewer import BestPracticeChecker
    
    checker = BestPracticeChecker()
    
    test_code = '''
def without_type_hint(x, y):
    return x + y

def with_bug():
    try:
        x = 1 / 0
    except:
        pass

class MyFactory:
    pass
'''
    
    print("\n  检查最佳实践...")
    issues = checker.check_best_practices(test_code)
    issues.extend(checker.check_error_handling(test_code))
    issues.extend(checker.check_design_patterns(test_code))
    
    print(f"\n  ✓ 发现 {len(issues)} 个最佳实践问题")
    
    for i, issue in enumerate(issues, 1):
        print(f"\n  {i}. [{issue.severity.value}] {issue.message}")
        print(f"     建议: {issue.suggestion}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("高级审查器", test_advanced_reviewer),
        ("性能检查", test_performance_checker),
        ("最佳实践检查", test_best_practice_checker),
    ]
    
    results = []
    
    print_header("🧪 Code RAG v18.0 - 高级审查功能测试")
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
    
    if passed == total:
        print(f"\n  🎉 所有高级审查测试通过!")
        return True
    else:
        print(f"\n  ⚠️ 部分测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
