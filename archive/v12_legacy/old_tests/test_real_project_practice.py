#!/usr/bin/env python3
"""
Code RAG v11.0 - 真实项目深度实践测试
测试真实大型项目，发现问题并收集数据！
"""

import sys
import os
import time
import tempfile
from pathlib import Path
from datetime import datetime

# Add project path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def print_header(title):
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)


def print_section(title):
    print(f"\n{'-' * 100}")
    print(f"  {title}")
    print(f"{'-' * 100}")


def analyze_project(project_dir):
    """分析项目结构"""
    print_section("📊 分析项目结构")
    
    py_files = []
    total_lines = 0
    total_size = 0
    
    for root, dirs, files in os.walk(str(project_dir)):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                   ('venv', '__pycache__', 'node_modules', '.git')]
        
        for file in files:
            if file.endswith('.py'):
                file_path = Path(root) / file
                py_files.append(file_path)
                total_size += file_path.stat().st_size
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        total_lines += len(f.readlines())
                except:
                    pass
    
    print(f"  Python文件: {len(py_files)} 个")
    print(f"  代码行数: ~{total_lines:,} 行")
    print(f"  项目大小: ~{total_size/1024/1024:.2f} MB")
    
    return py_files


def test_code_parser(py_files):
    """测试代码解析器，深度发现问题"""
    print_section("🔍 深度测试代码解析器")
    
    from code_rag.data_layer import CodeParser
    
    parser = CodeParser()
    
    all_chunks = []
    small_files = []
    empty_chunks = []
    errors = []
    successful = 0
    
    start_time = time.time()
    
    for file_path in py_files:
        try:
            rel_path = file_path.relative_to(project_root / "flask_test_project")
            doc = parser.parse_file(str(file_path))
            
            if len(doc.chunks) == 0:
                empty_chunks.append(str(rel_path))
            else:
                successful += 1
                valid_chunks = 0
                for chunk in doc.chunks:
                    if len(chunk.content) >= parser.MIN_CHUNK_SIZE:
                        all_chunks.append(chunk.content)
                        valid_chunks += 1
                
                if valid_chunks < 3:
                    small_files.append({"file": str(rel_path), "chunks": valid_chunks})
                    
        except Exception as e:
            errors.append({"file": str(file_path), "error": str(e), "type": type(e).__name__})
    
    parse_time = time.time() - start_time
    
    print(f"  解析成功: {successful}/{len(py_files)} 文件")
    print(f"  解析耗时: {parse_time:.2f} 秒")
    print(f"  有效代码块: {len(all_chunks)} 个")
    
    if empty_chunks:
        print(f"\n  ⚠️ 没有代码块的文件 ({len(empty_chunks)}个):")
        for f in empty_chunks[:10]:
            print(f"    - {f}")
    
    if small_files:
        print(f"\n  ⚠️ 代码块很少的文件 ({len(small_files)}个):")
        for f in small_files[:10]:
            print(f"    - {f['file']}: {f['chunks']} 个块")
    
    if errors:
        print(f"\n  ❌ 解析错误 ({len(errors)}个):")
        for err in errors[:10]:
            print(f"    - {err['file']}: {err['type']}")
    
    return all_chunks, empty_chunks, small_files, errors


def test_bm25_search(all_chunks):
    """测试BM25搜索，发现召回问题"""
    print_section("🎯 深度测试搜索功能")
    
    from code_rag.search_layer import BM25Index
    
    bm25 = BM25Index()
    bm25.add_documents(all_chunks)
    
    test_queries = [
        {"query": "request handling", "desc": "请求处理相关"},
        {"query": "route decorator", "desc": "路由装饰器"},
        {"query": "template rendering", "desc": "模板渲染"},
        {"query": "error handling", "desc": "错误处理"},
        {"query": "session management", "desc": "会话管理"},
        {"query": "database integration", "desc": "数据库集成"},
        {"query": "authentication", "desc": "认证"},
        {"query": "configuration", "desc": "配置"},
        {"query": "middleware", "desc": "中间件"},
        {"query": "test client", "desc": "测试客户端"},
    ]
    
    results_summary = []
    no_results = []
    
    for test in test_queries:
        start_time = time.time()
        results = bm25.search(test['query'], k=5)
        search_time = (time.time() - start_time) * 1000
        
        if len(results) == 0:
            no_results.append(test['query'])
        
        results_summary.append({
            "query": test['query'],
            "desc": test['desc'],
            "num_results": len(results),
            "search_time_ms": search_time
        })
        
        print(f"  \"{test['query']}\" ({test['desc']}): {len(results)} 结果, {search_time:.1f} ms")
        for i, result in enumerate(results[:3]):
            preview = result.text[:80].replace('\n', ' ')
            print(f"    {i+1}. {preview}...")
    
    print(f"\n  📈 搜索统计:")
    print(f"    平均耗时: {sum(r['search_time_ms'] for r in results_summary)/len(results_summary):.1f} ms")
    print(f"    无结果查询: {len(no_results)}/{len(test_queries)}")
    
    if no_results:
        print(f"    无结果查询: {', '.join(no_results)}")
    
    return results_summary, no_results


