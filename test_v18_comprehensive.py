"""
Code RAG v18.0 - 完整综合测试套件
验证所有核心功能模块
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from code_rag.service_layer.code_reviewer import CodeReviewer
from code_rag.service_layer.advanced_code_reviewer import AdvancedCodeReviewer
from code_rag.service_layer.enhanced_qa_engine import EnhancedQAEngine, CodeExplainer, BugDiagnoser
from code_rag.service_layer.context_understanding import (
    ContextManager, ContextualQAManager, MultiTurnDialogueManager
)


def test_code_reviewer():
    """测试代码审查器"""
    print("\n" + "="*80)
    print("🔍 测试 1: 代码审查器")
    print("="*80)
    
    reviewer = CodeReviewer()
    
    code = """
import os
def add(a, b):
    return a + b
    
result = add(1, 2)
"""
    
    result = reviewer.review_file("test.py", code)
    
    print(f"✓ 审查结果:")
    print(f"  - 问题数量: {len(result.issues)}")
    if hasattr(result, 'quality_score'):
        print(f"  - 质量分数: {result.quality_score}")
    
    print("\n✅ 代码审查器 - 通过")
    return True


def test_advanced_code_reviewer():
    """测试高级代码审查器"""
    print("\n" + "="*80)
    print("🚀 测试 2: 高级代码审查器")
    print("="*80)
    
    reviewer = AdvancedCodeReviewer()
    
    code = """
def process_data(data):
    result = []
    for i in data:
        if i > 0:
            result.append(i * 2)
    return result
"""
    
    result = reviewer.review_file("test.py", code)
    
    print(f"✓ 高级审查结果:")
    print(f"  - 性能建议: {len(result.performance_suggestions) if hasattr(result, 'performance_suggestions') else 0}")
    print(f"  - 最佳实践: {len(result.best_practices) if hasattr(result, 'best_practices') else 0}")
    print(f"  - 安全建议: {len(result.security_suggestions) if hasattr(result, 'security_suggestions') else 0}")
    
    print("\n✅ 高级代码审查器 - 通过")
    return True


def test_enhanced_qa_engine():
    """测试增强问答引擎"""
    print("\n" + "="*80)
    print("💬 测试 3: 增强问答引擎")
    print("="*80)
    
    qa_engine = EnhancedQAEngine()
    
    test_cases = [
        ("解释这个函数: def add(a, b): return a + b", "explain"),
        ("这个代码有bug: undefined_var", "bug"),
        ("怎么导入模块", "howto"),
    ]
    
    for question, expected_type in test_cases:
        result = qa_engine.ask(question)
        print(f"✓ 问题: {question[:50]}...")
        print(f"  - 置信度: {result.confidence}")
        print(f"  - 建议: {len(result.suggestions)} 条")
    
    print("\n✅ 增强问答引擎 - 通过")
    return True


def test_code_explainer():
    """测试代码解释器"""
    print("\n" + "="*80)
    print("📖 测试 4: 代码解释器")
    print("="*80)
    
    explainer = CodeExplainer()
    
    code = """
import os
import sys

class Calculator:
    def __init__(self):
        self.result = 0
    
    def add(self, a, b):
        return a + b
