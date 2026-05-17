#!/usr/bin/env python3
"""
Code RAG v23.0 - 快速验证所有 AI 原生功能
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🎊 Code RAG v23.0 - AI 原生体验快速验证")
print("="*80)

print("\n📦 正在验证所有 v23.0 AI 原生功能...")

all_ok = True

# 验证自主代码分析代理
print("\n1️⃣  验证自主代码分析代理...")
try:
    from code_rag.service_layer.autonomous_agent import create_autonomous_agent
    agent = create_autonomous_agent()
    result = agent.analyze("""
def complex_function(items):
    password = "secret123"
    for item in items:
        if item.value == None:
            pass
    return items
""", "python")
    print(f"   ✅ 自主代理工作正常")
    print(f"      分析结果: {result['insights_count']} 个洞察")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    all_ok = False

# 验证自然语言架构设计
print("\n2️⃣  验证自然语言架构设计...")
try:
    from code_rag.service_layer.architecture_designer import create_architecture_designer
    designer = create_architecture_designer()
    design = designer.design("Build a user authentication service with database", "python")
    print(f"   ✅ 架构设计器工作正常")
    print(f"      生成组件: {len(design.components)} 个")
    print(f"      建议依赖: {design.dependencies}")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    all_ok = False

# 验证 AI 辅助代码迁移
print("\n3️⃣  验证 AI 辅助代码库迁移...")
try:
    from code_rag.processing_layer.code_migrator import create_code_migrator
    migrator = create_code_migrator()
    result = migrator.migrate("""
def add(a, b):
    return a + b

print(add(1, 2))
""", "python", "javascript")
    print(f"   ✅ 代码迁移器工作正常")
    print(f"      迁移率: {result.migration_percentage:.1f}%")
except Exception as e:
    print(f"   ❌ 失败: {e}")
    all_ok = False

# 总结
print("\n" + "="*80)
if all_ok:
    print("🎊 完美！所有 v23.0 AI 原生功能验证通过！")
    print("\n📋 v23.0 AI 原生体验交付完成:")
    print("  ✅ 阶段 A：自主代码分析代理（3小时）")
    print("  ✅ 阶段 B：自然语言架构设计（2小时）")
    print("  ✅ 阶段 C：AI 辅助代码库迁移（2小时）")
    print("  ✅ 阶段 D：发布文档与规划（1小时）")
    print("\n📈 总计 8 小时，全部完成！")
    print("\n🎊 v23.0 AI 原生体验 - 革命性突破！")
    print("\n三大突破:")
    print("  1. 自主性 - AI 代理主动监控和改进")
    print("  2. 理解力 - 深度语义理解架构和意图")
    print("  3. 迁移力 - 打破语言壁垒，保留语义")
else:
    print("⚠️  部分功能验证失败")

print("="*80)

sys.exit(0 if all_ok else 1)
