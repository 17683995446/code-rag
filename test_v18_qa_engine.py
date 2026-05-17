#!/usr/bin/env python3
"""
Code RAG v18.0 - 增强问答引擎测试
测试智能问答、Bug诊断、代码解释
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_code_explainer():
    """测试代码解释器"""
    print_header("📖 测试 1: 代码解释器")
    
    from code_rag.service_layer.enhanced_qa_engine import CodeExplainer
    
    explainer = CodeExplainer()
    
    test_code = '''
import os
import sys

def calculate_sum(numbers):
    """计算列表中所有数字的总和"""
    total = 0
    for num in numbers:
        total += num
    return total

class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, a, b):
        return a + b
'''
    
    print("\n  解释测试代码...")
    explanation = explainer.explain_code(test_code)
    
    print(f"\n  ✓ 摘要: {explanation.summary}")
    print(f"  ✓ 复杂度: {explanation.complexity}")
    print(f"  ✓ 依赖: {explanation.dependencies}")
    
    if explanation.line_by_line:
        print(f"\n  逐行解释:")
        for item in explanation.line_by_line[:5]:
            print(f"    第{item['line']}行: {item['explanation']}")
    
    if explanation.suggestions:
        print(f"\n  建议:")
        for suggestion in explanation.suggestions:
            print(f"    • {suggestion}")
    
    return True


def test_bug_diagnoser():
    """测试Bug诊断器"""
    print_header("🐛 测试 2: Bug诊断器")
    
    from code_rag.service_layer.enhanced_qa_engine import BugDiagnoser
    
    diagnoser = BugDiagnoser()
    
    test_errors = [
        "NameError: name 'undefined_var' is not defined",
        "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
        "IndexError: list index out of range"
    ]
    
    print("\n  诊断测试错误...")
    
    for error in test_errors:
        diagnosis = diagnoser.diagnose(error, "")
        
        print(f"\n  错误: {error}")
        print(f"  ✓ 类型: {diagnosis.bug_type}")
        print(f"  ✓ 严重性: {diagnosis.severity}")
        print(f"  ✓ 原因: {diagnosis.cause}")
        print(f"  ✓ 建议: {diagnosis.suggestion}")
    
    return True


def test_qa_engine():
    """测试问答引擎"""
    print_header("💬 测试 3: 增强问答引擎")
    
    from code_rag.service_layer.enhanced_qa_engine import EnhancedQAEngine
    
    engine = EnhancedQAEngine()
    
    test_cases = [
        ("解释这个函数", "def add(a, b): return a + b"),
        ("这个代码有bug", "print(undefined_var)"),
        ("怎么导入模块", None),
        ("为什么报错", None)
    ]
    
    print("\n  测试问答...")
    
    for question, context in test_cases:
        response = engine.ask(question, context)
        
        print(f"\n  问题: {question}")
        print(f"  ✓ 置信度: {response.confidence}")
        print(f"  回答: {response.answer[:100]}...")
        if response.suggestions:
            print(f"  建议: {response.suggestions[0]}")
    
    return True


def test_explanation_scenarios():
    """测试解释场景"""
    print_header("📚 测试 4: 解释场景")
    
    from code_rag.service_layer.enhanced_qa_engine import CodeExplainer
    
    explainer = CodeExplainer()
    
    scenarios = [
        (
            "简单函数",
            "def greet(name):\n    return f'Hello, {name}!'"
        ),
        (
            "类定义",
            "class User:\n    def __init__(self, name):\n        self.name = name"
        ),
        (
            "导入语句",
            "import pandas as pd\nfrom typing import List"
        )
    ]
    
    print("\n  测试不同场景...")
    
    for name, code in scenarios:
        explanation = explainer.explain_code(code)
        print(f"\n  场景: {name}")
        print(f"  ✓ 摘要: {explanation.summary}")
        print(f"  ✓ 复杂度: {explanation.complexity}")
    
    return True


def test_bug_fix():
    """测试Bug修复"""
    print_header("🔧 测试 5: Bug修复建议")
    
    from code_rag.service_layer.enhanced_qa_engine import BugDiagnoser
    
    diagnoser = BugDiagnoser()
    
    buggy_code = '''
# Bug: 使用未定义的变量
print(undefined_variable)

# Bug: 索引越界
my_list = [1, 2, 3]
print(my_list[10])
'''
    
    print("\n  诊断Bug代码...")
    
    for line in buggy_code.split('\n'):
        if 'undefined' in line or '10' in line:
            diagnosis = diagnoser.diagnose(f"IndexError: list index out of range", buggy_code)
            print(f"\n  诊断:")
            print(f"  ✓ Bug类型: {diagnosis.bug_type}")
            print(f"  ✓ 建议: {diagnosis.suggestion}")
            break
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("代码解释器", test_code_explainer),
        ("Bug诊断器", test_bug_diagnoser),
        ("增强问答引擎", test_qa_engine),
        ("解释场景", test_explanation_scenarios),
        ("Bug修复建议", test_bug_fix)
    ]
    
    results = []
    
    print_header("🧪 Code RAG v18.0 - 增强问答引擎测试")
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
        print(f"\n  🎉 所有测试通过! 增强问答引擎就绪!")
        return True
    else:
        print(f"\n  ⚠️ 部分测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
