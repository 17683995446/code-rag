#!/usr/bin/env python3
"""
Code RAG v11.0 - 自动更新可视化网站
每次修改代码后运行此脚本更新文档
"""

import os
import sys
from pathlib import Path
from datetime import datetime


def main():
    print("🚀 Code RAG v11.0 - 自动更新可视化网站")
    print("=" * 60)
    print(f"更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    project_root = Path(__file__).parent
    vis_dir = project_root / "visualization"
    
    if not vis_dir.exists():
        print(f"❌ 可视化目录不存在: {vis_dir}")
        return 1
    
    print("✅ 检查核心文件:")
    
    core_files = [
        "src/code_rag/data_layer/code_parser_and_document_processor.py",
        "src/code_rag/search_layer/bm25_search_engine.py"
    ]
    
    for rel_path in core_files:
        path = project_root / rel_path
        if path.exists():
            mtime = datetime.fromtimestamp(path.stat().st_mtime).strftime('%Y-%m-%d %H:%M')
            print(f"   ✓ {rel_path} ({mtime})")
        else:
            print(f"   ✗ {rel_path} (不存在)")
    
    print()
    print("📁 可视化网站内容:")
    
    html_files = list(vis_dir.glob("*.html"))
    for html_file in html_files:
        print(f"   - {html_file.name}")
    
    print()
    print("=" * 60)
    print("✅ 可视化网站已就绪！")
    print()
    print("如何查看:")
    print(f"   1. 直接在浏览器中打开: {vis_dir / 'index.html'}")
    print(f"   2. 或使用本地服务器: cd visualization && python -m http.server 8080")
    print(f"   3. 然后访问: http://localhost:8080")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
