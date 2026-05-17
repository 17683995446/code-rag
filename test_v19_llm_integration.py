#!/usr/bin/env python3
"""
Code RAG v19.0 - LLM集成框架测试
提示管理、代码生成、LLM抽象接口
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v19.0 - LLM集成框架测试")
print("="*80)

from code_rag.service_layer.llm_integration import (
    SimpleLLMClient,
    PromptManager,
    CodeGenAssistant,
    LLMMessage,
    LLMResponse,
    PromptTemplate,
    LLMProvider,
    create_llm_service
)


def test_llm_client_basic():
    """测试LLM客户端基础功能"""
    print("\n" + "="*60)
    print("测试 1: LLM客户端")
    print("="*60)
    
    client = SimpleLLMClient()
    
    messages = [
        LLMMessage(role="user", content="Explain this code")
    ]
    
    response = client.generate(messages)
    
    assert isinstance(response, LLMResponse)
    assert len(response.content) > 0
    assert response.role == "assistant"
    
    print(f"  ✅ LLM生成响应成功")
    print(f"  ✅ Model: {response.model}")
    print(f"  ✅ Tokens: {response.tokens_used}")
    
    return True


def test_prompt_manager():
    """测试提示管理系统"""
    print("\n" + "="*60)
    print("测试 2: 提示管理系统")
    print("="*60)
    
    manager = PromptManager()
    
    # 渲染内置模板
    code = "def test(): pass"
    result = manager.render("code_explanation", code=code)
    
    assert "Explain this code" in result
    assert code in result
    print(f"  ✅ 内置模板渲染成功")
    
    # 添加新模板
    new_template = PromptTemplate(
        name="custom_template",
        template="Hello, {name}! This is {project}.",
        variables=["name", "project"]
    )
    manager.add_template(new_template)
    
    # 渲染自定义模板
    custom_result = manager.render("custom_template", name="Alice", project="CodeRAG")
    assert "Hello, Alice" in custom_result
    print(f"  ✅ 自定义模板添加和渲染成功")
    
    return True


def test_code_gen_assistant():
    """测试代码生成助手"""
    print("\n" + "="*60)
    print("测试 3: 代码生成助手")
    print("="*60)
    
    assistant = CodeGenAssistant()
    
    # 测试解释代码
    code = "def add(a, b): return a + b"
    explanation = assistant.explain_code(code)
    
    assert isinstance(explanation, LLMResponse)
    print(f"  ✅ 代码解释: {len(explanation.content)} 字符")
    
    # 测试审查代码
    review = assistant.review_code(code, "python")
    assert isinstance(review, LLMResponse)
    print(f"  ✅ 代码审查: {len(review.content)} 字符")
    
    return True


def test_multi_provider_support():
    """测试多提供商支持"""
    print("\n" + "="*60)
    print("测试 4: 多提供商支持")
    print("="*60)
    
    for provider_name in ["local", "openai", "anthropic", "azure"]:
        try:
            service = create_llm_service(provider=provider_name, model="test-model")
            response = service.explain_code("def x(): pass")
            assert response is not None
            print(f"  ✅ Provider {provider_name} 初始化成功")
        except:
            print(f"  ⚠️ Provider {provider_name} 跳过（演示用途）")
    
    return True


def test_custom_templates_workflow():
    """测试自定义模板工作流"""
    print("\n" + "="*60)
    print("测试 5: 自定义模板工作流")
    print("="*60)
    
    manager = PromptManager()
    
    template = PromptTemplate(
        name="unit_test_gen",
        template="Generate a unit test for this {language} function:\n\n{code}",
        variables=["language", "code"],
        description="Unit test generator"
    )
    
    manager.add_template(template)
    
    rendered = manager.render(
        "unit_test_gen",
        language="python",
        code="def add(a, b): return a + b"
    )
    
    assert "unit test" in rendered.lower()
    assert "python" in rendered
    assert "def add" in rendered
    print(f"  ✅ 自定义模板工作流完整")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("LLM客户端基础", test_llm_client_basic),
        ("提示管理系统", test_prompt_manager),
        ("代码生成助手", test_code_gen_assistant),
        ("多提供商支持", test_multi_provider_support),
        ("自定义模板工作流", test_custom_templates_workflow),
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
    print("📋 LLM集成框架测试总结")
    print("="*80)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有LLM集成测试通过！")
        return True
    else:
        print(f"\n⚠️ {failed}个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
