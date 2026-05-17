"""
Code RAG v15.0 - 增强型命令行界面
用户友好的交互式CLI，带彩色输出和命令补全
"""

import sys
import os
import time
import json
import argparse
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    from rich import print as rprint
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from code_rag.data_layer.code_parser_and_document_processor import CodeParser
from code_rag.search_layer.bm25_search_engine import BM25Index
from code_rag.processing_layer.code_intelligence_and_semantic_understanding import (
    analyze_code_intelligence
)
from code_rag.search_layer.nl2code_converter import nl2code
from code_rag.processing_layer.code_dependency_analyzer import analyze_dependencies
from code_rag.processing_layer.incremental_index_and_parallel_processing import (
    create_incremental_indexer,
    create_parallel_engine,
    create_cache_manager
)


class Colors:
    """ANSI 颜色代码"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    BG_BLACK = '\033[40m'
    BG_GREEN = '\033[42m'


class EnhancedCLI:
    """
    增强型命令行界面
    提供友好的交互体验
    """

    def __init__(self):
        self.console = Console() if HAS_RICH else None
        self.parser = CodeParser()
        self.search_index = BM25Index()
        self.is_indexed = False
        self.indexed_dir = ""
        self.index_stats = {}
        
        self.colors = Colors()

    def print_banner(self):
        """打印欢迎横幅"""
        banner = f"""
{self.colors.CYAN}{self.colors.BOLD}
╔═══════════════════════════════════════════════════════════╗
║                                                           ║
║   🧠  Code RAG v15.0 - 智能代码检索系统                    ║
║                                                           ║
║   快速 · 智能 · 易用                                       ║
║                                                           ║
╚═══════════════════════════════════════════════════════════╝
{self.colors.RESET}
        """
        print(banner)

    def print_info(self, message: str):
        """打印信息"""
        print(f"{self.colors.BLUE}ℹ️  {message}{self.colors.RESET}")

    def print_success(self, message: str):
        """打印成功信息"""
        print(f"{self.colors.GREEN}✅ {message}{self.colors.RESET}")

    def print_warning(self, message: str):
        """打印警告信息"""
        print(f"{self.colors.YELLOW}⚠️  {message}{self.colors.RESET}")

    def print_error(self, message: str):
        """打印错误信息"""
        print(f"{self.colors.RED}❌ {message}{self.colors.RESET}")

    def print_header(self, title: str):
        """打印标题"""
        print(f"\n{self.colors.CYAN}{self.colors.BOLD}{'='*60}")
        print(f"  {title}")
        print(f"{'='*60}{self.colors.RESET}\n")

    def print_table(self, headers: List[str], rows: List[List[str]]):
        """打印表格"""
        if HAS_RICH:
            table = Table(show_header=True, header_style="bold magenta")
            for header in headers:
                table.add_column(header)
            for row in rows:
                table.add_row(*row)
            self.console.print(table)
        else:
            col_widths = [len(h) for h in headers]
            for row in rows:
                for i, cell in enumerate(row):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
            
            header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
            separator = "-+-".join("-" * w for w in col_widths)
            
            print(header_line)
            print(separator)
            for row in rows:
                print(" | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row)))
            print()

    def print_search_results(self, results: List[Dict], query: str):
        """打印搜索结果"""
        if not results:
            self.print_warning("没有找到相关结果")
            return
        
        self.print_header(f"🔍 搜索结果: '{query}'")
        
        print(f"找到 {len(results)} 个相关代码块:\n")
        
        for i, result in enumerate(results[:10], 1):
            score = result.get('score', 0)
            content = result.get('text', result.get('content', ''))
            
            preview = content[:200] + "..." if len(content) > 200 else content
            
            score_bar = "█" * int(score * 10) + "░" * (10 - int(score * 10))
            
            print(f"{self.colors.PURPLE}{i}. {self.colors.BOLD}相关性: [{score_bar}] {score:.2f}{self.colors.RESET}")
            print(f"{self.colors.CYAN}{'-'*60}{self.colors.RESET}")
            print(f"{self.colors.WHITE}{preview}{self.colors.RESET}")
            print()

    def print_code_analysis(self, code: str, analysis: Dict):
        """打印代码分析结果"""
        self.print_header("📊 代码分析结果")
        
        print(f"{self.colors.GREEN}检测语言:{self.colors.RESET} {analysis.get('detected_language', 'unknown')}")
        print(f"{self.colors.GREEN}主要意图:{self.colors.RESET} {analysis.get('intent', {}).get('primary', 'unknown')}")
        print(f"{self.colors.GREEN}置信度:{self.colors.RESET} {analysis.get('intent', {}).get('confidence', 0):.2f}")
        
        print(f"\n{self.colors.YELLOW}标签:{self.colors.RESET}")
        for tag in analysis.get('tags', [])[:10]:
            print(f"  • {tag.get('name', '')} [{tag.get('category', '')}]")
        
        print(f"\n{self.colors.CYAN}摘要:{self.colors.RESET}")
        print(f"  {analysis.get('summary', {}).get('short', 'N/A')}")

    def print_dependency_analysis(self, stats: Dict):
        """打印依赖分析结果"""
        self.print_header("📊 依赖分析结果")
        
        print(f"{self.colors.GREEN}文件数:{self.colors.RESET} {stats.get('files', 0)}")
        print(f"{self.colors.GREEN}函数数:{self.colors.RESET} {stats.get('functions', 0)}")
        print(f"{self.colors.GREEN}类数:{self.colors.RESET} {stats.get('classes', 0)}")
        print(f"{self.colors.GREEN}代码行数:{self.colors.RESET} {stats.get('total_lines', 0):,}")
        print(f"{self.colors.GREEN}导入语句:{self.colors.RESET} {stats.get('imports', 0)}")
        
        if stats.get('top_imported_modules'):
            print(f"\n{self.colors.YELLOW}最常导入的模块:{self.colors.RESET}")
            for module, count in stats['top_imported_modules'][:5]:
                if module:
                    print(f"  • {module}: {count} 次")

    def index_directory(self, directory: str) -> bool:
        """索引代码目录"""
        self.print_header("🚀 开始索引")
        
        dir_path = Path(directory)
        if not dir_path.exists():
            self.print_error(f"目录不存在: {directory}")
            return False
        
        self.print_info(f"索引目录: {directory}")
        
        start_time = time.time()
        
        all_chunks = []
        files_processed = 0
        
        try:
            for py_file in dir_path.rglob("*.py"):
                if any(skip in str(py_file) for skip in ['__pycache__', '.git', 'venv', '.venv', 'test', 'tests']):
                    continue
                
                try:
                    doc = self.parser.parse_file(str(py_file))
                    for chunk in doc.chunks:
                        if len(chunk.content) >= 30:
                            all_chunks.append(chunk.content)
                    files_processed += 1
                    
                    if files_processed % 20 == 0:
                        self.print_info(f"已处理 {files_processed} 个文件...")
                        
                except Exception as e:
                    continue
            
            if all_chunks:
                self.search_index.add_documents(all_chunks)
                self.is_indexed = True
                self.indexed_dir = directory
                
                elapsed = time.time() - start_time
                
                self.print_success(f"索引完成!")
                print(f"  处理文件: {files_processed}")
                print(f"  索引代码块: {len(all_chunks)}")
                print(f"  耗时: {elapsed:.2f}秒")
                
                self.index_stats = {
                    'files': files_processed,
                    'chunks': len(all_chunks),
                    'time': elapsed
                }
                
                return True
            else:
                self.print_warning("没有找到可索引的代码文件")
                return False
                
        except Exception as e:
            self.print_error(f"索引失败: {e}")
            return False

    def search_code(self, query: str, top_k: int = 5) -> List[Dict]:
        """搜索代码"""
        if not self.is_indexed:
            self.print_warning("请先索引代码目录 (使用 index 命令)")
            return []
        
        self.print_info(f"搜索: '{query}'")
        
        start_time = time.time()
        
        try:
            results = self.search_index.search(query, k=top_k)
            
            elapsed = (time.time() - start_time) * 1000
            
            print(f"{self.colors.GREEN}找到 {len(results)} 个结果 ({elapsed:.1f}ms){self.colors.RESET}\n")
            
            return results
            
        except Exception as e:
            self.print_error(f"搜索失败: {e}")
            return []

    def analyze_code(self, code: str) -> Dict:
        """分析代码"""
        try:
            return analyze_code_intelligence(code)
        except Exception as e:
            self.print_error(f"分析失败: {e}")
            return {}

    def nl2code_search(self, query: str) -> Dict:
        """NL2Code 查询"""
        try:
            return nl2code(query)
        except Exception as e:
            self.print_error(f"NL2Code 转换失败: {e}")
            return {}

    def show_help(self):
        """显示帮助"""
        help_text = f"""
{self.colors.CYAN}{self.colors.BOLD}Code RAG v15.0 - 帮助信息{self.colors.RESET}

