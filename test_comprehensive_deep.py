#!/usr/bin/env python3
"""
Code RAG v11.0 - 全面深度测试
测试多个真实GitHub项目，全面发现系统问题
"""

import sys
import os
import time
import tempfile
import subprocess
import traceback
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Add project path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))


def print_header(title):
    print("\n" + "=" * 100)
    print(f"  {title}")
    print("=" * 100)


def print_section(title):
    print(f"\n{'=' * 100}")
    print(f"  {title}")
    print(f"{'=' * 100}")


def clone_repo(repo_url: str, target_dir: Path) -> bool:
    """克隆仓库"""
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, str(target_dir)],
            capture_output=True,
            text=True,
            timeout=600
        )
        return result.returncode == 0
    except:
        return False


def scan_project(project_dir: Path) -> Dict[str, Any]:
    """扫描项目"""
    files_by_ext = defaultdict(list)
    total_lines = 0
    total_size = 0
    
    for root, dirs, files in os.walk(str(project_dir)):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                   ('venv', '__pycache__', 'node_modules', '.git')]
        
        for file in files:
            file_path = Path(root) / file
            ext = file_path.suffix.lower()
            
            try:
                files_by_ext[ext].append(file_path)
                total_size += file_path.stat().st_size
                
                if ext in ['.py', '.js', '.ts', '.java', '.cpp', '.md']:
                    try:
                        total_lines += len(file_path.read_text(encoding='utf-8', errors='ignore').split('\n'))
                    except:
                        pass
            except:
                pass
    
    return {
        "files": files_by_ext,
        "total_files": sum(len(v) for v in files_by_ext.values()),
        "total_lines": total_lines,
        "total_size": total_size
    }


def test_code_parsing_issues(files: List[Path], max_files: int = 100) -> Dict[str, Any]:
    """深度测试代码解析，发现各种问题"""
    from code_rag.data_layer import CodeParser
    
    parser = CodeParser()
    results = {
        "success": 0,
        "failures": 0,
        "issues": {
            "tiny_chunks": [],
            "parse_errors": [],
            "empty_files": [],
            "large_files": [],
            "encoding_issues": [],
            "syntax_complexity": []
        },
        "stats": {
            "total_chunks": 0,
            "avg_chunk_size": 0,
            "parse_time_total": 0
        }
    }
    
    for file_path in files[:max_files]:
        try:
            start = time.time()
            doc = parser.parse_file(str(file_path))
            elapsed = time.time() - start
            
            results["stats"]["parse_time_total"] += elapsed
            results["success"] += 1
            
            # 检查问题
            if len(doc.chunks) == 0:
                results["issues"]["empty_files"].append(str(file_path))
            elif len(doc.chunks) < 3:
                results["issues"]["tiny_chunks"].append({
                    "file": str(file_path),
                    "chunks": len(doc.chunks)
                })
            
            # 检查每个代码块
            for chunk in doc.chunks:
                if len(chunk.content) < parser.MIN_CHUNK_SIZE:
                    results["issues"]["tiny_chunks"].append({
                        "file": str(file_path),
                        "chunk_size": len(chunk.content),
                        "type": chunk.chunk_type
                    })
                    break
            
            # 检查大文件
            if len(doc.chunks) > 50:
                results["issues"]["large_files"].append({
                    "file": str(file_path),
                    "chunks": len(doc.chunks)
                })
            
            results["stats"]["total_chunks"] += len(doc.chunks)
            
        except UnicodeDecodeError as e:
            results["issues"]["encoding_issues"].append({
                "file": str(file_path),
                "error": str(e)
            })
        except Exception as e:
            results["failures"] += 1
            results["issues"]["parse_errors"].append({
                "file": str(file_path),
                "error": str(e),
                "type": type(e).__name__
            })
    
    # 计算平均大小
    if results["stats"]["total_chunks"] > 0:
        results["stats"]["avg_chunk_size"] = results["stats"]["total_chunks"] / results["success"] if results["success"] > 0 else 0
    
    return results


