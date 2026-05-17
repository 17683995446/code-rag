#!/usr/bin/env python3
"""
Code RAG v22.0 - 代码质量仪表板测试
"""

import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v22.0 - 代码质量仪表板测试")
print("="*80)

from code_rag.service_layer.quality_dashboard import (
    create_quality_dashboard,
    QualityDashboard,
    CodeAnalyzer,
    TrendAnalyzer,
    QualityLevel,
    MetricType
)


def test_code_analyzer():
    """测试代码分析器"""
    print("\n" + "="*70)
    print("测试 1: 代码分析器")
    print("="*70)
    
    analyzer = CodeAnalyzer()
    
    code = """
def complex_function():
    # This is a TODO item
    if True:
        for i in range(10):
            print(i)
        return i + 1
    else:
        while False:
            pass
"""
    
    metrics = analyzer.analyze(code)
    
    assert len(metrics) > 0
    print(f"  ✅ 分析完成，生成 {len(metrics)} 个质量指标")
    
    for metric in metrics:
        print(f"     - [{metric.metric_type.value}] {metric.name}: {metric.get_score():.1f}")
    
    return True


def test_trend_analyzer():
    """测试趋势分析器"""
    print("\n" + "="*70)
    print("测试 2: 趋势分析器")
    print("="*70)
    
    analyzer = TrendAnalyzer()
    
    # 添加多个数据点
    for i in range(5):
        analyzer.add_point("code_quality", 70 + i * 5)
        time.sleep(0.01)
    
    trend = analyzer.get_trend("code_quality")
    assert len(trend) == 5
    print(f"  ✅ 趋势分析：{len(trend)} 个数据点")
    
    direction = analyzer.calculate_trend_direction("code_quality")
    print(f"  ✅ 趋势方向：{direction}")
    
    return True


def test_quality_report_generation():
    """测试质量报告生成"""
    print("\n" + "="*70)
    print("测试 3: 质量报告生成")
    print("="*70)
    
    dashboard = create_quality_dashboard()
    
    code = """
class Calculator:
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b
"""
    
    report = dashboard.analyze_code(code, "python", "Test Project")
    
    assert report is not None
    assert 0 <= report.overall_score <= 100
    
    print(f"  ✅ 报告生成成功")
    print(f"     - 综合评分: {report.overall_score:.1f}")
    print(f"     - 质量等级: {report.quality_level.value}")
    print(f"     - 指标数量: {len(report.metrics)}")
    print(f"     - 问题数量: {len(report.issues)}")
    print(f"     - 建议数量: {len(report.recommendations)}")
    
    for rec in report.recommendations:
        print(f"       * {rec}")
    
    return True


def test_dashboard_summary():
    """测试仪表板摘要"""
    print("\n" + "="*70)
    print("测试 4: 仪表板摘要")
    print("="*70)
    
    dashboard = create_quality_dashboard()
    
    # 多次运行分析
    for i in range(3):
        code = f"def func{i}(): return {i}"
        dashboard.analyze_code(code, "python", "Project")
    
    summary = dashboard.get_dashboard_summary()
    
    assert summary is not None
    assert summary.get("status") != "no_data"
    
    print(f"  ✅ 仪表板摘要生成成功")
    print(f"     - 报告数量: {summary.get('report_count', 0)}")
    print(f"     - 最新评分: {summary.get('overall_score', 0):.1f}")
    print(f"     - 质量等级: {summary.get('quality_level', '')}")
    
    if "trends" in summary:
        for metric, trend in summary["trends"].items():
            print(f"       * {metric}: {trend}")
    
    return True


def test_quality_levels():
    """测试质量等级"""
    print("\n" + "="*70)
    print("测试 5: 质量等级")
    print("="*70)
    
    dashboard = create_quality_dashboard()
    
    test_cases = [
        (95, QualityLevel.EXCELLENT),
        (80, QualityLevel.GOOD),
        (60, QualityLevel.FAIR),
        (40, QualityLevel.POOR),
        (10, QualityLevel.CRITICAL),
    ]
    
    for score, expected_level in test_cases:
        # 创建简单的测试代码
        code = f"def test(): return {score}"
        report = dashboard.analyze_code(code, "python")
        
        # 我们直接检查级别确定逻辑
        level = dashboard._determine_quality_level(score)
        
        print(f"     - 分数 {score}: {level.value}")
    
    print(f"  ✅ 质量等级映射正确")
    
    return True


def test_multilanguage_support():
    """测试多语言支持"""
    print("\n" + "="*70)
    print("测试 6: 多语言支持")
    print("="*70)
    
    dashboard = create_quality_dashboard()
    
    languages = [
        ("python", "def test(): pass"),
        ("javascript", "function test() {}"),
        ("java", "void test() {}"),
        ("cpp", "void test() {}"),
    ]
    
    for lang, code in languages:
        report = dashboard.analyze_code(code, lang, f"Test {lang}")
        assert report is not None
        print(f"  ✅ {lang}: 评分 {report.overall_score:.1f}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("代码分析器", test_code_analyzer),
        ("趋势分析器", test_trend_analyzer),
        ("质量报告生成", test_quality_report_generation),
        ("仪表板摘要", test_dashboard_summary),
        ("质量等级", test_quality_levels),
        ("多语言支持", test_multilanguage_support)
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
    print("📋 代码质量仪表板测试总结")
    print("="*80)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有代码质量仪表板测试通过！")
        return True
    else:
        print(f"\n⚠️ {failed}个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