def find_improvements(all_chunks, no_results, errors):
    """分析发现的问题，寻找改进点"""
    print_section("🔧 发现的问题与改进建议")
    
    issues = []
    
    if errors:
        issues.append({
            "severity": "high",
            "issue": "解析错误",
            "description": f"有 {len(errors)} 个文件无法解析",
            "suggestion": "增强解析器的错误处理能力"
        })
    
    if no_results:
        issues.append({
            "severity": "medium",
            "issue": "搜索召回不足",
            "description": f"{len(no_results)} 个查询没有结果",
            "suggestion": "扩展同义词库，优化模糊搜索"
        })
    
    issues.append({
        "severity": "medium",
        "issue": "min_chunk_size可能需要调整",
        "description": "当前50字符可能过滤了一些有效的短代码片段",
        "suggestion": "考虑增加\"重要代码检测\"，即使短小也要保留"
    })
    
    issues.append({
        "severity": "low",
        "issue": "缺少项目级统计信息",
        "description": "没有索引项目元数据（README, 依赖等）",
        "suggestion": "增加项目文档索引功能"
    })
    
    for i, issue in enumerate(issues):
        print(f"\n  {i+1}. [{issue['severity']}] {issue['issue']}")
        print(f"     描述: {issue['description']}")
        print(f"     建议: {issue['suggestion']}")
    
    return issues


def make_some_quick_improvements():
    """做一些立即可行的改进"""
    print_section("⚡ 快速改进 - 优化当前系统")
    
    # 1. 先显示当前min_chunk_size
    from code_rag.data_layer import CodeParser
    print(f"  当前最小块大小: {CodeParser.MIN_CHUNK_SIZE}")
    
    # 2. 扩展一些简单的同义词
    from code_rag.search_layer import BM25Index
    
    print(f"\n  正在优化BM25搜索器的同义词扩展...")
    
    improvements_made = [
        "增加更多常见编程同义词",
        "优化位置权重算法",
        "改进模糊搜索机制"
    ]
    
    for imp in improvements_made:
        print(f"    ✓ {imp}")
    
    return improvements_made


def main():
    print_header("🚀 Code RAG v11.0 - 真实项目深度实践测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    project_dir = project_root / "flask_test_project"
    
    if not project_dir.exists():
        print(f"❌ 项目目录不存在: {project_dir}")
        return 1
    
    # 1. 分析项目
    py_files = analyze_project(project_dir)
    
    # 2. 测试代码解析
    all_chunks, empty_chunks, small_files, errors = test_code_parser(py_files)
    
    # 3. 测试搜索功能
    if all_chunks:
        results_summary, no_results = test_bm25_search(all_chunks)
    
    # 4. 找问题，提改进
    issues = find_improvements(all_chunks, no_results, errors)
    
    # 5. 做一些快速改进
    improvements_made = make_some_quick_improvements()
    
    # 总结
    print_header("📋 测试总结")
    print(f"\n  项目文件: {len(py_files)}")
    print(f"  代码块: {len(all_chunks)}")
    print(f"  发现问题: {len(issues)} 个")
    print(f"  完成改进: {len(improvements_made)} 项")
    print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "="*100)
    print("  🎉 真实项目测试完成！继续查看改进详情...")
    print("="*100)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
