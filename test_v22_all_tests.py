#!/usr/bin/env python3
"""
Code RAG v22.0 - 完整测试运行器
运行所有 v22.0 测试
"""

import sys
import os
import subprocess

print("="*80)
print("🧪 Code RAG v22.0 - 完整测试套件")
print("="*80)

os.environ['PYTHONUNBUFFERED'] = '1'

# 所有要运行的测试文件
test_scripts = [
    # v19.0 测试（向后兼容）
    "test_v19_multilanguage_parser.py",
    "test_v19_vscode_extension.py",
    "test_v19_llm_integration.py",
    
    # v20.0 测试（向后兼容）
    "test_v20_websocket_bridge.py",
    "test_v20_extended_languages.py",
    
    # v21.0 测试（向后兼容）
    "test_v21_llm_clients.py",
    "test_v21_semantic_search.py",
    
    # v22.0 新测试
    "test_v22_team_collaboration.py",
    "test_v22_quality_dashboard.py",
    "test_v22_security_scanner.py",
]

total_tests = len(test_scripts)
all_passed = True
results = []

# 运行每个测试
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
print("📊 Code RAG v22.0 - 完整测试总结")
print("="*80)

passed_count = sum(1 for s, p, e in results if p)
failed_count = total_tests - passed_count

print(f"\n总测试文件数: {total_tests}")
print(f"✅ 通过: {passed_count}")
print(f"❌ 失败: {failed_count}")
print(f"📈 通过率: {(passed_count/total_tests*100):.1f}%")

if failed_count > 0:
    print("\n失败的测试:")
    for script, passed, error in results:
        if not passed:
            print(f"  - {script}: {error}")
else:
    print("\n" + "🎉" * 30)
    print("🎉 恭喜！Code RAG v22.0 - 所有测试 100% 通过！🎉")
    print("🎉" * 30)
    print("\n已实现的企业级功能:")
    print("  ✅ 团队协作索引系统")
    print("  ✅ 代码质量仪表板")
    print("  ✅ 安全审计与扫描")
    print("  ✅ 向后兼容 v19/v20/v21")
    print("  ✅ 多语言支持（Python/JS/Java/C++/Go）")

print("\n" + "="*80)

sys.exit(0 if all_passed else 1)
