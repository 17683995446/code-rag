#!/usr/bin/env python3
"""
Code RAG v13.0 - 项目清理与整理脚本
清理和整理项目文件，为新阶段做准备
"""

import os
import sys
from pathlib import Path
import shutil
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent


def print_header(title):
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)


def archive_old_files():
    """归档旧文件和报告"""
    print_header("📦 步骤 1: 归档旧文件和报告")
    
    archive_dir = PROJECT_ROOT / "archive" / "v12_legacy"
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    # 要归档的文件模式
    report_patterns = [
        "COMPREHENSIVE_*.md",
        "FINAL_*.md",
        "REAL_PROJECT_TEST_REPORT.md",
        "REFACTORING_*.md",
        "SCALABILITY_TEST_REPORT.md",
        "FIXES_IMPROVEMENTS_SUMMARY.md",
        "PROJECT_STRUCTURE_AND_FLOW.md",
        "EVALUATION_REPORT*.md",
        "PHASE_BY_PHASE_*.md",
        "*.json"
    ]
    
    # 查找并归档报告文件
    archived_count = 0
    for pattern in report_patterns:
        for file_path in PROJECT_ROOT.glob(pattern):
            if file_path.is_file() and "archive" not in str(file_path):
                dest = archive_dir / file_path.name
                if not dest.exists():
                    shutil.copy(file_path, dest)
                    archived_count += 1
                    print(f"  已归档: {file_path.name}")
    
    # 归档旧测试脚本
    old_tests_archive = archive_dir / "old_tests"
    old_tests_archive.mkdir(exist_ok=True)
    
    test_files_to_archive = [
        "test_all_projects_comprehensive.py",
        "test_complete_v11.py",
        "test_comprehensive_deep.py",
        "test_fixes_verification.py",
        "test_github_project.py",
        "test_github_real_large.py",
        "test_large_github_project.py",
        "test_real_project_debug.py",
        "test_real_project_practice.py",
        "test_scalability_large.py",
        "test_improvements_verification.py",
        "defect_analysis.py",
        "demo_end_to_end.py",
        "demo_github_project.py",
        "v11_final_evaluation.py",
        "debug_test.py",
        "fix_imports.py",
        "main.py"
    ]
    
    for test_file in test_files_to_archive:
        src_path = PROJECT_ROOT / test_file
        if src_path.exists():
            dest_path = old_tests_archive / test_file
            shutil.copy(src_path, dest_path)
            print(f"  已归档测试: {test_file}")
            archived_count += 1
    
    print(f"\n  ✓ 共归档 {archived_count} 个文件")
    return archived_count


def organize_tests():
    """整理测试文件到 tests 目录"""
    print_header("🧪 步骤 2: 整理测试文件")
    
    tests_dir = PROJECT_ROOT / "tests" / "integration"
    tests_dir.mkdir(parents=True, exist_ok=True)
    
    # 当前应该保留的测试文件
    active_tests = [
        "test_code_intelligence.py",
        "test_semantic_search.py",
        "test_nl2code.py",
        "test_v12_comprehensive.py"
    ]
    
    moved_count = 0
    for test_file in active_tests:
        src_path = PROJECT_ROOT / test_file
        dest_path = tests_dir / test_file
        
        if src_path.exists():
            if not dest_path.exists():
                shutil.move(src_path, dest_path)
                moved_count += 1
                print(f"  已移动: {test_file} -> tests/integration/")
            else:
                print(f"  已存在: {test_file}")
                if src_path.exists():
                    src_path.unlink()
    
    print(f"\n  ✓ 已整理 {moved_count} 个测试文件")
    return moved_count


def create_clean_requirements():
    """创建干净的 requirements.txt"""
    print_header("📋 步骤 3: 更新依赖文件")
    
    requirements = """# Code RAG v13.0 - 核心依赖
# ---------------------------
# 核心搜索与索引
scikit-learn>=1.3.0
numpy>=1.24.0
nltk>=3.8

# 代码处理
tree-sitter>=0.20.0
tree-sitter-languages>=1.10.0

# 数据验证
pydantic>=2.0.0
pydantic-settings>=2.0.0

# 性能优化
orjson>=3.9.0

# 工具库
tqdm>=4.66.0
rich>=13.7.0
click>=8.1.0

# 可选：语义搜索 (需要GPU加速推荐)
# sentence-transformers>=2.5.0
# faiss-cpu>=1.7.0

# 可选：Web界面
# fastapi>=0.110.0
# uvicorn>=0.27.0
# jinja2>=3.1.0

# 开发工具
# pytest>=7.4.0
# pytest-cov>=4.1.0
# ruff>=0.1.0
"""
    
    req_path = PROJECT_ROOT / "requirements.txt"
    req_path.write_text(requirements)
    print(f"  ✓ 已更新: {req_path}")
    
    return True


