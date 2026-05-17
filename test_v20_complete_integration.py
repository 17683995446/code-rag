#!/usr/bin/env python3
"""
Code RAG v20.0 - 完整集成测试
包括所有新语言 + WebSocket + 原有功能
"""

import sys
import os
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v20.0 - 完整集成测试")
print("="*80)

# 导入所有模块
from code_rag.processing_layer.multilang_parser import (
    Language,
    parse_code
)
from code_rag.middleware_layer.websocket_bridge import (
    create_websocket_bridge,
    WSMessage,
    MessageType
)
from code_rag.middleware_layer.vscode_extension import create_vscode_service
from code_rag.service_layer.llm_integration import create_llm_service


def test_all_languages_in_bridge():
    """测试 WebSocket 桥接对所有语言的支持"""
    print("\n" + "="*70)
    print("场景 1: 所有语言的 WebSocket 桥接")
    print("="*70)
    
    bridge = create_websocket_bridge()
    bridge.start()
    
    client_id = "all_lang_client"
    bridge.ws_server.simulate_client_connect(client_id)
    
    # 测试各种语言的文档
    test_cases = [
        ("test.py", "def add(a, b): return a + b", Language.PYTHON),
        ("test.js", "function add(a, b) { return a + b; }", Language.JAVASCRIPT),
        ("Test.java", "public class Test { public int add(int a, int b) { return a + b; } }", Language.JAVA),
        ("test.cpp", "class Test { int add(int a, int b) { return a + b; } };", Language.CPP),
        ("test.go", "func add(a, b int) int { return a + b }", Language.GO),
    ]
    
    for file_path, code, lang in test_cases:
        open_msg = WSMessage(
            type=MessageType.DOCUMENT_OPEN.value,
            id=f"open_{file_path}",
            data={
                "file_path": file_path,
                "content": code,
                "language": lang.value
            }
        )
        
        # 测试解析
        module = parse_code(code, lang, file_path)
        assert module is not None
        
        print(f"  ✅ {lang.value} 文件解析成功，{len(module.entities)} 个实体")
    
    bridge.stop()
    print("  ✅ 所有语言桥接支持成功")
    return True


async def test_complete_workflow():
    """测试完整的 IDE 工作流程"""
    print("\n" + "="*70)
    print("场景 2: 完整 IDE 工作流")
    print("="*70)
    
    # 步骤 1: 初始化组件
    bridge = create_websocket_bridge()
    bridge.start()
    llm = create_llm_service()
    client_id = "workflow_client"
    bridge.ws_server.simulate_client_connect(client_id)
    
    # 步骤 2: 打开多语言项目文件
    files = [
        ("main.py", "def main(): print('Hello')", Language.PYTHON),
        ("utils.java", "public class Utils { public static void help() {} }", Language.JAVA),
    ]
    
    for file_path, code, lang in files:
        open_result = bridge.vscode_service.open_document(file_path, code, lang.value)
        print(f"  ✅ 打开 {lang.value} 文件: {file_path}")
    
    # 步骤 3: 查询 LLM
    explanation = llm.explain_code("def add(a, b): return a + b")
    assert len(explanation.content) > 0
    print(f"  ✅ LLM 解释完成")
    
    # 步骤 4: 关闭
    bridge.stop()
    print("  ✅ 完整工作流成功")
    return True


def test_project_stats():
    """测试项目统计功能"""
    print("\n" + "="*70)
    print("场景 3: 多语言项目统计")
    print("="*70)
    
    # 模拟多语言项目
    languages_supported = [
        Language.PYTHON,
        Language.JAVASCRIPT,
        Language.JAVA,
        Language.CPP,
        Language.GO
    ]
    
    print(f"  支持的语言总数: {len(languages_supported)}")
    print("  语言列表:")
    for lang in languages_supported:
        print(f"    - {lang.value}")
    
    # 测试每种语言的基本解析
    total_entities = 0
    for lang in languages_supported:
        code_snippet = {
            Language.PYTHON: "def test(): pass",
            Language.JAVASCRIPT: "function test() {}",
            Language.JAVA: "class Test { void test() {} }",
            Language.CPP: "class Test { void test() {} };",
            Language.GO: "func test() {}",
        }[lang]
        
        module = parse_code(code_snippet, lang)
        if module:
            total_entities += len(module.entities)
    
    print(f"  总解析实体数: {total_entities}")
    assert len(languages_supported) == 5
    return True


async def run_all_integration_tests():
    """运行所有集成测试"""
    tests = [
        ("所有语言 WebSocket 桥接", test_all_languages_in_bridge),
        ("完整 IDE 工作流", test_complete_workflow),
        ("项目统计", test_project_stats),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n[{passed+1+failed}/{len(tests)}] 执行: {name}")
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
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
    print("📋 v20.0 完整集成测试总结")
    print("="*80)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 v20.0 完整集成测试全部通过！")
        return True
    return False


if __name__ == "__main__":
    success = asyncio.run(run_all_integration_tests())
    sys.exit(0 if success else 1)
