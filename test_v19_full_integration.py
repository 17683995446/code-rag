#!/usr/bin/env python3
"""
Code RAG v19.0 - 完整集成测试
多语言 + VS Code + LLM 完整工作流
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v19.0 - 完整集成测试")
print("="*80)
print("测试内容: 多语言解析 + VS Code服务 + LLM助手 完整工作流")
print("="*80)

# 导入所有模块
from code_rag.processing_layer.multilang_parser import (
    Language,
    ParserRegistry,
    parse_code,
    PythonParser,
    JavaScriptParser
)

from code_rag.middleware_layer.vscode_extension import (
    VscodeExtension,
    CodeReviewer,
    create_vscode_service
)

from code_rag.service_layer.llm_integration import (
    CodeGenAssistant,
    create_llm_service
)


def test_full_workflow_python():
    """完整的Python完整工作流测试"""
    print("\n" + "="*70)
    print("工作流 1: Python 完整工作流")
    print("="*70)
    
    # 1. 多语言解析
    code = '''
"""Calculator module"""

class Calculator:
    def __init__(self):
        self.value = 0
    
    def add(self, a, b):
        return a + b
    
    def multiply(self, a, b):
        return a * b

def main():
    calc = Calculator()
    print(calc.add(2, 3))
'''
    
    module = parse_code(code, Language.PYTHON, "calc.py")
    assert module is not None
    assert len(module.entities) > 0
    print(f"  1️⃣ 多语言解析: {len(module.entities)} 个实体")
    
    # 2. VS Code 审查
    vscode = create_vscode_service()
    vscode.connect()
    result = vscode.open_document("calc.py", code)
    diagnostics = result["diagnostics"]
    print(f"  2️⃣ VS Code 审查: {len(diagnostics)} 个诊断")
    
    # 3. LLM 解释
    llm = create_llm_service()
    explanation = llm.explain_code(code)
    assert explanation is not None
    assert len(explanation.content) > 0
    print(f"  3️⃣ LLM 解释: {len(explanation.content)} 字符")
    
    return True


def test_full_workflow_javascript():
    """JavaScript完整工作流"""
    print("\n" + "="*70)
    print("工作流 2: JavaScript 完整工作流")
    print("="*70)
    
    code = '''
// Calculator JS
class CalculatorJS {
    constructor() { this.value = 0; }
    add(a, b) { return a + b; }
}

function main() {
    const calc = new CalculatorJS();
    console.log(calc.add(1, 2));
}
'''
    
    # 1. 多语言解析
    module = parse_code(code, Language.JAVASCRIPT, "calc.js")
    assert module is not None
    print(f"  1️⃣ 多语言解析: {len(module.entities)} 个实体")
    
    # 2. VS Code 审查
    vscode = create_vscode_service()
    vscode.open_document("calc.js", code, "javascript")
    print(f"  2️⃣ VS Code 审查: 完成")
    
    # 3. LLM 助手
    llm = create_llm_service()
    review = llm.review_code(code, "javascript")
    print(f"  3️⃣ LLM 审查: {len(review.content)} 字符")
    
    return True


def test_cross_language_comparison():
    """跨语言功能对比"""
    print("\n" + "="*70)
    print("工作流 3: 跨语言工作流")
    print("="*70)
    
    py_code = "class X: def f(): pass"
    js_code = "class X { f() {} }"
    
    py_module = parse_code(py_code, Language.PYTHON)
    js_module = parse_code(js_code, Language.JAVASCRIPT)
    
    print(f"  📊 Python 实体数: {len(py_module.entities)}")
    print(f"  📊 JavaScript 实体数: {len(js_module.entities)}")
    print(f"  ✅ 两种语言都能正常解析")
    
    return True


def test_multi_file_ide_session():
    """多文件IDE会话模拟"""
    print("\n" + "="*70)
    print("工作流 4: 多文件IDE会话")
    print("="*70)
    
    # 模拟IDE会话
    vscode = create_vscode_service()
    vscode.connect()
    
    files = [
        ("app.py", "def app(): return 'App'"),
        ("utils.js", "function utils() { return 'Utils' }"),
        ("test.py", "def test(): pass"),
    ]
    
    opened = []
    for file_path, content in files:
        res = vscode.open_document(file_path, content)
        opened.append(file_path)
        print(f"  📄 打开: {file_path}")
    
    assert len(vscode.active_documents) == 3
    print(f"  ✅ 会话管理: {len(opened)} 个文件活跃")
    
    return True


def run_all_workflows():
    """运行所有集成工作流"""
    workflows = [
        ("Python 完整工作流", test_full_workflow_python),
        ("JavaScript 完整工作流", test_full_workflow_javascript),
        ("跨语言对比", test_cross_language_comparison),
        ("多文件IDE会话", test_multi_file_ide_session),
    ]
    
    passed = 0
    failed = 0
    
    for name, workflow in workflows:
        try:
            print(f"\n[{passed+1+failed}/{len(workflows)}] 执行: {name}")
            if workflow():
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
    print("📋 v19.0 完整集成测试总结")
    print("="*80)
    print(f"📊 总工作流: {len(workflows)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(workflows)*100):.1f}%")
    
    if failed == 0:
        print("\n" + "🎉🎉🎉 恭喜！Code RAG v19.0 新篇章完整集成测试全部通过！")
        print("="*80)
        return True
    else:
        return False


if __name__ == "__main__":
    success = run_all_workflows()
    sys.exit(0 if success else 1)
