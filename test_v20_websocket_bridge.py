#!/usr/bin/env python3
"""
Code RAG v20.0 - WebSocket 通信桥测试
"""

import sys
import os
import asyncio
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v20.0 - WebSocket 通信桥测试")
print("="*80)

from code_rag.middleware_layer.websocket_bridge import (
    WebSocketServer,
    CodeRAGWebSocketBridge,
    WSMessage,
    MessageType,
    create_websocket_bridge
)


async def test_websocket_server_basic():
    """测试 WebSocket 服务器基础功能"""
    print("\n" + "="*70)
    print("测试 1: WebSocket 服务器基础")
    print("="*70)
    
    server = WebSocketServer()
    server.start()
    
    # 模拟客户端连接
    client_id = "test_client_1"
    conn = server.simulate_client_connect(client_id)
    
    print(f"  ✅ 客户端 {client_id} 连接成功")
    
    # 测试 Ping/Pong
    ping_msg = WSMessage(type=MessageType.PING.value, id="ping_1")
    pong_response = await server.simulate_message(client_id, ping_msg)
    
    assert pong_response is not None
    assert pong_response.type == MessageType.PONG.value
    print(f"  ✅ Ping/Pong 工作正常")
    
    # 测试连接消息
    connect_msg = WSMessage(
        type=MessageType.CONNECT.value,
        id="connect_1",
        data={"client_name": "Test Client"}
    )
    connect_response = await server.simulate_message(client_id, connect_msg)
    
    assert connect_response is not None
    assert connect_response.type == "connected"
    assert connect_response.data.get("server_version") == "20.0.0"
    print(f"  ✅ 连接握手成功")
    
    server.stop()
    print(f"  ✅ 服务器停止成功")
    
    return True


async def test_code_rag_bridge():
    """测试 Code RAG WebSocket 桥接"""
    print("\n" + "="*70)
    print("测试 2: Code RAG WebSocket 桥接")
    print("="*70)
    
    bridge = create_websocket_bridge()
    bridge.start()
    
    client_id = "test_rag_client"
    bridge.ws_server.simulate_client_connect(client_id)
    
    # 测试文档打开
    open_msg = WSMessage(
        type=MessageType.DOCUMENT_OPEN.value,
        id="doc_open_1",
        data={
            "file_path": "test.py",
            "content": "def add(a, b): return a + b",
            "language": "python"
        }
    )
    
    response = await bridge.ws_server.simulate_message(client_id, open_msg)
    
    assert response is not None
    assert response.type == MessageType.DIAGNOSTICS.value
    print(f"  ✅ 文档打开与诊断获取成功")
    
    # 测试代码解释
    explain_msg = WSMessage(
        type=MessageType.CODE_EXPLANATION.value,
        id="explain_1",
        data={"code": "def add(a, b): return a + b"}
    )
    
    explain_response = await bridge.ws_server.simulate_message(client_id, explain_msg)
    
    assert explain_response is not None
    assert "explanation" in explain_response.data
    assert len(explain_response.data.get("explanation", "")) > 0
    print(f"  ✅ 代码解释请求成功")
    
    bridge.stop()
    return True


async def test_document_change():
    """测试文档变更处理"""
    print("\n" + "="*70)
    print("测试 3: 文档变更处理")
    print("="*70)
    
    bridge = create_websocket_bridge()
    bridge.start()
    
    client_id = "doc_change_client"
    bridge.ws_server.simulate_client_connect(client_id)
    
    # 先打开文档
    open_msg = WSMessage(
        type=MessageType.DOCUMENT_OPEN.value,
        id="open_1",
        data={
            "file_path": "changing.py",
            "content": "def foo(): pass",
            "language": "python"
        }
    )
    await bridge.ws_server.simulate_message(client_id, open_msg)
    
    # 然后变更
    change_msg = WSMessage(
        type=MessageType.DOCUMENT_CHANGE.value,
        id="change_1",
        data={
            "file_path": "changing.py",
            "content": "def foo(): return 42"
        }
    )
    
    change_response = await bridge.ws_server.simulate_message(client_id, change_msg)
    
    assert change_response is not None
    print(f"  ✅ 文档变更处理成功")
    
    bridge.stop()
    return True


async def test_multiple_clients():
    """测试多客户端支持"""
    print("\n" + "="*70)
    print("测试 4: 多客户端支持")
    print("="*70)
    
    server = WebSocketServer()
    server.start()
    
    client_ids = ["client_1", "client_2", "client_3"]
    for cid in client_ids:
        server.simulate_client_connect(cid)
    
    assert len(server.clients) == 3
    print(f"  ✅ 同时管理 {len(server.clients)} 个客户端")
    
    # 测试每个客户端的通信
    for i, cid in enumerate(client_ids):
        ping_msg = WSMessage(type=MessageType.PING.value, id=f"ping_{i}")
        response = await server.simulate_message(cid, ping_msg)
        assert response is not None
    
    print(f"  ✅ 所有客户端通信正常")
    
    server.stop()
    return True


async def run_all_tests():
    """运行所有异步测试"""
    tests = [
        ("WebSocket 服务器基础", test_websocket_server_basic),
        ("Code RAG 桥接", test_code_rag_bridge),
        ("文档变更处理", test_document_change),
        ("多客户端支持", test_multiple_clients),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n[{passed+1+failed}/{len(tests)}] 执行: {name}")
            result = await test_func()
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
    print("📋 WebSocket 通信桥测试总结")
    print("="*80)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有 WebSocket 通信桥测试通过！")
        return True
    return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
