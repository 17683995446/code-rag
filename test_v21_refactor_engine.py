#!/usr/bin/env python3
"""
Code RAG v21.0 - 自动重构引擎测试
测试代码分析和重构建议
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v21.0 - 自动重构引擎测试")
print("="*80)

from code_rag.service_layer.refactor_engine import (
    RefactorEngine,
    PatternDetector,
    RefactorType,
    create_refactor_engine
)


def test_pattern_detector():
    """测试模式检测器"""
    print("\n" + "="*70)
    print("测试 1: 模式检测器")
    print("="*70)
    
    detector = PatternDetector()
    
    code = """
def long_function():
    # This is a very long function that should be refactored
    # Many lines of code here
    # More lines
    # Even more
    # Still going
    pass
"""
    
    issues = detector.detect_issues(code)
    
    print(f"  ✅ 检测到 {len(issues)} 个问题")
    for issue in issues:
        print(f"     - [{issue.severity}] {issue.message} (行 {issue.line})")
    
    return True


def test_complexity_analysis():
    """测试复杂度分析"""
    print("\n" + "="*70)
    print("测试 2: 复杂度分析")
    print("="*70)
    
    engine = create_refactor_engine()
    
    code = """
class MyClass:
    def method1(self):
        if True:
            for i in range(10):
                print(i)
    
    def method2(self):
        return 42

def simple_function():
    pass
"""
    
    metrics = engine.analyze_complexity(code)
    
    print(f"  ✅ 复杂度分析完成")
    print(f"     - 圈复杂度: {metrics.cyclomatic_complexity}")
    print(f"     - 代码行数: {metrics.lines_of_code}")
    print(f"     - 函数数量: {metrics.function_count}")
    print(f"     - 类数量: {metrics.class_count}")
    
    assert metrics.class_count > 0
    assert metrics.function_count > 0
    
    return True


def test_refactor_suggestions():
    """测试重构建议"""
    print("\n" + "="*70)
    print("测试 3: 重构建议")
    print("="*70)
    
    engine = create_refactor_engine()
    
    code = """
def process_data(input_data):
    if input_data:
        for item in input_data:
            if item > 0:
                result = item * 2
            else:
                result = 0
    else:
        result = None
    return result
"""
    
    suggestions = engine.suggest_refactors(code)
    
    print(f"  ✅ 生成 {len(suggestions)} 个重构建议")
    for suggestion in suggestions[:3]:
        print(f"     - [{suggestion.impact}] {suggestion.title}")
        print(f"       {suggestion.description}")
    
    return True


def test_refactor_report():
    """测试重构报告"""
    print("\n" + "="*70)
    print("测试 4: 重构报告生成")
    print("="*70)
    
    engine = create_refactor_engine()
    
    code = """
def example_function(param1, param2):
    if param1 and param2:
        return param1 + param2
    else:
        return None
"""
    
    report = engine.generate_report(code)
    
    print(f"  ✅ 重构报告生成成功")
    print(f"     - 问题总数: {report['summary']['total_issues']}")
    print(f"     - 建议总数: {report['summary']['total_suggestions']}")
    print(f"     - 复杂度指标:")
    metrics = report['summary']['complexity_metrics']
    print(f"       * 圈复杂度: {metrics['cyclomatic_complexity']}")
    print(f"       * 代码行数: {metrics['lines_of_code']}")
    
    return True


def test_multilanguage_support():
    """测试多语言支持"""
    print("\n" + "="*70)
    print("测试 5: 多语言支持")
    print("="*70)
    
    engine = create_refactor_engine()
    
    languages = [
        ("python", "def foo(): pass"),
        ("javascript", "function foo() { return 1; }"),
        ("java", "void foo() { }"),
        ("cpp", "void foo() { }"),
        ("go", "func foo() { }"),
    ]
    
    for lang, code in languages:
        metrics = engine.analyze_complexity(code)
        print(f"  ✅ {lang}: {metrics.lines_of_code} 行, {metrics.function_count} 函数")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("模式检测器", test_pattern_detector),
        ("复杂度分析", test_complexity_analysis),
        ("重构建议", test_refactor_suggestions),
        ("重构报告", test_refactor_report),
        ("多语言支持", test_multilanguage_support),
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
    print("📋 自动重构引擎测试总结")
    print("="*80)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有自动重构引擎测试通过！")
        return True
    else:
        print(f"\n⚠️ {failed}个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
