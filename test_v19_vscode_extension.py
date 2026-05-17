#!/usr/bin/env python3
"""
Code RAG v19.0 - VS Code扩展集成测试
LSP服务、实时代码审查、问题面板
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v19.0 - VS Code扩展集成测试")
print("="*80)

from code_rag.middleware_layer.vscode_extension import (
    VscodeExtension,
    LSPIntegration,
    CodeReviewer,
    CodeDiagnostic,
    DiagnosticSeverity,
    create_vscode_service
)


def test_code_reviewer():
    """测试实时代码审查器"""
    print("\n" + "="*60)
    print("测试 1: 实时代码审查器")
    print("="*60)
    
    reviewer = CodeReviewer()
    
    long_code = """
def very_long_function():
    print("This is a long line that exceeds 120 characters for testing purposes to see what happens when a line is too long")
    print("Another line")
    return 0
"""
    
    diagnostics = reviewer.review_code(long_code, "python")
    
    print(f"  ✅ 生成 {len(diagnostics)} 个诊断")
    for diag in diagnostics:
        print(f"    - [{diag.severity.value}] Line {diag.line_start}: {diag.message}")
    
    assert len(diagnostics) > 0, "应该生成至少1个诊断"
    return True


def test_lsp_integration():
    """测试LSP集成"""
    print("\n" + "="*60)
    print("测试 2: LSP集成服务")
    print("="*60)
    
    lsp = LSPIntegration()
    
    code = '''
def test():
    x = 1
    y = 2
    return x + y
'''
    
    diagnostics = lsp.on_document_open("test.py", code, "python")
    
    print(f"  ✅ 文档打开时生成 {len(diagnostics)} 个诊断")
    assert diagnostics is not None
    
    # 验证缓存
    cached = lsp.get_diagnostics("test.py")
    assert len(cached) == len(diagnostics)
    print(f"  ✅ 诊断缓存正常工作")
    
    return True


def test_vscode_extension_basic():
    """测试VS Code扩展基本功能"""
    print("\n" + "="*60)
    print("测试 3: VS Code扩展服务")
    print("="*60)
    
    service = create_vscode_service()
    
    # 连接
    connect_result = service.connect()
    assert connect_result["status"] == "connected"
    assert "version" in connect_result
    print(f"  ✅ 连接成功: {connect_result['version']}")
    
    # 打开文档
    code = '''
def hello():
    print("Hello world" * 10)

hello()
'''
    
    open_result = service.open_document("test.py", code, "python")
    
    assert "diagnostics" in open_result
    print(f"  ✅ 文档打开: 返回 {len(open_result['diagnostics'])} 个LSP诊断")
    
    # 更新文档
    update_result = service.update_document("test.py", "def updated(): pass")
    
    assert "diagnostics" in update_result
    print(f"  ✅ 文档更新成功")
    
    return True


def test_diagnostic_formatting():
    """测试诊断格式化为LSP协议"""
    print("\n" + "="*60)
    print("测试 4: LSP诊断格式化")
    print("="*60)
    
    service = VscodeExtension()
    
    diag = CodeDiagnostic(
        message="Test error",
        severity=DiagnosticSeverity.ERROR,
        line_start=5,
        line_end=5
    )
    
    # 通过服务格式化
    result = service._format_diagnostics([diag])
    
    assert len(result) == 1
    formatted = result[0]
    
    assert formatted["source"] == "CodeRAG"
    assert formatted["severity"] == 1  # ERROR
    assert formatted["range"]["start"]["line"] == 4  # line 5 -> index 4
    print(f"  ✅ 格式化正确")
    print(f"    Severity: {formatted['severity']}")
    print(f"    Line: {formatted['range']['start']['line'] + 1}")
    
    return True


def test_quick_fix_actions():
    """测试代码快速修复"""
    print("\n" + "="*60)
    print("测试 5: 代码快速修复建议")
    print("="*60)
    
    service = VscodeExtension()
    
    code = "def foo(): pass"
    service.open_document("test.py", code)
    
    actions = service.get_code_actions("test.py", 1)
    
    assert "actions" in actions
    print(f"  ✅ 获取 {len(actions['actions'])} 个代码操作")
    
    for action in actions["actions"]:
        print(f"    - {action['title']}")
    
    return True


def test_multiple_file_support():
    """测试多文件支持"""
    print("\n" + "="*60)
    print("测试 6: 多文件管理")
    print("="*60)
    
    service = VscodeExtension()
    
    # 打开多个文件
    files = [
        ("app.py", "def app(): pass"),
        ("utils.js", "function utils() {}"),
        ("test.py", "def test(): pass"),
    ]
    
    for file_path, content in files:
        result = service.open_document(file_path, content)
        print(f"  ✅ 打开 {file_path}: {len(result['diagnostics'])}个诊断")
    
    assert len(service.active_documents) == 3
    print(f"  ✅ 同时管理 {len(service.active_documents)} 个活跃文档")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("实时代码审查器", test_code_reviewer),
        ("LSP集成服务", test_lsp_integration),
        ("VS Code扩展服务", test_vscode_extension_basic),
        ("LSP诊断格式化", test_diagnostic_formatting),
        ("代码快速修复", test_quick_fix_actions),
        ("多文件管理", test_multiple_file_support),
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
    print("📋 VS Code扩展集成测试总结")
    print("="*80)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有VS Code扩展测试通过！")
        return True
    else:
        print(f"\n⚠️ {failed}个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
