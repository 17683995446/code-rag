#!/usr/bin/env python3
"""
Code RAG v18.5 - 用户体验优化测试
验证阶段4的12个优化点
"""

import sys
import os
import time
import json
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v18.5 - 用户体验优化测试")
print("="*80)

from code_rag.service_layer.enhanced_ux import (
    EnhancedUX, UXConfig, TextFormatter,
    ProgressTracker, InteractivePrompt, CommandHistory,
    create_ux
)

print("\n📋 测试计划:")
print("  共12个优化点，逐个验证")
print()


def test_1_config_support():
    """测试优化点1: 配置文件支持"""
    print("\n" + "="*60)
    print("测试1: 配置文件支持")
    print("="*60)
    
    config = UXConfig(
        enable_color=True,
        enable_emoji=True,
        compact_mode=False,
        verbosity=2,
        theme="ocean"
    )
    
    ux = EnhancedUX(config)
    
    ux.print("✅ 配置加载成功")
    ux.print(f"  • 主题: {config.theme}")
    ux.print(f"  • 颜色: {config.enable_color}")
    ux.print(f"  • 表情: {config.enable_emoji}")
    ux.print(f"  • 详情级别: {config.verbosity}")
    
    ux.save_config()
    ux.print("  ✅ 配置保存成功")
    
    return True


def test_2_enhanced_color():
    """测试优化点2: 增强的颜色输出"""
    print("\n" + "="*60)
    print("测试2: 增强的颜色输出")
    print("="*60)
    
    ux = create_ux()
    
    ux.print_success("成功消息 - 操作完成")
    ux.print_error("错误消息 - 出现问题")
    ux.print_warning("警告消息 - 需要注意")
    ux.print_info("信息消息 - 普通通知")
    
    return True


def test_3_advanced_progress():
    """测试优化点3: 高级进度条"""
    print("\n" + "="*60)
    print("测试3: 高级进度条")
    print("="*60)
    
    ux = create_ux()
    
    ux.progress_tracker.start("test_index", "索引代码文件", total=100)
    
    for i in range(100):
        time.sleep(0.01)
        if i % 20 == 0:
            ux.progress_tracker.update("test_index", advance=20, extra=f"处理了 {i} 个文件")
    
    elapsed = ux.progress_tracker.finish("test_index", True)
    ux.print(f"  耗时: {elapsed:.2f}s")
    
    return True


def test_4_table_display():
    """测试优化点4: 表格显示"""
    print("\n" + "="*60)
    print("测试4: 表格显示")
    print("="*60)
    
    ux = create_ux()
    
    data = [
        {"文件名": "main.py", "行数": 150, "复杂度": "低"},
        {"文件名": "utils.py", "行数": 80, "复杂度": "低"},
        {"文件名": "api.py", "行数": 250, "复杂度": "中"},
        {"文件名": "database.py", "行数": 400, "复杂度": "高"},
    ]
    
    ux.print_table(data, title="代码文件统计")
    
    return True


def test_5_code_highlight():
    """测试优化点5: 代码高亮显示"""
    print("\n" + "="*60)
    print("测试5: 代码高亮显示")
    print("="*60)
    
    ux = create_ux()
    
    code = """def hello_world():
    print("Hello, World!")
    return True

result = hello_world()
"""
    
    ux.print_code(code, language="python", line_numbers=True)
    
    return True


def test_6_markdown_support():
    """测试优化点6: Markdown支持"""
    print("\n" + "="*60)
    print("测试6: Markdown支持")
    print("="*60)
    
    ux = create_ux()
    
    markdown = """# 快速开始指南

## 安装
\`\`\`bash
pip install code-rag
\`\`\`

## 使用

1. 索引代码
2. 搜索查询
3. 获得答案

> **提示**: 使用 --help 获取更多选项
"""
    
    ux.print_markdown(markdown)
    
    return True


def test_7_tree_display():
    """测试优化点7: 树形结构显示"""
    print("\n" + "="*60)
    print("测试7: 树形结构显示")
    print("="*60)
    
    ux = create_ux()
    
    project_structure = {
        "src": {
            "core": ["main.py", "utils.py"],
            "api": ["routes.py", "models.py"]
        },
        "tests": ["test_core.py", "test_api.py"],
        "docs": ["README.md", "API.md"],
        "config": "config.yaml"
    }
    
    ux.print_tree(project_structure, root_label="项目结构")
    
    return True


def test_8_panel_display():
    """测试优化点8: 面板显示"""
    print("\n" + "="*60)
    print("测试8: 面板显示")
    print("="*60)
    
    ux = create_ux()
    
    content = """欢迎使用 Code RAG！

这是一个智能代码检索系统，支持：
- 关键词搜索
- 语义理解
- 代码解释
- 智能问答

版本: v18.5"""
    
    ux.print_panel(content, title="📚 欢迎界面", border_style="green")
    
    return True


