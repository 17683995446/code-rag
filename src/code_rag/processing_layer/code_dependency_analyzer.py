"""
代码依赖分析与可视化模块
v13.0 新增功能
"""

import re
import ast
from typing import List, Dict, Set, Tuple, Optional, Any
from pathlib import Path
from dataclasses import dataclass, field
from collections import defaultdict, Counter


@dataclass
class FunctionCall:
    """函数调用信息"""
    caller: str
    callee: str
    caller_file: str
    callee_file: Optional[str] = None
    line: int = 0


@dataclass
class ImportDependency:
    """导入依赖信息"""
    source_file: str
    imported_module: str
    imported_names: List[str] = field(default_factory=list)
    is_relative: bool = False


@dataclass
class ClassInheritance:
    """类继承关系"""
    class_name: str
    parent_classes: List[str]
    file_path: str


@dataclass
class CodeDependencyGraph:
    """代码依赖关系图"""
    # 函数调用关系
    function_calls: List[FunctionCall] = field(default_factory=list)
    # 模块导入关系
    imports: List[ImportDependency] = field(default_factory=list)
    # 类继承关系
    inheritance: List[ClassInheritance] = field(default_factory=list)
    # 文件统计
    file_statistics: Dict[str, Dict] = field(default_factory=dict)


class CodeDependencyAnalyzer:
    """
    代码依赖分析器
    分析函数调用、导入关系、类继承等
    """

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.graph = CodeDependencyGraph()
        self._function_locations: Dict[str, str] = {}  # func_name -> file

    def analyze_directory(self, directory: str) -> CodeDependencyGraph:
        """分析整个目录"""
        dir_path = Path(directory)
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        print(f"  📂 正在分析: {directory}")
        
        python_files = list(dir_path.rglob("*.py"))
        
        # 先扫描所有函数定义位置
        for py_file in python_files:
            if any(skip in str(py_file) for skip in ['__pycache__', '.git', 'venv', 'test']):
                continue
            self._scan_functions(py_file)
        
        # 然后分析依赖关系
        for py_file in python_files:
            if any(skip in str(py_file) for skip in ['__pycache__', '.git', 'venv', 'test']):
                continue
            self.analyze_file(py_file)
        
        print(f"  ✅ 分析完成: {len(python_files)} 个文件")
        return self.graph

    def _scan_functions(self, file_path: Path):
        """扫描文件中的函数定义"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(content, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    self._function_locations[node.name] = str(file_path)
                elif isinstance(node, ast.ClassDef):
                    self._function_locations[node.name] = str(file_path)
        except:
            pass

    def analyze_file(self, file_path: Path) -> None:
        """分析单个文件"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(content, filename=str(file_path))
            
            # 统计文件信息
            self._analyze_file_statistics(file_path, content, tree)
            
            # 分析导入
            self._analyze_imports(file_path, tree)
            
            # 分析函数调用
            self._analyze_function_calls(file_path, tree)
            
            # 分析类继承
            self._analyze_inheritance(file_path, tree)
            
        except Exception as e:
            print(f"  ⚠️ 分析失败: {file_path}: {e}")

    def _analyze_file_statistics(self, file_path: Path, content: str, tree: ast.AST) -> None:
        """分析文件统计"""
        lines = content.split('\n')
        
        line_count = len(lines)
        empty_lines = sum(1 for line in lines if line.strip() == '')
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        code_lines = line_count - empty_lines - comment_lines
        
        function_count = 0
        class_count = 0
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                function_count += 1
            elif isinstance(node, ast.ClassDef):
                class_count += 1
        
        self.graph.file_statistics[str(file_path)] = {
            'lines': line_count,
            'code_lines': code_lines,
            'empty_lines': empty_lines,
            'comment_lines': comment_lines,
            'functions': function_count,
            'classes': class_count
        }

    def _analyze_imports(self, file_path: Path, tree: ast.AST) -> None:
        """分析导入语句"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for name in node.names:
                    self.graph.imports.append(ImportDependency(
                        source_file=str(file_path),
                        imported_module=name.name,
                        is_relative=False
                    ))
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ''
                imported_names = [n.name for n in node.names]
                self.graph.imports.append(ImportDependency(
                    source_file=str(file_path),
                    imported_module=module_name,
                    imported_names=imported_names,
                    is_relative=node.level > 0
                ))

    def _analyze_function_calls(self, file_path: Path, tree: ast.AST) -> None:
        """分析函数调用"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                # 简单函数调用
                callee_name = node.func.id
                caller_info = self._get_enclosing_function_name(node)
                
                if caller_info:
                    self.graph.function_calls.append(FunctionCall(
                        caller=caller_info,
                        callee=callee_name,
                        caller_file=str(file_path),
                        callee_file=self._function_locations.get(callee_name),
                        line=node.lineno
                    ))

    def _analyze_inheritance(self, file_path: Path, tree: ast.AST) -> None:
        """分析类继承"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                parent_classes = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        parent_classes.append(base.id)
                
                if parent_classes:
                    self.graph.inheritance.append(ClassInheritance(
                        class_name=node.name,
                        parent_classes=parent_classes,
                        file_path=str(file_path)
                    ))

    def _get_enclosing_function_name(self, node: ast.AST) -> Optional[str]:
        """获取包含节点的函数名"""
        current = node
        while current:
            if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return current.name
            if hasattr(current, 'parent'):
                current = current.parent
            else:
                break
        return None


class DependencyVisualizer:
    """依赖关系可视化"""

    @staticmethod
    def generate_summary(graph: CodeDependencyGraph) -> Dict:
        """生成依赖总结"""
        # 统计
        total_files = len(graph.file_statistics)
        total_functions = sum(s['functions'] for s in graph.file_statistics.values())
        total_classes = sum(s['classes'] for s in graph.file_statistics.values())
        total_lines = sum(s['lines'] for s in graph.file_statistics.values())
        
        # 导入统计
        import_count = len(graph.imports)
        top_modules = Counter(imp.imported_module for imp in graph.imports)
        
        # 函数调用统计
        call_count = len(graph.function_calls)
        
        # 继承统计
        inheritance_count = len(graph.inheritance)
        
        return {
            'files': total_files,
            'functions': total_functions,
            'classes': total_classes,
            'total_lines': total_lines,
            'imports': import_count,
            'function_calls': call_count,
            'inheritances': inheritance_count,
            'top_imported_modules': top_modules.most_common(10)
        }

    @staticmethod
    def print_report(graph: CodeDependencyGraph) -> None:
        """打印报告"""
        summary = DependencyVisualizer.generate_summary(graph)
        
        print("\n" + "=" * 80)
        print("  📊 代码依赖分析报告")
        print("=" * 80)
        
        print(f"\n  📁 文件统计:")
        print(f"    文件数: {summary['files']}")
        print(f"    函数数: {summary['functions']}")
        print(f"    类数: {summary['classes']}")
        print(f"    总代码行数: {summary['total_lines']:,}")
        
        print(f"\n  🔗 依赖关系:")
        print(f"    导入语句: {summary['imports']}")
        print(f"    函数调用: {summary['function_calls']}")
        print(f"    类继承: {summary['inheritances']}")
        
        if summary['top_imported_modules']:
            print(f"\n  📦 最常导入的模块:")
            for module, count in summary['top_imported_modules'][:5]:
                if module:
                    print(f"    {module}: {count} 次")
        
        print("\n" + "=" * 80)

    @staticmethod
    def find_circular_dependencies(graph: CodeDependencyGraph) -> List[List[str]]:
        """检测循环依赖"""
        # 构建模块依赖图
        module_deps = defaultdict(set)
        
        for imp in graph.imports:
            if imp.imported_module:
                module_deps[imp.source_file].add(imp.imported_module)
        
        # 简化版检测（实际需要更复杂的算法）
        return []


def analyze_dependencies(directory: str) -> Dict:
    """
    快捷函数：分析代码依赖
    
    Args:
        directory: 要分析的目录
    
    Returns:
        依赖分析结果
    """
    analyzer = CodeDependencyAnalyzer()
    graph = analyzer.analyze_directory(directory)
    
    visualizer = DependencyVisualizer()
    visualizer.print_report(graph)
    
    return visualizer.generate_summary(graph)
