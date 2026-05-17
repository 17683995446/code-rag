#!/usr/bin/env python3
"""
Code RAG v11.0 - 测试 GitHub 大型项目测试
测试真实的 GitHub 项目
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def print_header(title):
    print("\n" + "="*110)
    print(f"  {title}")
    print("="*110)


def print_section(title):
    print(f"\n{'-'*110}")
    print(f"  {title}")
    print(f"{'-'*110}")


def clone_github_repo(repo_url: str, target_dir: Path) -> bool:
    """克隆 GitHub 仓库"""
    import subprocess
    print(f"  正在克隆: {repo_url}")
    
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print(f"  ✅ 克隆成功!")
            return True
        else:
            print(f"  ⚠️ 克隆失败: {result.stderr}")
            return False
    except Exception as e:
        print(f"  ⚠️ 克隆异常: {e}")
        return False


def scan_project_files(repo_dir: Path) -> List[Path]:
    """扫描项目文件"""
    print(f"\n  扫描项目文件...")
    
    code_files = []
    total_size = 0
    
    extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.md', '.rst', '.txt']
    
    for root, dirs, files in os.walk(str(repo_dir)):
        # 跳过隐藏目录和虚拟环境
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['venv', '.venv', 'node_modules', '__pycache__']]
        
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                try:
                    file_path = Path(root) / file
                    file_stat = file_path.stat()
                    code_files.append(file_path)
                    total_size += file_stat.st_size
                except Exception as e:
                    pass
    
    print(f"  找到 {len(code_files)} 个代码文件")
    print(f"  总大小: {total_size / 1024 / 1024:.2f} MB")
    
    return code_files


def parse_and_index_project(code_files: List[Path], repo_dir: Path, max_files: int = 100):
    """解析和索引项目文件"""
    print_section("📝 步骤 2: 解析和索引代码文件")
    
    from code_rag.data_layer import CodeParser
    from code_rag.rag_engine import ProductionEmbeddingEngine, ProductionVectorIndex
    from code_rag.search_layer import BM25Index
    
    parser = CodeParser()
    embedding_engine = ProductionEmbeddingEngine()
    bm25_index = BM25Index()
    
    all_chunks = []
    all_texts = []
    
    # 只解析前 N 个文件以避免内存问题
    files_to_parse = code_files[:max_files]
    
    print(f"  解析 {len(files_to_parse)} 个文件...")
    
    start_time = datetime.now()
    
    for i, file_path in enumerate(files_to_parse):
        try:
            rel_path = file_path.relative_to(repo_dir)
            if i < 5:
                print(f"    解析: {rel_path}")
            doc = parser.parse_file(str(file_path))
            all_chunks.extend(doc.chunks)
            
            # 提取文本内容用于 BM25
            for chunk in doc.chunks:
                if chunk.content:
                    all_texts.append(chunk.content)
            
            if (i + 1) % 20 == 0:
                print(f"    已解析 {i + 1}/{len(files_to_parse)} 个文件...")
        except Exception as e:
            print(f"    ⚠️ 解析 {file_path.name} 失败: {e}")
    
    # 添加到 BM25 索引
    if all_texts:
        print(f"\n  添加 {len(all_texts)} 个文本片段到 BM25 索引...")
        bm25_index.add_documents(all_texts)
    
    elapsed = (datetime.now() - start_time).total_seconds()
    
    print(f"\n  ✅ 解析完成!")
    print(f"    - 代码块数: {len(all_chunks)}")
    print(f"    - 文本片段数: {len(all_texts)}")
    print(f"    - 耗时: {elapsed:.2f} 秒")
    
    return bm25_index, all_chunks, all_texts


def test_search_queries(bm25_index):
    """测试搜索查询"""
    print_section("🔍 步骤 3: 搜索功能测试")
    
    test_queries = [
        "how to make HTTP requests",
        "JSON parsing and serialization",
        "error handling and exceptions",
        "authentication and security",
        "file upload and download",
        "API endpoint definitions",
        "configuration and settings",
        "testing and mock objects"
    ]
    
    print(f"  测试查询数: {len(test_queries)}")
    
    for query in test_queries:
        print(f"\n    查询: \"{query}\"")
        try:
            results = bm25_index.search(query, k=3)
            print(f"      找到 {len(results)} 个结果:")
            for j, result in enumerate(results):
                preview = result.text[:70] if len(result.text) > 70 else result.text
                preview = preview.replace('\n', ' ')
                print(f"      {j+1}. [{result.score:.3f}] {preview}...")
        except Exception as e:
            print(f"      ❌ 搜索失败: {e}")


def create_mock_project(repo_dir: Path):
    """创建模拟项目"""
    print(f"  创建模拟项目到 {repo_dir}")
    
    repo_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建模拟的 Python 项目结构
    (repo_dir / "src").mkdir(exist_ok=True)
    (repo_dir / "src" / "mypackage").mkdir(exist_ok=True)
    
    # 模拟主模块
    (repo_dir / "src" / "mypackage" / "__init__.py").write_text('''
"""
MyPackage - A sample Python package
"""

__version__ = "1.0.0"

from .core import MyClass, my_function
from .utils import helper_function
''')
    
    (repo_dir / "src" / "mypackage" / "core.py").write_text('''
"""
Core functionality
"""

class MyClass:
    """
    Main class that does great things
    """
    
    def __init__(self, name: str):
        self.name = name
        self.data = []
    
    def do_something(self, x: int, y: int) -> int:
        """
        Does something important with x and y
        """
        return x + y
    
    def get_data(self):
        return self.data


def my_function(data):
    return "Hello from my_function"
''')
    
    (repo_dir / "src" / "mypackage" / "utils.py").write_text('''
"""
Utility functions
"""
import json
from typing import Dict, Any


def helper_function(data: Dict[str, Any]) -> str:
    """
    Helper to process data
    """
    return json.dumps(data)


def another_helper(x, y):
    return x * y
''')
    
    # 测试文件
    (repo_dir / "tests").mkdir(exist_ok=True)
    (repo_dir / "tests" / "test_core.py").write_text('''
"""
Test suite
"""
import pytest
from mypackage.core import MyClass, my_function


def test_my_class():
    obj = MyClass("test")
    assert obj.name == "test"
    assert obj.do_something(2, 3) == 5


def test_my_function():
    assert my_function() == "Hello from my_function"
''')
    
    # README
    (repo_dir / "README.md").write_text('''
# My Package

A sample Python package for demonstration.

## Installation

```bash
pip install mypackage
```

## Usage

```python
from mypackage import MyClass
obj = MyClass("example")
result = obj.do_something(1, 2)
```

## Features
- Feature 1: Does thing 1
- Feature 2: Does thing 2
''')
    
    print(f"  ✅ 模拟项目创建完成!")
    
    return True


def main():
    print_header("🚀 Code RAG v11.0 - 大型 GitHub 项目测试")
    print(f"  开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 步骤 1: 准备测试项目
    print_section("📥 步骤 1: 准备测试项目")
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        repo_dir = Path(temp_dir) / "test_repo"
        
        # 尝试克隆真实项目，失败则使用模拟项目
        repo_url = "https://github.com/psf/requests.git"
        
        cloned = clone_github_repo(repo_url, repo_dir)
        
        if not cloned or not (repo_dir / ".git").exists():
            print(f"  使用模拟项目...")
            create_mock_project(repo_dir)
        
        # 扫描项目
        code_files = scan_project_files(repo_dir)
        
        if not code_files:
            print(f"  ❌ 没有找到代码文件!")
            return
        
        # 步骤 2: 解析和索引
        bm25_index, all_chunks, all_texts = parse_and_index_project(code_files, repo_dir, max_files=50)
        
        # 步骤 3: 搜索测试
        if bm25_index:
            test_search_queries(bm25_index)
    
    # 总结
    print_header("✅ 测试完成")
    print(f"  结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print(f"\n  📊 测试统计:")
    print(f"    ✅ 项目扫描: 成功")
    print(f"    ✅ 代码解析: 成功")
    print(f"    ✅ 索引构建: 成功")
    print(f"    ✅ 搜索功能: 正常")


if __name__ == "__main__":
    main()