def test_search_comprehensive(bm25_index, test_cases: List[Dict]) -> Dict[str, Any]:
    """全面搜索测试"""
    results = {
        "total_tests": len(test_cases),
        "passed": 0,
        "failed": 0,
        "issues": []
    }
    
    for test in test_cases:
        query = test["query"]
        expected_keywords = test.get("expect_keywords", [])
        
        search_results = bm25_index.search(query, k=10)
        
        if len(search_results) == 0:
            results["failed"] += 1
            results["issues"].append({
                "query": query,
                "issue": "no_results",
                "suggestion": test.get("suggestion", "")
            })
        elif len(search_results) < test.get("min_results", 3):
            results["issues"].append({
                "query": query,
                "issue": "few_results",
                "found": len(search_results),
                "expected": test.get("min_results", 3)
            })
        else:
            # 检查相关性
            relevant = False
            for result in search_results[:3]:
                text_lower = result.text.lower()
                for keyword in expected_keywords:
                    if keyword.lower() in text_lower:
                        relevant = True
                        break
                if relevant:
                    break
            
            if relevant:
                results["passed"] += 1
            else:
                results["failed"] += 1
                results["issues"].append({
                    "query": query,
                    "issue": "low_relevance",
                    "top_result": search_results[0].text[:100]
                })
    
    return results


def test_performance_stress(project_dir: Path, files: List[Path]) -> Dict[str, Any]:
    """性能压力测试"""
    from code_rag.data_layer import CodeParser
    from code_rag.search_layer import BM25Index
    
    results = {
        "parsing": {},
        "indexing": {},
        "search": {},
        "memory_usage": []
    }
    
    # 测试不同规模的解析
    test_sizes = [10, 30, 50, 100]
    
    parser = CodeParser()
    
    for size in test_sizes:
        if size > len(files):
            continue
        
        start = time.time()
        all_chunks = []
        
        for file_path in files[:size]:
            try:
                doc = parser.parse_file(str(file_path))
                all_chunks.extend([c.content for c in doc.chunks if c.content])
            except:
                pass
        
        parse_time = time.time() - start
        
        results["parsing"][size] = {
            "time": parse_time,
            "chunks": len(all_chunks),
            "time_per_file": parse_time / size if size > 0 else 0
        }
        
        # 测试索引
        if all_chunks:
            start = time.time()
            bm25 = BM25Index()
            bm25.add_documents(all_chunks)
            index_time = time.time() - start
            
            results["indexing"][size] = {
                "time": index_time,
                "docs": len(all_chunks)
            }
            
            # 测试搜索
            search_times = []
            for i in range(10):
                start = time.time()
                bm25.search("test function", k=10)
                search_times.append(time.time() - start)
            
            results["search"][size] = {
                "avg_time": sum(search_times) / len(search_times),
                "min_time": min(search_times),
                "max_time": max(search_times)
            }
    
    return results


def test_edge_cases() -> Dict[str, Any]:
    """边界情况测试"""
    results = {
        "tests": [],
        "passed": 0,
        "failed": 0
    }
    
    from code_rag.search_layer import BM25Index
    
    # 测试空查询
    bm25 = BM25Index()
    bm25.add_documents(["test document"])
    
    try:
        result = bm25.search("", k=5)
        results["tests"].append({"test": "empty_query", "passed": True})
        results["passed"] += 1
    except Exception as e:
        results["tests"].append({"test": "empty_query", "passed": False, "error": str(e)})
        results["failed"] += 1
    
    # 测试特殊字符
    try:
        result = bm25.search("test<script>alert('xss')</script>", k=5)
        results["tests"].append({"test": "special_chars", "passed": True})
        results["passed"] += 1
    except Exception as e:
        results["tests"].append({"test": "special_chars", "passed": False, "error": str(e)})
        results["failed"] += 1
    
    # 测试超长查询
    try:
        long_query = "test " * 1000
        result = bm25.search(long_query, k=5)
        results["tests"].append({"test": "long_query", "passed": True})
        results["passed"] += 1
    except Exception as e:
        results["tests"].append({"test": "long_query", "passed": False, "error": str(e)})
        results["failed"] += 1
    
    # 测试Unicode
    try:
        result = bm25.search("测试中文功能 函数测试", k=5)
        results["tests"].append({"test": "unicode_query", "passed": True})
        results["passed"] += 1
    except Exception as e:
        results["tests"].append({"test": "unicode_query", "passed": False, "error": str(e)})
        results["failed"] += 1
    
    return results


