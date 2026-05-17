#!/usr/bin/env python3
"""
Code RAG v17.0 - AI对话助手测试
测试对话管理和代码生成功能
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_conversation_manager():
    """测试对话管理器"""
    print_header("💬 测试 1: 对话管理器")
    
    from code_rag.service_layer.conversation_manager import (
        ConversationManager,
        MessageRole,
        Intent
    )
    
    print("\n  创建对话管理器...")
    manager = ConversationManager()
    
    print("\n  创建新会话...")
    session_id = manager.create_session()
    print(f"  ✓ 会话ID: {session_id[:16]}...")
    
    print("\n  测试意图分类:")
    test_messages = [
        ("你好", Intent.GREETING),
        ("帮我搜索用户认证代码", Intent.CODE_SEARCH),
        ("解释这个函数", Intent.CODE_EXPLANATION),
        ("生成一个API接口", Intent.CODE_GENERATION),
        ("这个代码有bug", Intent.BUG_ANALYSIS),
    ]
    
    for message, expected_intent in test_messages:
        result = manager.intent_classifier.classify(message, None)
        status = "✓" if result['intent'] == expected_intent else "⚠️"
        print(f"  {status} '{message}' -> {result['intent'].value} (置信度: {result['confidence']:.2f})")
    
    print("\n  测试消息处理:")
    response = manager.process_message(session_id, "你好")
    print(f"  ✓ 响应意图: {response.intent.value}")
    print(f"  ✓ 置信度: {response.confidence:.2f}")
    print(f"  ✓ 建议数: {len(response.suggestions)}")
    
    response2 = manager.process_message(session_id, "帮我生成一个API接口")
    print(f"\n  ✓ 第二个响应意图: {response2.intent.value}")
    
    return True


def test_code_generator():
    """测试代码生成器"""
    print_header("🛠️ 测试 2: 代码生成器")
    
    from code_rag.service_layer.code_generator import (
        CodeGenerator,
        GenerationRequest
    )
    
    print("\n  创建代码生成器...")
    generator = CodeGenerator()
    
    print("\n  测试API生成:")
    request = GenerationRequest(
        intent="generate API endpoint",
        language="python",
        framework="fastapi",
        context={
            'class_name': 'UserAPI',
            'function_name': 'get_user',
            'path': 'user',
            'method': 'get',
            'description': '获取用户信息'
        }
    )
    
    result = generator.generate(request)
    
    print(f"  ✓ 模板名称: {result.template_name}")
    print(f"  ✓ 编程语言: {result.language}")
    print(f"  ✓ 代码长度: {len(result.code)} 字符")
    
    print(f"\n  生成的代码预览:")
    lines = result.code.split('\n')[:10]
    for line in lines:
        print(f"    {line}")
    if len(result.code.split('\n')) > 10:
        print(f"    ...")
    
    print("\n  测试模型生成:")
    request2 = GenerationRequest(
        intent="generate data model",
        context={'model_name': 'User', 'description': '用户模型'}
    )
    
    result2 = generator.generate(request2)
    print(f"  ✓ 模板: {result2.template_name}")
    
    print("\n  列出可用模板:")
    templates = generator.list_templates()
    print(f"  ✓ 模板类别数: {len(templates)}")
    for cat in templates:
        print(f"    - {cat['category']}: {len(cat['templates'])} 个模板")
    
    return True


def test_intent_classification():
    """测试意图分类"""
    print_header("🎯 测试 3: 意图分类")
    
    from code_rag.service_layer.conversation_manager import IntentClassifier, ConversationContext
    
    classifier = IntentClassifier()
    
    test_cases = [
        "你好",
        "hi there",
        "帮我搜索登录代码",
        "这个函数是什么",
        "写一个数据库连接",
        "程序出错了",
        "应该用什么架构",
        "代码规范是什么",
        "怎么重构这段代码",
        "怎么优化性能"
    ]
    
    print("\n  意图分类测试:")
    for msg in test_cases:
        result = classifier.classify(msg, None)
        print(f"  ✓ '{msg}' -> {result['intent'].value} ({result['confidence']:.2f})")
    
    return True


def test_multi_turn_conversation():
    """测试多轮对话"""
    print_header("🔄 测试 4: 多轮对话")
    
    from code_rag.service_layer.conversation_manager import ConversationManager
    
    manager = ConversationManager()
    session_id = manager.create_session()
    
    conversation = [
        "你好",
        "帮我搜索用户认证代码",
        "能解释一下吗",
        "帮我生成一个类似的API",
        "谢谢，再见"
    ]
    
    print("\n  多轮对话测试:")
    for i, message in enumerate(conversation, 1):
        print(f"\n  第{i}轮:")
        print(f"    用户: {message}")
        
        response = manager.process_message(session_id, message)
        print(f"    助手: {response.intent.value} ({response.confidence:.2f})")
        
        if response.suggestions:
            print(f"    建议: {response.suggestions[0]}")
    
    session = manager.get_session(session_id)
    print(f"\n  ✓ 会话消息数: {len(session.messages)}")
    
    return True


def test_integration():
    """测试集成"""
    print_header("🔗 测试 5: 对话与代码生成集成")
    
    from code_rag.service_layer.conversation_manager import ConversationManager
    from code_rag.service_layer.code_generator import CodeGenerator, GenerationRequest
    
    print("\n  创建组件...")
    conv_manager = ConversationManager()
    code_gen = CodeGenerator()
    
    print("\n  对话流程:")
    session_id = conv_manager.create_session()
    
    response1 = conv_manager.process_message(session_id, "帮我生成一个API接口")
    print(f"  ✓ 对话响应: {response1.intent.value}")
    
    if response1.intent.value == "code_generation":
        gen_request = GenerationRequest(
            intent="generate API endpoint",
            context={
                'class_name': 'TestAPI',
                'function_name': 'test_endpoint',
                'path': 'test',
                'method': 'post',
                'description': '测试接口'
            }
        )
        code = code_gen.generate(gen_request)
        print(f"  ✓ 生成代码: {code.template_name}")
    
    response2 = conv_manager.process_message(session_id, "再生成一个数据模型")
    print(f"  ✓ 继续对话: {response2.intent.value}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("对话管理器", test_conversation_manager),
        ("代码生成器", test_code_generator),
        ("意图分类", test_intent_classification),
        ("多轮对话", test_multi_turn_conversation),
        ("集成测试", test_integration),
    ]
    
    results = []
    
    print_header("🧪 Code RAG v17.0 - AI对话助手测试")
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
        print(f"\n  🎉 所有测试通过! Code RAG v17.0 AI对话助手就绪!")
        return True
    else:
        print(f"\n  ⚠️ 部分测试失败，请检查")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