def test_9_stats_display():
    """测试优化点9: 统计信息展示"""
    print("\n" + "="*60)
    print("测试9: 统计信息展示")
    print("="*60)
    
    ux = create_ux()
    
    stats = {
        "索引文件数": 156,
        "代码行数": 123456,
        "搜索次数": 42,
        "平均响应时间": "0.15s",
        "缓存命中率": "85%",
        "最后更新": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    ux.print_stats(stats, title="📊 系统统计")
    
    return True


def test_10_suggestions():
    """测试优化点10: 建议列表"""
    print("\n" + "="*60)
    print("测试10: 建议列表")
    print("="*60)
    
    ux = create_ux()
    
    suggestions = [
        "尝试使用 'search' 命令搜索代码",
        "使用 'index' 命令索引新目录",
        "查看 'help' 获取更多命令选项",
        "考虑启用缓存以提高性能"
    ]
    
    ux.print_suggestions(suggestions)
    
    return True


def test_11_options():
    """测试优化点11: 选项列表"""
    print("\n" + "="*60)
    print("测试11: 选项列表")
    print("="*60)
    
    ux = create_ux()
    
    # 不实际调用输入，只测试显示
    question = "请选择操作模式"
    options = ["快速模式", "详细模式", "交互式模式", "批量模式"]
    
    ux.print_options(question, options)
    
    ux.print_success("选项列表显示成功")
    
    return True


def test_12_session_summary():
    """测试优化点12: 会话摘要"""
    print("\n" + "="*60)
    print("测试12: 会话摘要")
    print("="*60)
    
    ux = create_ux()
    
    ux.command_history.add("search 'def main'")
    ux.command_history.add("index ./src")
    ux.command_history.add("review main.py")
    ux.command_history.add("explain 'class User'")
    
    time.sleep(0.5)
    
    ux.print_session_summary()
    
    return True


def run_all_tests():
    """运行所有12个优化点测试"""
    print("\n" + "="*80)
    print("🚀 开始测试所有12个优化点")
    print("="*80)
    
    tests = [
        ("配置文件支持", test_1_config_support),
        ("增强的颜色输出", test_2_enhanced_color),
        ("高级进度条", test_3_advanced_progress),
        ("表格显示", test_4_table_display),
        ("代码高亮", test_5_code_highlight),
        ("Markdown支持", test_6_markdown_support),
        ("树形结构显示", test_7_tree_display),
        ("面板显示", test_8_panel_display),
        ("统计信息展示", test_9_stats_display),
        ("建议列表", test_10_suggestions),
        ("选项列表", test_11_options),
        ("会话摘要", test_12_session_summary),
    ]
    
    passed = 0
    failed = 0
    failures = []
    
    start_time = time.time()
    
    for i, (name, test_func) in enumerate(tests, 1):
        try:
            print(f"\n{'='*80}")
            print(f"[{i}/{len(tests)}] {name}")
            print('='*80)
            
            result = test_func()
            
            if result:
                passed += 1
                print(f"\n✅ {name} - 通过")
            else:
                failed += 1
                failures.append(name)
                print(f"\n❌ {name} - 失败")
        except Exception as e:
            failed += 1
            failures.append(name)
            print(f"\n❌ {name} - 异常: {e}")
            import traceback
            traceback.print_exc()
    
    elapsed = time.time() - start_time
    
    print("\n" + "="*80)
    print("📋 用户体验优化测试总结")
    print("="*80)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(tests)*100):.1f}%")
    print(f"⏱️ 总耗时: {elapsed:.2f}s")
    
    if failures:
        print("\n❌ 失败的测试:")
        for name in failures:
            print(f"  - {name}")
    
    if failed == 0:
        print("\n🎉 所有12个优化点测试全部通过！")
        return True
    else:
        print(f"\n⚠️ {failed} 个测试失败")
        return False


def test_text_formatter():
    """额外测试：文本格式化器"""
    print("\n" + "="*80)
    print("📝 额外测试：文本格式化器")
    print("="*80)
    
    print("\n截取文本:")
    text = "这是一个非常长的文本，需要被截断显示。"
    result = TextFormatter.truncate(text, 20)
    print(f"  原文: {text}")
    print(f"  结果: {result}")
    
    print("\n格式化字节:")
    print(f"  1024: {TextFormatter.format_bytes(1024)}")
    print(f"  2048000: {TextFormatter.format_bytes(2048000)}")
    
    print("\n格式化时间:")
    print(f"  0.5s: {TextFormatter.format_time(0.5)}")
    print(f"  120s: {TextFormatter.format_time(120)}")
    
    return True


if __name__ == "__main__":
    # 额外测试
    test_text_formatter()
    
    # 主测试
    success = run_all_tests()
    sys.exit(0 if success else 1)