{self.colors.GREEN}可用命令:{self.colors.RESET}

  {self.colors.YELLOW}index <目录>{self.colors.RESET}
    索引代码目录
    示例: index ./src

  {self.colors.YELLOW}search <查询>{self.colors.RESET}
    搜索代码
    示例: search user authentication

  {self.colors.YELLOW}analyze{self.colors.RESET}
    分析剪贴板或输入的代码
    示例: analyze

  {self.colors.YELLOW}nl2code <自然语言>{self.colors.RESET}
    自然语言转代码搜索
    示例: nl2code create user login

  {self.colors.YELLOW}deps [目录]{self.colors.RESET}
    分析代码依赖
    示例: deps ./src

  {self.colors.YELLOW}stats{self.colors.RESET}
    显示索引统计

  {self.colors.YELLOW}help{self.colors.RESET}
    显示此帮助信息

  {self.colors.YELLOW}exit / quit{self.colors.RESET}
    退出程序

{self.colors.GREEN}快捷键:{self.colors.RESET}
  Ctrl+C - 取消当前操作
  Ctrl+D - 退出
  Tab - 命令补全 (交互模式)

{self.colors.GREEN}示例:{self.colors.RESET}
  $ code-rag index ./my-project
  $ code-rag search "user authentication"
  $ code-rag nl2code "how to validate email"

