#!/usr/bin/env python3
"""
Code RAG v11.0 - 多项目综合测试
测试所有克隆的大型真实项目，发现系统问题！
"""

import sys
import time
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


def test_single_project(project_name, project_dir):
    """测试单个项目"""
    print_section(f"🔍 测试项目: {project_name}")
    
    if not project_dir.exists():
        print(f"  ❌ 项目不存在: {project_dir}")
        return None
    
    # 1. 分析项目结构
    print(f"  正在分析项目结构...")
    py_files = []
    total_lines = 0
    
    # 使用rglob递归查找所有Python文件
    py_files = list(project_dir.rglob("*.py"))
    
    # 过滤掉测试目录和特殊目录（只匹配目录名，不匹配整个路径）
    filtered_py_files = []
    for f in py_files:
        # 获取文件所在的所有目录名
        parts = f.parts
        # 检查是否在测试或缓存目录中
        skip = False
        for part in parts:
            if part in ['__pycache__', '.git', 'venv', 'node_modules', 
                       '.venv', 'env', 'test', 'tests', 'Test', 'Tests']:
                skip = True
                break
        if not skip:
            filtered_py_files.append(f)
    
    py_files = filtered_py_files
    
    for file_path in py_files:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                total_lines += len(f.readlines())
        except:
            pass
    
    print(f"    Python文件: {len(py_files)} 个")
    print(f"    代码行数: ~{total_lines:,} 行")
    
    if len(py_files) == 0:
        print(f"    ⚠️ 没有Python文件，跳过")
        return None
    
    # 2. 测试代码解析
    print(f"  正在解析代码...")
    from code_rag.data_layer import CodeParser
    parser = CodeParser()
    
    all_chunks = []
    parse_errors = []
    empty_files = []
    very_small_chunks = []
    
    start_time = time.time()
    files_tested = min(100, len(py_files))  # 限制测试文件数
    
    for i, file_path in enumerate(py_files[:files_tested]):
        try:
            doc = parser.parse_file(str(file_path))
            
            if len(doc.chunks) == 0:
                empty_files.append(file_path.name)
            
            valid_count = 0
            for chunk in doc.chunks:
                if len(chunk.content) >= parser.MIN_CHUNK_SIZE:
                    all_chunks.append(chunk.content)
                    valid_count += 1
                else:
                    very_small_chunks.append({
                        "file": file_path.name,
                        "size": len(chunk.content),
                        "type": chunk.chunk_type
                    })
            
        except Exception as e:
            parse_errors.append({
                "file": file_path.name,
                "error": type(e).__name__
            })
    
    parse_time = time.time() - start_time
    
    print(f"    解析: {files_tested}/{len(py_files)} 文件")
    print(f"    耗时: {parse_time:.2f}s")
    print(f"    代码块: {len(all_chunks)} 个")
    
    if parse_errors:
        print(f"    ⚠️ 解析错误: {len(parse_errors)} 个")
        for err in parse_errors[:3]:
            print(f"      - {err['file']}: {err['error']}")
    
    if empty_files:
        print(f"    ⚠️ 无代码块文件: {len(empty_files)} 个")
    
    # 3. 测试搜索
    if len(all_chunks) < 10:
        print(f"    ⚠️ 代码块太少，跳过搜索测试")
        return None
    
    print(f"  正在测试搜索...")
    from code_rag.search_layer import BM25Index
    bm25 = BM25Index()
    
    # 根据项目类型选择测试查询
    if 'flask' in project_name.lower():
        queries = ["route decorator", "template", "request handling", "app config", "session"]
    elif 'django' in project_name.lower():
        queries = ["model", "view", "template", "orm", "migrate"]
    elif 'ansible' in project_name.lower():
        queries = ["playbook", "task", "module", "inventory", "handler"]
    elif 'vscode' in project_name.lower():
        queries = ["extension", "editor", "command", "workspace", "debug"]
    else:
        queries = ["function", "class", "import", "test", "config"]
    
    start_time = time.time()
    bm25.add_documents(all_chunks[:500])  # 限制文档数
    index_time = time.time() - start_time
    
    print(f"    索引: {len(all_chunks[:500])} 个文档")
    print(f"    耗时: {index_time:.2f}s")
    
    # 测试查询
    search_results = []
    no_results = []
    
    for query in queries:
        start_time = time.time()
        results = bm25.search(query, k=5)
        search_time = (time.time() - start_time) * 1000
        
        search_results.append({
            "query": query,
            "results": len(results),
            "time_ms": search_time
        })
        
        if len(results) == 0:
            no_results.append(query)
        
        print(f"    '{query}': {len(results)} 结果, {search_time:.1f}ms")
    
    # 4. 总结
    success_rate = len(search_results) > 0 and (
        sum(r['results'] for r in search_results) / (len(search_results) * 5) * 100
    )
    
    avg_search_time = sum(r['time_ms'] for r in search_results) / len(search_results) if search_results else 0
    
    print(f"\n  📊 测试结果:")
    print(f"    文件解析成功率: {((files_tested - len(parse_errors)) / files_tested * 100):.1f}%")
    print(f"    搜索成功率: {((len(search_results) - len(no_results)) / len(search_results) * 100):.1f}%")
    print(f"    平均搜索时间: {avg_search_time:.1f}ms")
    
    return {
        "project": project_name,
        "py_files": len(py_files),
        "tested_files": files_tested,
        "total_lines": total_lines,
        "chunks": len(all_chunks),
        "parse_errors": len(parse_errors),
        "search_queries": len(search_results),
        "no_results": len(no_results),
        "avg_search_time": avg_search_time,
        "issues": []
    }


