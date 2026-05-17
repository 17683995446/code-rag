#!/usr/bin/env python3
"""
Code RAG v21.0 - LLM 客户端测试
测试真实 LLM API 集成
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v21.0 - LLM 客户端测试")
print("="*80)

from code_rag.service_layer.llm_clients import (
    LLMProvider,
    LLMConfig,
    LLMMessage,
    LLMResponse,
    MockLLMClient,
    OpenAIClient,
    AnthropicClient,
    OllamaClient,
    LLMClientFactory,
    EnhancedLLMService,
    create_llm_service
)


def test_mock_client():
    """测试模拟 LLM 客户端"""
    print("\n" + "="*70)
    print("测试 1: 模拟 LLM 客户端")
    print("="*70)
    
    config = LLMConfig(provider=LLMProvider.MOCK)
    client = MockLLMClient(config)
    
    # 测试代码解释
    messages = [
        LLMMessage("user", "Explain this code: def add(a, b): return a + b")
    ]
    response = client.generate(messages)
    
    assert isinstance(response, LLMResponse)
    assert len(response.content) > 0
    assert response.provider == "mock"
    print(f"  ✅ 模拟客户端生成响应")
    print(f"  ✅ Provider: {response.provider}")
    print(f"  ✅ Tokens: {response.tokens_used}")
    
    return True


def test_llm_config():
    """测试 LLM 配置"""
    print("\n" + "="*70)
    print("测试 2: LLM 配置管理")
    print("="*70)
    
    # 手动配置
    config = LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4",
        temperature=0.5
    )
    
    assert config.provider == LLMProvider.OPENAI
    assert config.model == "gpt-4"
    print(f"  ✅ 手动配置成功: {config.provider.value}/{config.model}")
    
    # 环境变量配置（模拟）
    os.environ["LLM_PROVIDER"] = "anthropic"
    os.environ["LLM_MODEL"] = "claude-2"
    
    config_from_env = LLMConfig.from_env()
    assert config_from_env.provider == LLMProvider.ANTHROPIC
    print(f"  ✅ 环境变量配置: {config_from_env.provider.value}/{config_from_env.model}")
    
    return True


def test_message_handling():
    """测试消息处理"""
    print("\n" + "="*70)
    print("测试 3: 消息处理")
    print("="*70)
    
    # 创建消息
    msg = LLMMessage("user", "Hello, how are you?")
    
    # 转换为字典
    msg_dict = msg.to_dict()
    assert msg_dict["role"] == "user"
    assert msg_dict["content"] == "Hello, how are you?"
    print(f"  ✅ 消息转字典成功")
    
    # 从字典恢复
    msg2 = LLMMessage.from_dict(msg_dict)
    assert msg2.role == msg.role
    assert msg2.content == msg.content
    print(f"  ✅ 字典转消息成功")
    
    return True


def test_openai_client():
    """测试 OpenAI 客户端"""
    print("\n" + "="*70)
    print("测试 4: OpenAI 客户端")
    print("="*70)
    
    config = LLMConfig(provider=LLMProvider.OPENAI, model="gpt-4")
    client = OpenAIClient(config)
    
    messages = [LLMMessage("user", "What is 2+2?")]
    response = client.generate(messages)
    
    assert isinstance(response, LLMResponse)
    print(f"  ✅ OpenAI 客户端响应: {response.provider}")
    print(f"  ✅ 内容长度: {len(response.content)} 字符")
    
    return True


def test_anthropic_client():
    """测试 Anthropic 客户端"""
    print("\n" + "="*70)
    print("测试 5: Anthropic 客户端")
    print("="*70)
    
    config = LLMConfig(provider=LLMProvider.ANTHROPIC, model="claude-2")
    client = AnthropicClient(config)
    
    messages = [LLMMessage("user", "Explain Python")]
    response = client.generate(messages)
    
    assert isinstance(response, LLMResponse)
    print(f"  ✅ Anthropic 客户端响应: {response.provider}")
    
    return True


def test_factory():
    """测试客户端工厂"""
    print("\n" + "="*70)
    print("测试 6: LLM 客户端工厂")
    print("="*70)
    
    # 根据配置创建
    config = LLMConfig(provider=LLMProvider.OLLAMA, model="llama2")
    client = LLMClientFactory.create(config)
    assert client is not None
    print(f"  ✅ 工厂创建 {config.provider.value} 客户端")
    
    # 根据任务类型创建
    code_explainer = LLMClientFactory.create_for_task("code_explanation")
    assert code_explainer is not None
    print(f"  ✅ 任务特定客户端创建成功")
    
    return True


def test_enhanced_service():
    """测试增强的 LLM 服务"""
    print("\n" + "="*70)
    print("测试 7: 增强 LLM 服务")
    print("="*70)
    
    service = EnhancedLLMService()
    
    # 代码解释
    explanation = service.explain_code("def add(a, b): return a + b", "python")
    assert isinstance(explanation, LLMResponse)
    print(f"  ✅ 代码解释: {len(explanation.content)} 字符")
    
    # 代码生成
    generation = service.generate_code("a function that calculates factorial")
    assert isinstance(generation, LLMResponse)
    print(f"  ✅ 代码生成: {len(generation.content)} 字符")
    
    # 代码审查
    review = service.review_code("def foo(): pass", "python")
    assert isinstance(review, LLMResponse)
    print(f"  ✅ 代码审查: {len(review.content)} 字符")
    
    # Bug 修复
    bug_fix = service.fix_bug("def divide(a, b): return a / b", "ZeroDivisionError")
    assert isinstance(bug_fix, LLMResponse)
    print(f"  ✅ Bug 修复: {len(bug_fix.content)} 字符")
    
    # 重构
    refactor = service.refactor_code("def F(x,y):return x+y", "readability")
    assert isinstance(refactor, LLMResponse)
    print(f"  ✅ 代码重构: {len(refactor.content)} 字符")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("模拟 LLM 客户端", test_mock_client),
        ("LLM 配置管理", test_llm_config),
        ("消息处理", test_message_handling),
        ("OpenAI 客户端", test_openai_client),
        ("Anthropic 客户端", test_anthropic_client),
        ("客户端工厂", test_factory),
        ("增强 LLM 服务", test_enhanced_service),
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
    print("📋 LLM 客户端测试总结")
    print("="*80)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有 LLM 客户端测试通过！")
        return True
    else:
        print(f"\n⚠️ {failed}个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