{self.colors.CYAN}更多信息: https://github.com/code-rag{self.colors.RESET}
"""
        print(help_text)

    def show_status(self):
        """显示状态"""
        self.print_header("📊 系统状态")
        
        print(f"{self.colors.GREEN}索引状态:{self.colors.RESET} {'已索引' if self.is_indexed else '未索引'}")
        
        if self.is_indexed:
            print(f"{self.colors.GREEN}索引目录:{self.colors.RESET} {self.indexed_dir}")
            print(f"{self.colors.GREEN}文件数:{self.colors.RESET} {self.index_stats.get('files', 0)}")
            print(f"{self.colors.GREEN}代码块:{self.colors.RESET} {self.index_stats.get('chunks', 0)}")

    def run_interactive(self):
        """运行交互式模式"""
        self.print_banner()
        self.print_info("输入 'help' 查看可用命令\n")
        
        while True:
            try:
                user_input = input(f"{self.colors.GREEN}code-rag>{self.colors.RESET} ").strip()
                
                if not user_input:
                    continue
                
                parts = user_input.split(maxsplit=1)
                command = parts[0].lower()
                args = parts[1] if len(parts) > 1 else ""
                
                if command in ['exit', 'quit', 'q']:
                    self.print_success("再见!")
                    break
                
                elif command == 'help':
                    self.show_help()
                
                elif command == 'index':
                    if not args:
                        self.print_warning("请提供要索引的目录")
                        self.print_info("用法: index <目录>")
                    else:
                        self.index_directory(args)
                
                elif command == 'search':
                    if not self.is_indexed:
                        self.print_warning("请先索引代码目录")
                    elif not args:
                        self.print_warning("请提供搜索查询")
                        self.print_info("用法: search <查询>")
                    else:
                        results = self.search_code(args)
                        self.print_search_results(results, args)
                
                elif command == 'analyze':
                    self.print_info("请输入要分析的代码 (输入空行结束):")
                    lines = []
                    while True:
                        try:
                            line = input()
                            if line == "":
                                break
                            lines.append(line)
                        except EOFError:
                            break
                    
                    code = "\n".join(lines)
                    if code.strip():
                        analysis = self.analyze_code(code)
                        self.print_code_analysis(code, analysis)
                
                elif command == 'nl2code':
                    if not args:
                        self.print_warning("请提供自然语言查询")
                        self.print_info("用法: nl2code <自然语言>")
                    else:
                        result = self.nl2code_search(args)
                        if result:
                            self.print_header("🔄 NL2Code 转换结果")
                            print(f"{self.colors.GREEN}意图:{self.colors.RESET} {result.get('intent', 'unknown')}")
                            print(f"{self.colors.GREEN}置信度:{self.colors.RESET} {result.get('confidence', 0):.2f}")
                            print(f"\n{self.colors.YELLOW}生成的搜索查询:{self.colors.RESET}")
                            for query in result.get('search_queries', []):
                                print(f"  • {query}")
                
                elif command == 'deps':
                    target_dir = args if args else self.indexed_dir
                    if not target_dir:
                        self.print_warning("请提供要分析的目录")
                        self.print_info("用法: deps [目录]")
                    else:
                        self.print_info(f"分析目录: {target_dir}")
                        stats = analyze_dependencies(target_dir)
                        self.print_dependency_analysis(stats)
                
                elif command == 'stats':
                    self.show_status()
                
                else:
                    self.print_warning(f"未知命令: {command}")
                    self.print_info("输入 'help' 查看可用命令")
                    
            except KeyboardInterrupt:
                print(f"\n{self.colors.YELLOW}操作已取消{self.colors.RESET}")
            except EOFError:
                break
        
        return 0


def main():
    """主函数"""
    import sys
    
    cli = EnhancedCLI()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        args = " ".join(sys.argv[2:]) if len(sys.argv) > 2 else ""
        
        if command == 'index' and args:
            cli.index_directory(args)
        elif command == 'search' and args:
            cli.index_directory(args) if not cli.is_indexed else None
            results = cli.search_code(args)
            cli.print_search_results(results, args)
        elif command == 'help':
            cli.show_help()
        else:
            cli.print_banner()
            cli.show_help()
    else:
        cli.run_interactive()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
