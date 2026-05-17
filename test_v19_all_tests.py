#!/usr/bin/env python3
"""
Code RAG v19.0 - 所有测试一次性运行
"""

import sys
import os

os.environ['PYTHONUNBUFFERED'] = '1'

print("="*80)
print("🧪 Code RAG v19.0 - 完整测试套件运行")
print("="*80)
print(f"工作目录: {os.getcwd()}")
print("="*80)

# 测试文件列表
test_scripts = [
    "test_v19_multilanguage_parser.py",
    "test_v19_vscode_extension.py",
    "test_v19_llm_integration.py",
    "test_v19_full_integration.py",
]

# 运行每个测试
all_passed = True

for idx, script in enumerate(test_scripts, 1):
    print(f"\n{'='*80}")
    print(f"[{idx}/{len(test_scripts)}] 运行: {script}")
    print('='*80)
    
    script_path = os.path.join(os.path.dirname(__file__), script)
    
    try:
        import subprocess
        result = subprocess.run(
            [sys.executable, script_path],
            cwd=os.path.dirname(__file__),
            capture_output=True,
            text=True,
            timeout=120
        )
        
        print(result.stdout)
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"\n✅ {script} - 通过!")
        else:
            print(f"\n❌ {script} - 失败 (退出码: {result.returncode})")
            all_passed = False
            
    except Exception as e:
        print(f"\n❌ {script} - 异常: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False


print("\n" + "="*80)
print("📋 Code RAG v19.0 - 完整测试总结")
print("="*80)

if all_passed:
    print("""
🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉
🎉 恭喜！Code RAG v19.0 新篇章完美交付！ 🎉
🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉🎉

所有 {total} 个测试脚本全部通过！

新增功能:
  1. 多语言解析基础设施 (Python + JS)
  2. VS Code 扩展后端集成 (LSP)
  3. LLM 集成框架 (提示管理 + 代码生成)

战略路线图:
  v20.0: 完整 VS Code 扩展前端
  v21.0: 高级智能功能
  v22.0: 企业级功能
  v23.0: AI 原生体验

感谢您开启 Code RAG 的新篇章！
""".format(total=len(test_scripts)))
else:
    print("⚠️ 部分测试失败，请检查输出")

print("\n" + "="*80)
sys.exit(0 if all_passed else 1)
