#!/usr/bin/env python3
"""
Code RAG v16.0 - Web应用测试
测试FastAPI后端
"""

import sys
import json
import time
from pathlib import Path
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def print_header(title):
    print("\n" + "=" * 80)
    print(f"  {title}")
    print("=" * 80)


def test_web_app():
    """测试Web应用"""
    print_header("🧪 Code RAG v16.0 - Web应用测试")
    
    # 导入应用
    from code_rag.web_app import app
    client = TestClient(app)
    
    all_passed = True
    
    # 测试1: 健康检查
    print("\n测试1: 健康检查")
    try:
        response = client.get("/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 状态: {data['status']}")
        else:
            print(f"  ❌ 失败，状态码: {response.status_code}")
            all_passed = False
    except Exception as e:
        print(f"  ❌ 异常: {e}")
        all_passed = False
    
    # 测试2: 系统状态
    print("\n测试2: 系统状态")
    try:
        response = client.get("/")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 名称: {data['name']}")
            print(f"  ✅ 版本: {data['version']}")
            print(f"  ✅ 索引状态: {data['indexed']}")
        else:
            print(f"  ❌ 失败")
            all_passed = False
    except Exception as e:
        print(f"  ❌ 异常: {e}")
        all_passed = False
    
    # 测试3: API文档可访问
    print("\n测试3: API文档")
    try:
        response = client.get("/docs")
        if response.status_code == 200:
            print(f"  ✅ API文档可访问")
        else:
            print(f"  ❌ 文档访问失败")
            all_passed = False
    except Exception as e:
        print(f"  ❌ 异常: {e}")
        all_passed = False
    
    # 测试4: 统计信息
    print("\n测试4: 统计信息")
    try:
        response = client.get("/api/stats")
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 索引状态: {data['indexed']}")
        else:
            print(f"  ❌ 失败")
            all_passed = False
    except Exception as e:
        print(f"  ❌ 异常: {e}")
        all_passed = False
    
    # 测试5: 搜索API (预期失败因为未索引)
    print("\n测试5: 搜索API (未索引状态)")
    try:
        response = client.post("/api/search", json={
            "query": "test",
            "top_k": 10
        })
        if response.status_code == 400:
            print(f"  ✅ 正确返回未索引错误")
        else:
            print(f"  ⚠️ 状态码: {response.status_code}")
    except Exception as e:
        print(f"  ❌ 异常: {e}")
        all_passed = False
    
    # 测试6: NL2Code API
    print("\n测试6: NL2Code API")
    try:
        response = client.post("/api/nl2code", json={
            "query": "create user authentication"
        })
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 意图: {data['intent']}")
            print(f"  ✅ 置信度: {data['confidence']:.2f}")
        else:
            print(f"  ❌ 失败")
            all_passed = False
    except Exception as e:
        print(f"  ❌ 异常: {e}")
        all_passed = False
    
    # 测试7: 代码分析API
    print("\n测试7: 代码分析API")
    try:
        test_code = '''
def authenticate_user(username, password):
    if verify_credentials(username, password):
        return generate_token(username)
    return None
'''
        response = client.post("/api/analyze", json={
            "code": test_code
        })
        if response.status_code == 200:
            data = response.json()
            print(f"  ✅ 检测语言: {data['detected_language']}")
        else:
            print(f"  ❌ 失败")
            all_passed = False
    except Exception as e:
        print(f"  ❌ 异常: {e}")
        all_passed = False
    
    print_header("📊 测试总结")
    if all_passed:
        print("\n  🎉 所有测试通过! v16.0 Web应用就绪!")
        return 0
    else:
        print("\n  ⚠️ 部分测试失败，请检查")
        return 1


if __name__ == "__main__":
    exit_code = test_web_app()
    sys.exit(exit_code)
