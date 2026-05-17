#!/usr/bin/env python3
"""
Code RAG v23.0 - 自主代码分析代理测试
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v23.0 - 自主代码分析代理测试")
print("="*80)

from code_rag.service_layer.autonomous_agent import (
    create_autonomous_agent,
    AutonomousCodeAgent,
    PerceptionModule,
    DecisionEngine,
    ActionExecutor,
    AgentState,
    AnalysisType
)


def test_perception_module():
    """测试感知模块"""
    print("\n" + "="*70)
    print("测试 1: 感知模块")
    print("="*70)
    
    perception = PerceptionModule()
    
    code = """
def complex_function(items):
    for item in items:
        if item.value == None:
            pass
    return items
"""
    
    context = perception.analyze_context(code, "python")
    
    assert context is not None
    assert "patterns" in context
    assert "structure" in context
    
    print(f"  ✅ 上下文分析完成")
    print(f"     - 语言: {context['language']}")
    print(f"     - 行数: {context['lines']}")
    print(f"     - 复杂度: {context['complexity']}")
    print(f"     - 检测到模式: {len(context['patterns'])} 个")
    
    return True


def test_decision_engine():
    """测试决策引擎"""
    print("\n" + "="*70)
    print("测试 2: 决策引擎")
    print("="*70)
    
    engine = DecisionEngine()
    
    # 测试高复杂度上下文
    high_complexity_context = {"complexity": 15, "lines": 100}
    actions = engine.decide(high_complexity_context)
    
    print(f"  ✅ 决策生成: {len(actions)} 个行动")
    for action in actions:
        print(f"     - [{action.action_type}] {action.description}")
    
    return True


def test_action_executor():
    """测试行动执行器"""
    print("\n" + "="*70)
    print("测试 3: 行动执行器")
    print("="*70)
    
    executor = ActionExecutor()
    
    code_with_issues = """
password = "hardcoded_secret"
global_data = 42
"""
    
    result = executor.execute(
        type('Action', (), {
            'action_type': 'security_review',
            'description': 'Security check',
            'priority': 1
        })(),
        code_with_issues
    )
    
    assert result is not None
    assert result["success"] is True
    
    print(f"  ✅ 行动执行成功")
    print(f"     - 类型: {result['action']}")
    print(f"     - 成功: {result['success']}")
    
    return True


def test_autonomous_agent_basic():
    """测试自主代理基础功能"""
    print("\n" + "="*70)
    print("测试 4: 自主代理基础")
    print("="*70)
    
    agent = create_autonomous_agent()
    
    code = """
def calculate_sum(numbers):
    result = 0
    for n in numbers:
        result = result + n
    return result

class DataProcessor:
    def process(self, data):
        return [x * 2 for x in data]
"""
    
    result = agent.analyze(code)
    
    assert result is not None
    assert "context" in result
    assert "actions" in result
    
    print(f"  ✅ 代码分析完成")
    print(f"     - 洞察数: {result['insights_count']}")
    print(f"     - 上下文: {result['context']['structure']['functions']} 个函数")
    
    return True


def test_specific_analysis_types():
    """测试特定类型分析"""
    print("\n" + "="*70)
    print("测试 5: 特定类型分析")
    print("="*70)
    
    agent = create_autonomous_agent()
    
    code = """
password = "secret123"
result = ""
for i in range(100):
    result = result + str(i)

def complex_func(x, y, z):
    return x + y + z
"""
    
    # 性能分析
    perf_insights = agent.get_insights(code, AnalysisType.PERFORMANCE)
    print(f"  ✅ 性能分析: {len(perf_insights)} 个洞察")
    
    # 安全分析
    sec_insights = agent.get_insights(code, AnalysisType.SECURITY)
    print(f"  ✅ 安全分析: {len(sec_insights)} 个洞察")
    
    # 质量分析
    qual_insights = agent.get_insights(code, AnalysisType.QUALITY)
    print(f"  ✅ 质量分析: {len(qual_insights)} 个洞察")
    
    # 架构分析
    arch_insights = agent.get_insights(code, AnalysisType.ARCHITECTURE)
    print(f"  ✅ 架构分析: {len(arch_insights)} 个洞察")
    
    return True


def test_monitoring():
    """测试监控功能"""
    print("\n" + "="*70)
    print("测试 6: 监控功能")
    print("="*70)
    
    agent = create_autonomous_agent()
    
    code = "def test(): pass"
    
    # 开始监控
    agent.monitor(code, interval=5)
    assert agent.is_monitoring is True
    print(f"  ✅ 监控启动成功")
    
    # 停止监控
    agent.stop_monitoring()
    assert agent.is_monitoring is False
    print(f"  ✅ 监控停止成功")
    
    return True


def test_report_generation():
    """测试报告生成"""
    print("\n" + "="*70)
    print("测试 7: 报告生成")
    print("="*70)
    
    agent = create_autonomous_agent()
    
    # 先分析一些代码
    agent.analyze("""
password = "secret"
def slow(): pass
""")
    
    report = agent.generate_report()
    
    assert report is not None
    print(f"  ✅ 报告生成成功")
    print(f"     - 代理状态: {report['agent_state']}")
    print(f"     - 总洞察数: {report['total_insights']}")
    print(f"     - 监控状态: {report['monitoring_active']}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("感知模块", test_perception_module),
        ("决策引擎", test_decision_engine),
        ("行动执行器", test_action_executor),
        ("自主代理基础", test_autonomous_agent_basic),
        ("特定类型分析", test_specific_analysis_types),
        ("监控功能", test_monitoring),
        ("报告生成", test_report_generation),
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
    print("📋 自主代码分析代理测试总结")
    print("="*80)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有自主代码分析代理测试通过！")
        return True
    else:
        print(f"\n⚠️ {failed}个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