def create_project_structure_guide():
    """创建项目结构指南"""
    print_header("📁 步骤 4: 创建项目结构指南")
    
    structure_guide = """# Code RAG v13.0 - 项目结构指南

## 核心目录
```
/workspace/code-rag/
├── src/                           # 源代码
│   ├── code_rag/                  # 主要代码库 (v12+ 架构)
│   │   ├── base_layer/            # 基础层
│   │   ├── data_layer/            # 数据层
│   │   ├── processing_layer/      # 处理层
│   │   ├── search_layer/          # 搜索层
│   │   ├── rag_engine/            # RAG引擎
│   │   ├── service_layer/         # 服务层
│   │   ├── middleware_layer/      # 中间件层
│   │   ├── observability_layer/   # 可观测性层
│   │   └── api_layer/             # API层
│   └── api/                       # FastAPI应用
├── tests/                         # 测试
│   ├── unit/                      # 单元测试
│   └── integration/               # 集成测试
├── docs/                          # 文档
├── data/                          # 数据目录
├── visualization/                 # 可视化网站
├── scripts/                       # 工具脚本
└── archive/                       # 归档文件
```

## 已整合的功能
- v11.0: 9层模块化架构
- v12.0: 代码智能理解、NL2Code、语义搜索

## 下一阶段 (v13.0)
- 整合与清理
- 功能完善
- 创新功能
- 用户体验提升
"""
    
    guide_path = PROJECT_ROOT / "PROJECT_GUIDE.md"
    guide_path.write_text(structure_guide)
    print(f"  ✓ 已创建: {guide_path}")
    
    return True


def create_new_main_entrypoint():
    """创建新的主入口文件"""
    print_header("🚀 步骤 5: 创建新入口点")
    
    main_script = """#!/usr/bin/env python3
\"\"\"
Code RAG v13.0 - 主入口点
统一的命令行界面
\"\"\"

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


def print_banner():
    print("\\n" + "=" * 60)
    print("  🧠 Code RAG v13.0 - 智能代码检索系统")
    print("=" * 60)


def show_help():
    print(\"\"\"
用法: python main.py [命令]

命令:
  search [查询]       - 搜索代码
  index [目录]        - 索引代码库
  analyze [文件]      - 代码智能分析
  nl2code [查询]      - 自然语言查询代码
  test                - 运行测试
  version             - 显示版本
\"\"\")


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
        print("\\n  🧪 运行测试...")
        print("  (使用: python -m pytest tests/)")
    elif command in ["help", "--help", "-h"]:
        show_help()
    else:
        print(f"\\n  ⚠️ 未知命令: {command}")
        show_help()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
"""
    
    main_path = PROJECT_ROOT / "main.py"
    main_path.write_text(main_script)
    main_path.chmod(0o755)
    print(f"  ✓ 已创建: {main_path}")
    
    return True


def run_cleanup_summary():
    """运行清理并显示总结"""
    print_header("🧹 Code RAG v13.0 - 项目清理开始")
    print(f"  时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    total_files = 0
    total_files += archive_old_files()
    total_files += organize_tests()
    create_clean_requirements()
    create_project_structure_guide()
    create_new_main_entrypoint()
    
    print_header("✅ 清理完成")
    print(f"\\n  已处理文件总数: {total_files}")
    print(f"  项目已为 v13.0 新阶段做好准备！")
    print(f"\\n  下一步:")
    print(f"    1. 运行测试验证: python main.py test")
    print(f"    2. 查看项目指南: cat PROJECT_GUIDE.md")
    print(f"    3. 继续 v13.0 开发")
    
    return True


if __name__ == "__main__":
    try:
        success = run_cleanup_summary()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\\n❌ 清理失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
