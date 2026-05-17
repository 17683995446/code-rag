"""
Code RAG v18.0 - 上下文理解增强测试
测试多轮对话和上下文管理功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from code_rag.service_layer.context_understanding import (
    ContextManager, ConversationContext, ContextualQAManager, 
    MultiTurnDialogueManager, Message
)


def test_context_manager():
    """测试上下文管理器"""
    print("\n" + "="*80)
    print("🧪 测试 1: 上下文管理器")
    print("="*80)
    
    manager = ContextManager(max_history=10)
    
    conv_id = "test_conv_001"
    context = manager.create_conversation(conv_id)
    
    print(f"✓ 创建对话: {conv_id}")
    assert manager.get_context(conv_id) is not None
    print("✓ 获取上下文成功")
    
    manager.add_message(conv_id, "user", "你好，我想了解Python")
    manager.add_message(conv_id, "assistant", "您好！请问您想了解Python的哪方面？")
    manager.add_message(conv_id, "user", "我想知道如何定义函数")
    
    history = manager.get_history(conv_id)
    print(f"✓ 对话历史: {len(history)} 条消息")
    assert len(history) == 3
    
    context_window = manager.get_context_window(conv_id, window_size=2)
    print(f"✓ 上下文窗口: {len(context_window)} 条消息")
    
    context.add_turn("function_definition", "Python函数", ["函数", "定义"])
    context.add_code_snippet("def my_func(): pass")
    
    summary = manager.get_conversation_summary(conv_id)
    print(f"✓ 对话摘要:")
    print(f"  - 主题: {summary.get('topic')}")
    print(f"  - 轮次: {summary.get('turns_count')}")
    print(f"  - 代码片段: {summary.get('code_snippets_count')}")
    
    print("\n✅ 上下文管理器 - 通过")
    return True


def test_contextual_qa_manager():
    """测试上下文感知问答管理器"""
    print("\n" + "="*80)
    print("💬 测试 2: 上下文感知问答管理器")
    print("="*80)
    
    qa_manager = ContextualQAManager()
    
    conv_id = qa_manager.start_conversation()
    print(f"✓ 开始新对话: {conv_id}")
    
    qa_manager.add_user_message("解释这段代码")
    qa_manager.add_assistant_message("好的，请提供代码")
    qa_manager.add_user_message("它有什么问题")
    
    is_follow_up = qa_manager.is_follow_up_question("它有什么问题")
    print(f"✓ 识别后续问题: {is_follow_up}")
    assert is_follow_up
    
    resolved = qa_manager.resolve_pronouns("它有什么问题")
    print(f"✓ 代词解析: '{resolved}'")
    
    contextual_prompt = qa_manager.get_contextual_prompt("怎么修复？", window_size=3)
    print(f"✓ 生成上下文提示:")
    print(f"  {contextual_prompt[:100]}...")
    
    state = qa_manager.get_conversation_state()
    print(f"✓ 对话状态:")
    print(f"  - 活跃: {state.get('active')}")
    print(f"  - 对话ID: {state.get('conversation_id')}")
    
    print("\n✅ 上下文感知问答管理器 - 通过")
    return True


def test_multi_turn_dialogue():
    """测试多轮对话管理器"""
    print("\n" + "="*80)
    print("🔄 测试 3: 多轮对话管理器")
    print("="*80)
    
    dialogue_manager = MultiTurnDialogueManager()
    
    print("\n第一轮对话:")
    result1 = dialogue_manager.process_input("你好，我想学习Python")
    print(f"✓ 用户: 你好，我想学习Python")
    print(f"✓ 策略: {result1['response']['strategy']}")
    print(f"✓ 是后续问题: {result1['is_follow_up']}")
    
    print("\n第二轮对话 (后续问题):")
    result2 = dialogue_manager.process_input("它有什么优点")
    print(f"✓ 用户: 它有什么优点")
    print(f"✓ 策略: {result2['response']['strategy']}")
    print(f"✓ 是后续问题: {result2['is_follow_up']}")
    print(f"✓ 解析后: {result2['resolved_input']}")
    
    print("\n第三轮对话 (总结):")
    result3 = dialogue_manager.process_input("总结一下我们的对话", intent="summary")
    print(f"✓ 用户: 总结一下我们的对话")
    print(f"✓ 策略: {result3['response']['strategy']}")
    print(f"✓ 回答: {result3['response']['answer'][:100]}...")
    
    state = dialogue_manager.qa_manager.get_conversation_state()
    print(f"\n✓ 最终对话状态:")
    print(f"  - 活跃: {state.get('active')}")
    print(f"  - 轮次: {state.get('summary', {}).get('turns_count', 0)}")
    
    print("\n✅ 多轮对话管理器 - 通过")
    return True


def test_conversation_export_import():
    """测试对话导入导出"""
    print("\n" + "="*80)
    print("💾 测试 4: 对话导入导出")
    print("="*80)
    
    manager = ContextManager()
    conv_id = "export_test"
    manager.create_conversation(conv_id)
    
    manager.add_message(conv_id, "user", "测试消息1")
    manager.add_message(conv_id, "assistant", "回复1")
    manager.add_message(conv_id, "user", "测试消息2")
    
    context = manager.get_context(conv_id)
    context.add_code_snippet("x = 1")
    context.topic = "测试主题"
    
    json_export = manager.export_conversation(conv_id)
    print(f"✓ 导出对话成功: {len(json_export)} 字符")
    
    manager2 = ContextManager()
    imported_id = manager2.import_conversation(json_export)
    print(f"✓ 导入对话成功: {imported_id}")
    
    imported_context = manager2.get_context(imported_id)
    assert imported_context.topic == "测试主题"
    print(f"✓ 主题验证: {imported_context.topic}")
    
    imported_history = manager2.get_history(imported_id)
    assert len(imported_history) == 3
    print(f"✓ 消息数量验证: {len(imported_history)}")
    
    print("\n✅ 对话导入导出 - 通过")
    return True


def test_entity_tracking():
    """测试实体追踪"""
    print("\n" + "="*80)
    print("🎯 测试 5: 实体追踪")
    print("="*80)
    
    manager = ContextManager()
    conv_id = "entity_test"
    manager.create_conversation(conv_id)
    
    context = manager.get_context(conv_id)
    context.add_turn("python_intro", "Python编程", ["Python", "函数", "类"])
    context.add_turn("java_intro", "Java编程", ["Java", "对象"])
    context.add_turn("refactor", "代码重构", ["重构", "优化"])
    
    entities = manager.extract_entities_from_context(conv_id)
    print(f"✓ 提取实体: {entities}")
    assert len(entities) >= 5
    
    code_snippets = manager.extract_code_snippets(conv_id)
    print(f"✓ 提取代码片段: {code_snippets}")
    
    summary = manager.get_conversation_summary(conv_id)
    print(f"✓ 最近意图: {summary.get('recent_intents')}")
    
    print("\n✅ 实体追踪 - 通过")
    return True


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*80)
    print("🎯 Code RAG v18.0 - 上下文理解增强测试")
    print("="*80)
    
    tests = [
        ("上下文管理器", test_context_manager),
        ("上下文感知问答", test_contextual_qa_manager),
        ("多轮对话", test_multi_turn_dialogue),
        ("导入导出", test_conversation_export_import),
        ("实体追踪", test_entity_tracking),
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
    print("📋 测试总结")
    print("="*80)
    print(f"📊 结果: {passed}/{len(tests)} 测试通过")
    print(f"✅ 通过率: {100*passed/len(tests):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有测试通过! 上下文理解增强就绪!")
        return True
    else:
        print(f"\n⚠️ {failed} 个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
