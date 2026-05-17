#!/usr/bin/env python3
"""
Code RAG v11.0 - 真实项目深度测试和问题发现
测试多个真实GitHub项目，发现实际使用中的问题
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


def print_error(message):
    print(f"\n  ❌ ERROR: {message}")


def print_warning(message):
    print(f"\n  ⚠️ WARNING: {message}")


def print_success(message):
    print(f"\n  ✅ {message}")


def clone_repo(repo_url: str, target_dir: Path) -> bool:
    """克隆GitHub仓库"""
    print(f"    克隆: {repo_url}")
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", "--filter=blob:none", repo_url, str(target_dir)],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode == 0:
            print(f"    ✅ 克隆成功")
            return True
        else:
            print(f"    ⚠️ 克隆失败: {result.stderr[:100]}")
            return False
    except Exception as e:
        print(f"    ❌ 克隆异常: {e}")
        return False


def scan_project(project_dir: Path) -> Dict[str, Any]:
    """扫描项目文件"""
    print("    扫描项目文件...")
    
    files_by_type = defaultdict(list)
    total_size = 0
    total_lines = 0
    
    for root, dirs, files in os.walk(str(project_dir)):
        dirs[:] = [d for d in dirs if not d.startswith('.') and d not in 
                  ('venv', '.venv', 'node_modules', '__pycache__')]
        
        for file in files:
            file_path = Path(root) / file
            ext = file_path.suffix.lower()
            
            try:
                files_by_type[ext].append(file_path)
                total_size += file_path.stat().st_size
                
                # 统计行数（仅文本文件）
                if ext in ['.py', '.js', '.ts', '.java', '.cpp', '.md', '.txt', '.rst']:
                    try:
                        total_lines += len(file_path.read_text(encoding='utf-8', errors='ignore').split('\n'))
                    except:
                        pass
            except Exception as e:
                pass
    
    return {
        "files_by_type": files_by_type,
        "total_files": sum(len(v) for v in files_by_type.values()),
        "total_size": total_size,
        "total_lines": total_lines
    }


def test_code_parsing(project_dir: Path, files: List[Path], max_files: int = 50):
    """测试代码解析，发现问题"""
    from code_rag.data_layer import CodeParser
    
    parser = CodeParser()
    results = {
        "success": 0,
        "failures": 0,
        "errors": [],
        "total_chunks": 0,
        "chunk_sizes": [],
        "time_per_file": []
    }
    
    print(f"    解析 {min(len(files), max_files)} 个文件...")
    
    for i, file_path in enumerate(files[:max_files]):
        try:
            start = time.time()
            doc = parser.parse_file(str(file_path))
            elapsed = time.time() - start
            
            results["success"] += 1
            results["total_chunks"] += len(doc.chunks)
            results["chunk_sizes"].extend([len(c.content) for c in doc.chunks if c.content])
            results["time_per_file"].append(elapsed)
            
            # 检查潜在问题
            if len(doc.chunks) == 0:
                print_warning(f"文件 {file_path.name} 没有生成任何代码块")
            
            for chunk in doc.chunks:
                if len(chunk.content) < 10:
                    results["errors"].append({
                        "type": "tiny_chunk",
                        "file": str(file_path),
                        "chunk_content": chunk.content[:50]
                    })
                    if len(results["errors"]) < 5:
                        print_warning(f"文件 {file_path.name} 包含过小的代码块")
        
        except Exception as e:
            results["failures"] += 1
            error_info = {
                "type": "parse_error",
                "file": str(file_path),
                "error": str(e),
                "traceback": traceback.format_exc()[:500]
            }
            results["errors"].append(error_info)
            print_error(f"解析 {file_path.name} 失败: {e}")
    
    # 统计分析
    if results["time_per_file"]:
        avg_time = sum(results["time_per_file"]) / len(results["time_per_file"])
        print(f"    平均解析时间: {avg_time*1000:.2f}ms")
    
    if results["chunk_sizes"]:
        avg_chunk_size = sum(results["chunk_sizes"]) / len(results["chunk_sizes"])
        print(f"    平均代码块大小: {avg_chunk_size:.0f} 字符")
    
    return results


def test_search_functionality(project_dir: Path, files: List[Path]):
    """测试搜索功能"""
    from code_rag.data_layer import CodeParser
    from code_rag.search_layer import BM25Index
    
    parser = CodeParser()
    bm25 = BM25Index()
    
    all_texts = []
    
    print("    构建搜索索引...")
    
    for file_path in files[:30]:
        try:
            doc = parser.parse_file(str(file_path))
            for chunk in doc.chunks:
                if chunk.content and len(chunk.content) > 50:
                    all_texts.append(chunk.content)
        except Exception as e:
            pass
    
    if not all_texts:
        print_warning("没有足够的文本内容进行搜索测试")
        return {"error": "no_content"}
    
    bm25.add_documents(all_texts)
    
    # 测试查询
    test_queries = [
        "function definition",
        "class implementation",
        "import statement",
        "error handling",
        "test case",
        "configuration",
        "logging",
        "API",
        "database",
        "cache"
    ]
    
    results = {
        "queries_tested": len(test_queries),
        "avg_results": 0,
        "avg_time": 0,
        "query_results": []
    }
    
    total_results = 0
    total_time = 0
    
    print("    测试搜索查询...")
    
    for query in test_queries:
        start = time.time()
        search_results = bm25.search(query, k=5)
        elapsed = time.time() - start
        
        total_results += len(search_results)
        total_time += elapsed
        
        results["query_results"].append({
            "query": query,
            "results": len(search_results),
            "time_ms": elapsed * 1000
        })
        
        # 检查相关性
        if len(search_results) == 0:
            print_warning(f"查询 '{query}' 没有返回结果")
        else:
            # 检查第一个结果是否包含查询词
            first_result = search_results[0].text.lower()
            query_lower = query.lower()
            query_words = query_lower.split()
            matched = any(word in first_result for word in query_words)
            if not matched:
                print_warning(f"查询 '{query}' 的结果相关性可能较低")
    
    results["avg_results"] = total_results / len(test_queries)
    results["avg_time"] = (total_time / len(test_queries)) * 1000
    
    print(f"    平均每个查询返回 {results['avg_results']:.1f} 个结果")
    print(f"    平均查询时间: {results['avg_time']:.2f}ms")
    
    return results


def test_embedding_generation(texts: List[str]):
    """测试Embedding生成"""
    from code_rag.rag_engine import ProductionEmbeddingEngine
    
    print("    测试Embedding生成...")
    
    engine = ProductionEmbeddingEngine()
    
    results = {
        "success": 0,
        "failures": 0,
        "errors": [],
        "avg_time": 0,
        "embedding_dimension": None
    }
    
    test_texts = texts[:50]
    
    if not test_texts:
        print_warning("没有文本进行Embedding测试")
        return results
    
    try:
        start = time.time()
        embeddings = engine.encode_batch(test_texts)
        elapsed = time.time() - start
        
        results["success"] = len(embeddings)
        results["avg_time"] = (elapsed / len(test_texts)) * 1000
        
        if embeddings:
            results["embedding_dimension"] = len(embeddings[0])
        
        print(f"    Embedding生成: {len(embeddings)} 个, 维度: {results['embedding_dimension']}")
        print(f"    平均每个: {results['avg_time']:.2f}ms")
        
    except Exception as e:
        results["failures"] = len(test_texts)
        results["errors"].append(str(e))
        print_error(f"Embedding测试失败: {e}")
    
    return results


def run_project_test(project_name: str, repo_url: str):
    """运行单个项目测试"""
    print_section(f"🔍 测试项目: {project_name}")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        project_dir = Path(temp_dir) / project_name
        
        if not clone_repo(repo_url, project_dir):
            print_warning(f"无法克隆 {project_name}，跳过")
            return None
        
        # 扫描项目
        scan_result = scan_project(project_dir)
        print(f"    文件数: {scan_result['total_files']}")
        print(f"    代码行数: ~{scan_result['total_lines']:,}")
        print(f"    总大小: {scan_result['total_size'] / 1024 / 1024:.2f} MB")
        
        # 打印文件类型分布
        print("\n    文件类型分布:")
        for ext, files in sorted(scan_result["files_by_type"].items(), key=lambda x: len(x[1]), reverse=True)[:10]:
            print(f"      {ext}: {len(files)} 个")
        
        # 获取Python文件列表
        py_files = scan_result["files_by_type"].get('.py', [])
        md_files = scan_result["files_by_type"].get('.md', [])
        
        # 测试代码解析
        parsing_results = test_code_parsing(project_dir, py_files + md_files, max_files=50)
        print(f"\n    解析结果: {parsing_results['success']} 成功, {parsing_results['failures']} 失败")
        
        # 测试搜索
        search_results = test_search_functionality(project_dir, py_files[:30])
        
        # 收集文本用于Embedding测试
        texts_for_embedding = []
        parser = __import__('code_rag.data_layer', fromlist=['CodeParser']).CodeParser()
        for file_path in py_files[:10]:
            try:
                doc = parser.parse_file(str(file_path))
                texts_for_embedding.extend([c.content for c in doc.chunks if c.content and len(c.content) > 50])
            except:
                pass
        
        # 测试Embedding
        embedding_results = test_embedding_generation(texts_for_embedding)
        
        # 总结问题
        issues_found = []
        
        # 解析问题
        if parsing_results["failures"] > 0:
            issues_found.append(f"代码解析失败 {parsing_results['failures']} 个文件")
        
        if parsing_results.get("errors"):
            issues_found.append(f"发现 {len(parsing_results['errors'])} 个解析问题")
        
        # 搜索问题
        if search_results.get("avg_results", 0) < 2:
            issues_found.append("搜索返回结果较少")
        
        # 输出问题
        if issues_found:
            print_section(f"⚠️ 发现的问题 ({len(issues_found)})")
            for i, issue in enumerate(issues_found, 1):
                print(f"    {i}. {issue}")
        
        return {
            "project": project_name,
            "repo_url": repo_url,
            "scan_result": scan_result,
            "parsing_results": parsing_results,
            "search_results": search_results,
            "embedding_results": embedding_results,
            "issues_found": issues_found
        }


def main():
    print_header("🚀 Code RAG v11.0 - 真实项目深度测试")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 测试多个真实GitHub项目
    projects_to_test = [
        ("requests", "https://github.com/psf/requests"),
        ("flask", "https://github.com/pallets/flask"),
        ("pandas", "https://github.com/pandas-dev/pandas"),
        ("numpy", "https://github.com/numpy/numpy"),
        ("scikit-learn", "https://github.com/scikit-learn/scikit-learn"),
    ]
    
    all_results = []
    all_issues = []
    
    for project_name, repo_url in projects_to_test[:3]:  # 测试前3个项目
        result = run_project_test(project_name, repo_url)
        if result:
            all_results.append(result)
            all_issues.extend(result.get("issues_found", []))
    
    # 总结
    print_header("📊 测试总结")
    
    print(f"\n  测试项目数: {len(all_results)}")
    
    # 统计问题
    issue_counts = defaultdict(int)
    for issue in all_issues:
        issue_counts[issue] += 1
    
    if issue_counts:
        print("\n  发现的问题统计:")
        for issue, count in sorted(issue_counts.items(), key=lambda x: x[1], reverse=True):
            print(f"    {issue}: {count} 次")
    
    # 给出改进建议
    print("\n  💡 改进建议:")
    
    if any("解析失败" in issue for issue in all_issues):
        print("    1. 增强代码解析器对复杂语法的支持")
        print("    2. 添加更多编程语言的解析支持")
    
    if any("返回结果较少" in issue for issue in all_issues):
        print("    3. 优化BM25参数以提高搜索召回率")
        print("    4. 添加查询扩展功能")
    
    if any("Embedding" in issue for issue in all_issues):
        print("    5. 优化Embedding模型选择")
        print("    6. 添加缓存机制减少重复计算")
    
    print(f"\n  完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 保存测试报告
    report_path = project_root / "REAL_PROJECT_TEST_REPORT.md"
    save_report(all_results, report_path)
    print(f"\n  ✅ 测试报告已保存到: {report_path}")


def save_report(results, filepath):
    """保存测试报告"""
    report = []
    report.append("# 真实项目测试报告")
    report.append(f"生成时间: {datetime.now().isoformat()}")
    report.append("")
    
    for result in results:
        report.append(f"## {result['project']}")
        report.append(f"- 仓库: {result['repo_url']}")
        report.append(f"- 文件数: {result['scan_result']['total_files']}")
        report.append(f"- 代码行数: {result['scan_result']['total_lines']:,}")
        report.append(f"- 解析成功: {result['parsing_results']['success']}")
        report.append(f"- 解析失败: {result['parsing_results']['failures']}")
        
        if result['issues_found']:
            report.append("")
            report.append("### 发现的问题:")
            for issue in result['issues_found']:
                report.append(f"- {issue}")
    
    filepath.write_text("\n".join(report))


if __name__ == "__main__":
    from collections import defaultdict
    main()
