#!/usr/bin/env python3
"""
Code RAG v13.0 - 主入口点
统一的命令行界面
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def print_banner():
    print("\n" + "=" * 60)
    print("  🧠 Code RAG v13.0 - 智能代码检索系统")
    print("=" * 60)


def show_help():
    print("""
用法: python main.py [命令]

命令:
  search [查询]       - 搜索代码
  index [目录]        - 索引代码库
  analyze [文件]      - 代码智能分析
  nl2code [查询]      - 自然语言查询代码
  test                - 运行测试
  version             - 显示版本
""")


def main():
    print_banner()
    
    if len(sys.argv) < 2:
        show_help()
        return 0
    
    command = sys.argv[1]
    
    if command == "version":
        print("  版本: v13.0")
        print("  发布: 2026-05-16")
        print("  阶段: 整合与完善")
    elif command == "test":
        print("\n  🧪 运行测试...")
        print("  (使用: python -m pytest tests/)")
    elif command in ["help", "--help", "-h"]:
        show_help()
    else:
        print(f"\n  ⚠️ 未知命令: {command}")
        show_help()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