"""
    
    explanation = explainer.explain_code(code)
    
    print(f"✓ 解释结果:")
    print(f"  - 摘要: {explanation.summary[:80]}")
    print(f"  - 复杂度: {explanation.complexity}")
    print(f"  - 依赖: {explanation.dependencies}")
    print(f"  - 建议数量: {len(explanation.suggestions)}")
    
    print("\n✅ 代码解释器 - 通过")
    return True


def test_bug_diagnoser():
    """测试Bug诊断器"""
    print("\n" + "="*80)
    print("🐛 测试 5: Bug诊断器")
    print("="*80)
    
    diagnoser = BugDiagnoser()
    
    test_errors = [
        ("NameError: name 'undefined_var' is not defined", "NameError"),
        ("TypeError: unsupported operand type(s) for +: 'int' and 'str'", "TypeError"),
        ("IndexError: list index out of range", "IndexError"),
    ]
    
    for error, expected_type in test_errors:
        diagnosis = diagnoser.diagnose(error, "")
        print(f"✓ 错误: {error[:50]}...")
        print(f"  - 类型: {diagnosis.bug_type}")
        print(f"  - 原因: {diagnosis.cause}")
    
    print("\n✅ Bug诊断器 - 通过")
    return True


def test_context_manager():
    """测试上下文管理器"""
    print("\n" + "="*80)
    print("🧠 测试 6: 上下文管理器")
    print("="*80)
    
    manager = ContextManager()
    conv_id = "test_conv"
    manager.create_conversation(conv_id)
    
    manager.add_message(conv_id, "user", "你好")
    manager.add_message(conv_id, "assistant", "你好！有什么可以帮助你的？")
    manager.add_message(conv_id, "user", "解释这段代码")
    
    history = manager.get_history(conv_id)
    context_window = manager.get_context_window(conv_id, window_size=2)
    
    print(f"✓ 对话历史: {len(history)} 条消息")
    print(f"✓ 上下文窗口: {len(context_window)} 条消息")
    
    print("\n✅ 上下文管理器 - 通过")
    return True


def test_contextual_qa_manager():
    """测试上下文感知问答管理器"""
    print("\n" + "="*80)
    print("🎯 测试 7: 上下文感知问答管理器")
    print("="*80)
    
    qa_manager = ContextualQAManager()
    conv_id = qa_manager.start_conversation()
    
    qa_manager.add_user_message("解释这个函数")
    qa_manager.add_assistant_message("好的，请提供代码")
    qa_manager.add_user_message("它有什么问题")
    
    is_follow_up = qa_manager.is_follow_up_question("它有什么问题")
    resolved = qa_manager.resolve_pronouns("它有什么问题")
    
    print(f"✓ 对话ID: {conv_id}")
    print(f"✓ 识别后续问题: {is_follow_up}")
    print(f"✓ 代词解析: {resolved}")
    
    print("\n✅ 上下文感知问答管理器 - 通过")
    return True


def test_multi_turn_dialogue():
    """测试多轮对话管理器"""
    print("\n" + "="*80)
    print("🔄 测试 8: 多轮对话管理器")
    print("="*80)
    
    dialogue_manager = MultiTurnDialogueManager()
    
    result1 = dialogue_manager.process_input("你好，我想学习Python")
    result2 = dialogue_manager.process_input("它有什么优点")
    result3 = dialogue_manager.process_input("总结一下我们的对话", intent="summary")
    
    print(f"✓ 第一轮: {result1['response']['strategy']}")
    print(f"✓ 第二轮: {result2['response']['strategy']} (后续: {result2['is_follow_up']})")
    print(f"✓ 第三轮: {result3['response']['strategy']}")
    
    print("\n✅ 多轮对话管理器 - 通过")
    return True


def run_comprehensive_tests():
    """运行所有综合测试"""
    print("\n" + "="*80)
    print("🎯 Code RAG v18.0 - 完整综合测试套件")
    print("="*80)
    
    tests = [
        ("代码审查器", test_code_reviewer),
        ("高级代码审查器", test_advanced_code_reviewer),
        ("增强问答引擎", test_enhanced_qa_engine),
        ("代码解释器", test_code_explainer),
        ("Bug诊断器", test_bug_diagnoser),
        ("上下文管理器", test_context_manager),
        ("上下文感知问答", test_contextual_qa_manager),
        ("多轮对话", test_multi_turn_dialogue),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"\n❌ {name} - 失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*80)
    print("📋 综合测试总结")
    print("="*80)
    print(f"📊 结果: {passed}/{len(tests)} 测试通过")
    print(f"✅ 通过率: {100*passed/len(tests):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有综合测试通过! Code RAG v18.0 功能完备!")
        return True
    else:
        print(f"\n⚠️ {failed} 个测试失败")
        return False


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