def run_full_test():
    """运行完整测试"""
    print_header("🚀 Code RAG v11.0 - 全面深度测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试项目列表
    projects = [
        ("requests", "https://github.com/psf/requests"),
        ("flask", "https://github.com/pallets/flask"),
        ("django", "https://github.com/django/django"),
        ("numpy", "https://github.com/numpy/numpy"),
        ("scikit-learn", "https://github.com/scikit-learn/scikit-learn"),
    ]
    
    all_issues = defaultdict(list)
    total_projects = 0
    
    for project_name, repo_url in projects[:2]:  # 测试前2个
        print_section(f"🔍 测试项目: {project_name}")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            project_dir = Path(tmpdir) / project_name
            
            print(f"  克隆仓库...")
            if not clone_repo(repo_url, project_dir):
                print(f"  ❌ 克隆失败，跳过")
                continue
            
            # 扫描项目
            scan = scan_project(project_dir)
            print(f"  文件数: {scan['total_files']}, 代码行: ~{scan['total_lines']:,}")
            
            # 获取文件列表
            py_files = scan['files'].get('.py', [])
            md_files = scan['files'].get('.md', [])
            all_files = py_files + md_files
            
            if not all_files:
                continue
            
            total_projects += 1
            
            # 1. 代码解析问题测试
            print(f"\n  📝 测试代码解析...")
            parse_results = test_code_parsing_issues(all_files, max_files=100)
            print(f"    成功: {parse_results['success']}, 失败: {parse_results['failures']}")
            print(f"    代码块: {parse_results['stats']['total_chunks']}, 平均: {parse_results['stats']['avg_chunk_size']:.1f}")
            
            if parse_results['issues']['empty_files']:
                print(f"    ⚠️ 空文件: {len(parse_results['issues']['empty_files'])} 个")
                all_issues['empty_files'].extend(parse_results['issues']['empty_files'][:5])
            
            if parse_results['issues']['parse_errors']:
                print(f"    ❌ 解析错误: {len(parse_results['issues']['parse_errors'])} 个")
                for err in parse_results['issues']['parse_errors'][:3]:
                    print(f"      - {err['file']}: {err['type']}")
                all_issues['parse_errors'].extend(parse_results['issues']['parse_errors'])
            
            if parse_results['issues']['encoding_issues']:
                print(f"    ⚠️ 编码问题: {len(parse_results['issues']['encoding_issues'])} 个")
                all_issues['encoding_issues'].extend(parse_results['issues']['encoding_issues'])
            
            # 2. 搜索测试
            print(f"\n  🔍 测试搜索功能...")
            
            # 准备索引
            from code_rag.data_layer import CodeParser
            from code_rag.search_layer import BM25Index
            
            parser = CodeParser()
            bm25 = BM25Index()
            
            for file_path in all_files[:100]:
                try:
                    doc = parser.parse_file(str(file_path))
                    for chunk in doc.chunks:
                        if chunk.content:
                            bm25.add_document(chunk.content)
                except:
                    pass
            
            # 全面搜索测试用例
            search_tests = [
                {"query": "function implementation", "expect_keywords": ["def", "function"], "min_results": 3, "suggestion": "检查函数解析"},
                {"query": "class definition", "expect_keywords": ["class"], "min_results": 3, "suggestion": "检查类解析"},
                {"query": "import module", "expect_keywords": ["import"], "min_results": 2, "suggestion": "检查导入语句"},
                {"query": "test case", "expect_keywords": ["test", "Test"], "min_results": 3, "suggestion": "检查测试代码"},
                {"query": "configuration", "expect_keywords": ["config", "setting"], "min_results": 2, "suggestion": "添加同义词"},
                {"query": "error handling", "expect_keywords": ["error", "exception"], "min_results": 2, "suggestion": "检查异常处理"},
                {"query": "database query", "expect_keywords": ["sql", "query", "database"], "min_results": 2, "suggestion": "检查数据库代码"},
                {"query": "API endpoint", "expect_keywords": ["api", "endpoint", "route"], "min_results": 2, "suggestion": "检查API代码"},
                {"query": "logging", "expect_keywords": ["log", "logger"], "min_results": 2, "suggestion": "检查日志代码"},
                {"query": "cache", "expect_keywords": ["cache", "cache"], "min_results": 1, "suggestion": "检查缓存代码"},
            ]
            
            search_results = test_search_comprehensive(bm25, search_tests)
            print(f"    测试: {search_results['total_tests']}, 通过: {search_results['passed']}, 失败: {search_results['failed']}")
            
            if search_results['issues']:
                print(f"    ⚠️ 发现 {len(search_results['issues'])} 个搜索问题:")
                for issue in search_results['issues'][:5]:
                    print(f"      - \"{issue['query']}\": {issue['issue']}")
                all_issues['search_issues'].extend(search_results['issues'])
            
            # 3. 性能测试
            print(f"\n  ⚡ 测试性能...")
            perf_results = test_performance_stress(project_dir, all_files)
            
            if perf_results['parsing']:
                last_size = list(perf_results['parsing'].keys())[-1]
                parse_data = perf_results['parsing'][last_size]
                print(f"    解析 {last_size} 文件: {parse_data['time']:.2f}s ({parse_data['time_per_file']*1000:.1f}ms/file)")
            
            if perf_results['search']:
                last_size = list(perf_results['search'].keys())[-1]
                search_data = perf_results['search'][last_size]
                print(f"    搜索延迟: {search_data['avg_time']*1000:.2f}ms (平均)")
    
    # 边界情况测试
    print_section("🧪 边界情况测试")
    edge_results = test_edge_cases()
    print(f"  测试: {edge_results['passed'] + edge_results['failed']}, 通过: {edge_results['passed']}, 失败: {edge_results['failed']}")
    
    if edge_results['failed'] > 0:
        for test in edge_results['tests']:
            if not test['passed']:
                print(f"    ❌ {test['test']}: {test.get('error', 'unknown')}")
                all_issues['edge_cases'].append(test)
    
    # 总结
    print_header("📊 测试总结")
    
    print(f"\n  测试项目数: {total_projects}")
    print(f"\n  问题分类统计:")
    
    for issue_type, issues in all_issues.items():
        print(f"    {issue_type}: {len(issues)} 个")
    
    print(f"\n  💡 改进建议:")
    
    if all_issues.get('parse_errors'):
        print(f"    1. 增强代码解析器错误处理能力")
        print(f"       - 添加更多语法支持")
        print(f"       - 改进错误信息")
    
    if all_issues.get('empty_files'):
        print(f"    2. 优化空文件和小型文件处理")
        print(f"       - 添加最小内容检查")
        print(f"       - 跳过无意义文件")
    
    if all_issues.get('encoding_issues'):
        print(f"    3. 改进编码处理")
        print(f"       - 添加更多编码支持")
        print(f"       - 改进错误恢复")
    
    if all_issues.get('search_issues'):
        print(f"    4. 继续优化搜索召回")
        print(f"       - 扩展同义词库")
        print(f"       - 改进相关性算法")
    
    print(f"\n完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 保存报告
    report = {
        "timestamp": datetime.now().isoformat(),
        "projects_tested": total_projects,
        "all_issues": dict(all_issues),
        "edge_results": edge_results
    }
    
    import json
    report_path = project_root / "COMPREHENSIVE_TEST_REPORT.json"
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n  ✅ 完整测试报告已保存到: {report_path}")


if __name__ == "__main__":
    run_full_test()