def analyze_issues(all_results):
    """分析所有项目的测试结果，找出系统性问题"""
    print_header("🔧 系统性问题分析")
    
    all_issues = []
    
    for result in all_results:
        if not result:
            continue
        
        if result['no_results'] > 2:
            all_issues.append({
                "project": result['project'],
                "severity": "high",
                "issue": "搜索召回率低",
                "description": f"{result['no_results']}/{result['search_queries']} 查询无结果"
            })
        
        if result['parse_errors'] > result['tested_files'] * 0.1:
            all_issues.append({
                "project": result['project'],
                "severity": "medium",
                "issue": "代码解析失败率高",
                "description": f"{result['parse_errors']}/{result['tested_files']} 文件解析失败"
            })
        
        if result['avg_search_time'] > 100:
            all_issues.append({
                "project": result['project'],
                "severity": "low",
                "issue": "搜索速度慢",
                "description": f"平均 {result['avg_search_time']:.1f}ms"
            })
    
    if all_issues:
        print(f"\n  发现 {len(all_issues)} 个系统性问题:\n")
        
        # 按严重性分组
        high = [i for i in all_issues if i['severity'] == 'high']
        medium = [i for i in all_issues if i['severity'] == 'medium']
        low = [i for i in all_issues if i['severity'] == 'low']
        
        for issue in high:
            print(f"  🔴 [{issue['project']}] {issue['issue']}")
            print(f"     {issue['description']}\n")
        
        for issue in medium:
            print(f"  🟡 [{issue['project']}] {issue['issue']}")
            print(f"     {issue['description']}\n")
        
        for issue in low:
            print(f"  🟢 [{issue['project']}] {issue['issue']}")
            print(f"     {issue['description']}\n")
    else:
        print(f"\n  ✅ 没有发现严重问题！")
    
    return all_issues


def suggest_improvements(issues):
    """根据问题提出改进建议"""
    print_header("💡 改进建议")
    
    suggestions = []
    
    # 统计问题类型
    issue_types = {}
    for issue in issues:
        issue_type = issue['issue']
        issue_types[issue_type] = issue_types.get(issue_type, 0) + 1
    
    # 生成建议
    if '搜索召回率低' in issue_types:
        suggestions.append({
            "priority": 1,
            "title": "扩展同义词库",
            "description": f"在 {issue_types['搜索召回率低']} 个项目中出现，需要针对不同项目类型扩展同义词"
        })
        
        suggestions.append({
            "priority": 2,
            "title": "增加模糊匹配",
            "description": "当前精确匹配无法覆盖变体词汇，需要增强模糊匹配算法"
        })
    
    if '代码解析失败率高' in issue_types:
        suggestions.append({
            "priority": 3,
            "title": "增强解析器容错性",
            "description": "某些文件格式导致解析失败，需要更好的错误处理"
        })
    
    suggestions.append({
        "priority": 4,
        "title": "优化搜索性能",
        "description": "当文档数超过500时，考虑使用倒排索引或分布式搜索"
    })
    
    # 按优先级排序
    suggestions.sort(key=lambda x: x['priority'])
    
    print(f"\n  改进建议 ({len(suggestions)} 项):\n")
    for i, sug in enumerate(suggestions, 1):
        print(f"  {i}. {sug['title']}")
        print(f"     {sug['description']}\n")
    
    return suggestions


def main():
    print_header("🚀 Code RAG v11.0 - 多项目综合测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    projects = [
        ("Flask", project_root / "flask_test_project"),
        ("Django", project_root / "django_test_project"),
        ("Ansible", project_root / "ansible_test_project"),
        ("VSCode", project_root / "vscode_test_project"),
    ]
    
    results = []
    
    for name, path in projects:
        result = test_single_project(name, path)
        results.append(result)
    
    # 分析问题
    issues = analyze_issues(results)
    
    # 改进建议
    suggestions = suggest_improvements(issues)
    
    # 总结
    print_header("📋 测试总结")
    
    total_files = sum(r['py_files'] for r in results if r)
    total_chunks = sum(r['chunks'] for r in results if r)
    total_queries = sum(r['search_queries'] for r in results if r)
    total_no_results = sum(r['no_results'] for r in results if r)
    
    print(f"\n  📊 综合统计:")
    print(f"     测试项目: {len([r for r in results if r])} 个")
    print(f"     Python文件: {total_files:,} 个")
    print(f"     代码块: {total_chunks:,} 个")
    print(f"     搜索查询: {total_queries} 次")
    print(f"     无结果查询: {total_no_results} 次")
    print(f"     发现问题: {len(issues)} 个")
    print(f"     改进建议: {len(suggestions)} 项")
    
    print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    print("\n" + "="*100)
    print("  🎉 多项目测试完成！")
    print("="*100)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
