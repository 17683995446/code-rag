#!/usr/bin/env python3
"""
Code RAG v21.0 - 快速验证脚本
验证所有核心功能
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v21.0 - 快速验证")
print("="*80)

all_passed = True

# 1. 验证 LLM 客户端
print("\n📦 验证 LLM 客户端...")
try:
    from code_rag.service_layer.llm_clients import create_llm_service
    
    service = create_llm_service()
    response = service.explain_code("def test(): pass")
    assert response is not None
    print("  ✅ LLM 客户端工作正常")
except Exception as e:
    print(f"  ❌ LLM 客户端失败: {e}")
    all_passed = False

# 2. 验证语义搜索
print("\n📦 验证语义搜索...")
try:
    from code_rag.processing_layer.semantic_search import create_search_engine
    
    engine = create_search_engine()
    engine.index_code("test", "def test(): pass", "python")
    results = engine.search_by_keyword("test")
    assert len(results) > 0
    print("  ✅ 语义搜索工作正常")
except Exception as e:
    print(f"  ❌ 语义搜索失败: {e}")
    all_passed = False

# 3. 验证多语言解析器
print("\n📦 验证多语言解析器...")
try:
    from code_rag.processing_layer.multilang_parser import parse_code, Language
    
    py_module = parse_code("def test(): pass", Language.PYTHON)
    js_module = parse_code("function test() {}", Language.JAVASCRIPT)
    assert py_module is not None
    assert js_module is not None
    print("  ✅ 多语言解析器工作正常")
except Exception as e:
    print(f"  ❌ 多语言解析器失败: {e}")
    all_passed = False

# 4. 验证 WebSocket 桥接
print("\n📦 验证 WebSocket 桥接...")
try:
    from code_rag.middleware_layer.websocket_bridge import create_websocket_bridge
    
    bridge = create_websocket_bridge()
    bridge.start()
    print("  ✅ WebSocket 桥接工作正常")
    bridge.stop()
except Exception as e:
    print(f"  ❌ WebSocket 桥接失败: {e}")
    all_passed = False

# 5. 验证 LLM 集成
print("\n📦 验证 LLM 集成...")
try:
    from code_rag.service_layer.llm_integration import create_llm_service
    
    assistant = create_llm_service()
    explanation = assistant.explain_code("def add(a, b): return a + b")
    assert explanation is not None
    print("  ✅ LLM 集成工作正常")
except Exception as e:
    print(f"  ❌ LLM 集成失败: {e}")
    all_passed = False

# 总结
print("\n" + "="*80)
if all_passed:
    print("🎉 Code RAG v21.0 - 所有核心功能验证通过！")
    print("\n已实现的智能功能:")
    print("  ✅ 真实 LLM API 集成")
    print("  ✅ 语义搜索增强")
    print("  ✅ 多语言解析")
    print("  ✅ WebSocket 通信")
    print("  ✅ LLM 代码助手")
else:
    print("⚠️ 部分功能验证失败，请检查输出")
print("="*80)

sys.exit(0 if all_passed else 1)
