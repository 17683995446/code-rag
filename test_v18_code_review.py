#!/usr/bin/env python3
"""
Code RAG v18.0 - 代码审查系统测试
测试代码审查、质量评估和优化建议
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_code_reviewer():
    """测试代码审查器"""
    print_header("🔍 测试 1: 代码审查器")
    
    from code_rag.service_layer.code_reviewer import (
        CodeReviewer,
        Severity,
        IssueType
    )
    
    print("\n  创建代码审查器...")
    reviewer = CodeReviewer()
    
    test_code = '''
import os
import sys

def calculate(x, y):
    # TODO: refactor
    if x > 10:
        if y > 5:
            if x > y:
                if y > 0:
                    return x + y
    return 0

def tmp(x):
    return x * 2

class MyClass:
    def __init__(self):
        self.data = None
    
    def process(self):
        eval("print('test')")
        return self.data

PASSWORD = "hardcoded_password_123"

def very_long_function_name_that_exceeds_reasonable_length():
    # This is a very long function name that should trigger a warning
    pass
'''
    
    print("\n  审查测试代码...")
    report = reviewer.review_file("test_code.py", test_code)
    
    print(f"\n  ✓ 审查完成")
    print(f"  ✓ 总行数: {report.total_lines}")
    print(f"  ✓ 问题数: {len(report.issues)}")
    
    if report.issues:
        print(f"\n  发现的问题:")
        for i, issue in enumerate(report.issues[:10], 1):
            print(f"\n  {i}. [{issue.severity.value.upper()}] {issue.message}")
            print(f"     行号: {issue.line_number}")
            print(f"     类型: {issue.issue_type.value}")
    
    return True


def test_security_checker():
    """测试安全检查"""
    print_header("🔒 测试 2: 安全检查")
    
    from code_rag.service_layer.code_reviewer import SecurityChecker, CodeIssue
    
    checker = SecurityChecker()
    
    test_code = '''
# Test security issues
password = "hardcoded123"
eval("print('hello')")
exec("os.system('ls')")
api_key = "sk_test_secret_key_123"
'''
    
    print("\n  检查安全漏洞...")
    issues = checker.check_security(test_code, "test.py")
    
    print(f"\n  ✓ 发现 {len(issues)} 个安全问题")
    
    for i, issue in enumerate(issues, 1):
        print(f"\n  {i}. [{issue.severity.value.upper()}] {issue.message}")
        print(f"     建议: {issue.suggestion}")
    
    return True


def test_complexity_checker():
    """测试复杂度检查"""
    print_header("📊 测试 3: 复杂度检查")
    
    from code_rag.service_layer.code_reviewer import ComplexityChecker
    
    checker = ComplexityChecker()
    
    test_code = '''
if condition1:
    if condition2:
        if condition3:
            if condition4:
                if condition5:
                    do_something()
'''
    
    print("\n  计算圈复杂度...")
    complexity = checker.calculate_complexity(test_code)
    print(f"  ✓ 圈复杂度: {complexity}")
    
    if complexity > 10:
        print(f"  ⚠️  复杂度较高，建议拆分")
    
    return True


def test_naming_checker():
    """测试命名检查"""
    print_header("📝 测试 4: 命名检查")
    
    from code_rag.service_layer.code_reviewer import NamingChecker
    
    checker = NamingChecker()
    
    test_names = ['tmp', 'get_user_by_id', 'MyClass', 'foo', 'calculate_sum']
    
    print("\n  检查命名规范...")
    
    for name in test_names:
        issues = checker.check_function_name(name)
        if issues:
            print(f"  ⚠️  '{name}': {issues[0]}")
        else:
            print(f"  ✓  '{name}': 命名规范")
    
    return True


def test_real_project_review():
    """测试真实项目审查"""
    print_header("🏢 测试 5: 真实项目审查")
    
    from code_rag.service_layer.code_reviewer import CodeReviewer
    
    reviewer = CodeReviewer()
    
    test_dir = str(PROJECT_ROOT / "src" / "code_rag")
    
    print(f"\n  审查目录: {test_dir}")
    print("  (审查前10个文件)")
    
    reports = reviewer.review_directory(test_dir)[:10]
    
    total_issues = 0
    critical_count = 0
    
    for report in reports:
        total_issues += len(report.issues)
        critical_count += report.metrics.get('critical_count', 0)
    
    print(f"\n  ✓ 审查完成")
    print(f"  ✓ 审查文件: {len(reports)}")
    print(f"  ✓ 发现问题: {total_issues}")
    print(f"  ✓ 严重问题: {critical_count}")
    
    return True


def test_review_summary():
    """测试审查报告汇总"""
    print_header("📋 测试 6: 审查报告汇总")
    
    from code_rag.service_layer.code_reviewer import CodeReviewer
    
    reviewer = CodeReviewer()
    
    test_code = '''
def example_function():
    password = "secret123"
    eval("print('test')")
    
    if x > 0:
        if y > 0:
            if z > 0:
                return True
    return False
'''
    
    report = reviewer.review_file("example.py", test_code)
    
    print(f"\n  审查报告汇总:")
    print(f"  文件: {report.file_path}")
    print(f"  总行数: {report.total_lines}")
    print(f"  问题总数: {len(report.issues)}")
    
    print(f"\n  问题分布:")
    for severity, count in report.summary.items():
        if count > 0:
            print(f"    {severity.upper()}: {count}")
    
    print(f"\n  指标:")
    for key, value in report.metrics.items():
        print(f"    {key}: {value}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("代码审查器", test_code_reviewer),
        ("安全检查", test_security_checker),
        ("复杂度检查", test_complexity_checker),
        ("命名检查", test_naming_checker),
        ("真实项目审查", test_real_project_review),
        ("审查报告汇总", test_review_summary),
    ]
    
    results = []
    
    print_header("🧪 Code RAG v18.0 - 代码审查系统测试")
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
        print(f"\n  🎉 所有测试通过! 代码审查系统就绪!")
        return True
    else:
        print(f"\n  ⚠️ 部分测试失败，请检查")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
