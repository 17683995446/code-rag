#!/usr/bin/env python3
"""
Code RAG v20.0 - 完整测试套件运行器
运行所有 v20.0 测试文件
"""

import sys
import os
import subprocess

print("="*80)
print("🧪 Code RAG v20.0 - 完整测试套件")
print("="*80)

os.environ['PYTHONUNBUFFERED'] = '1'

# 所有要运行的测试文件
test_scripts = [
    "test_v19_multilanguage_parser.py",  # 向后兼容性
    "test_v19_vscode_extension.py",      # 向后兼容性
    "test_v19_llm_integration.py",       # 向后兼容性
    "test_v20_websocket_bridge.py",      # 新: WebSocket
    "test_v20_extended_languages.py",    # 新: Java/C++/Go
    "test_v20_complete_integration.py",  # 新: 完整集成
]

total_tests = len(test_scripts)
all_passed = True

# 运行每个测试
results = []

for idx, script in enumerate(test_scripts, 1):
    script_path = os.path.join(os.path.dirname(__file__), script)
    
    print(f"\n{'='*80}")
    print(f"[{idx}/{total_tests}] 运行: {script}")
    print('='*80)
    
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=300
        )
        
        print(result.stdout)
        if result.stderr:
            print("\nSTDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            results.append((script, True, None))
            print(f"\n✅ {script} - 测试通过！")
        else:
            results.append((script, False, f"退出码: {result.returncode}"))
            all_passed = False
            print(f"\n❌ {script} - 测试失败！")
            
    except Exception as e:
        results.append((script, False, str(e)))
        all_passed = False
        print(f"\n❌ {script} - 异常: {e}")
        import traceback
        traceback.print_exc()

# 总结
print("\n" + "="*80)
print("📊 完整测试套件总结")
print("="*80)

passed_count = sum(1 for s, p, e in results if p)
failed_count = total_tests - passed_count

print(f"\n总测试数: {total_tests}")
print(f"✅ 通过: {passed_count}")
print(f"❌ 失败: {failed_count}")
print(f"📈 通过率: {(passed_count/total_tests*100):.1f}%")

if failed_count > 0:
    print("\n失败的测试:")
    for script, passed, error in results:
        if not passed:
            print(f"  - {script}: {error}")
else:
    print("\n" + "🎉" * 20)
    print("🎉 恭喜！Code RAG v20.0 - 所有测试 100% 通过！🎉")
    print("🎉" * 20)
    print("\nCode RAG v20.0 已准备好投入使用！")
    print("\n已实现功能:")
    print("  ✅ WebSocket 实时通信桥")
    print("  ✅ 5种语言支持 (Python/JS/Java/C++/Go)")
    print("  ✅ VS Code 扩展后端")
    print("  ✅ LLM 集成框架")
    print("  ✅ 完整多语言 IDE 基础")

print("\n" + "="*80)

sys.exit(0 if all_passed else 1)
