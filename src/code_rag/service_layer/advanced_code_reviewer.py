"""
Code RAG v18.0 - 代码审查AI系统（高级功能）
第二部分：性能审查和最佳实践检查
"""

import re
import ast
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from .code_reviewer import (
    CodeIssue,
    IssueType,
    Severity,
    CodeReviewer as BaseReviewer
)


class PerformanceChecker:
    """性能检查器"""

    def __init__(self):
        self.inefficient_patterns = {
            'nested_loops': (r'for\s+.*:\s*\n.*for\s+.*:', '嵌套循环可能导致性能问题'),
            'repeated_regex': (r'(re\.compile.*\n.*for.*in.*)', '循环中重复编译正则表达式'),
            'list_comprehension': (r'\[.*for.*for.*\]', '多层列表推导式'),
            'string_concat': (r'\+\s*["\']', '字符串拼接使用 + 可能效率低'),
        }

    def check_performance(self, code: str) -> List[CodeIssue]:
        """检查性能问题"""
        issues = []
        
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            if 'for' in line:
                for j in range(i, min(i + 10, len(lines))):
                    if j > i and 'for' in lines[j]:
                        issues.append(CodeIssue(
                            issue_type=IssueType.PERFORMANCE,
                            severity=Severity.MEDIUM,
                            line_number=i,
                            message="嵌套循环检测",
                            description=f"第 {i} 行和第 {j} 行存在嵌套循环",
                            suggestion="考虑使用向量化操作或优化算法",
                            code_snippet=lines[i-1][:50]
                        ))
                        break
        
        for pattern_name, (pattern, message) in self.inefficient_patterns.items():
            if pattern_name != 'nested_loops':
                matches = re.finditer(pattern, code, re.MULTILINE)
                for match in matches:
                    line_number = code[:match.start()].count('\n') + 1
                    issues.append(CodeIssue(
                        issue_type=IssueType.PERFORMANCE,
                        severity=Severity.LOW,
                        line_number=line_number,
                        message=f"性能建议: {message}",
                        description=f"第 {line_number} 行可能存在性能问题",
                        suggestion="考虑使用更高效的实现方式",
                        code_snippet=code.split('\n')[line_number-1][:50]
                    ))
        
        return issues

    def check_database_queries(self, code: str) -> List[CodeIssue]:
        """检查数据库查询"""
        issues = []
        
        query_patterns = [
            (r'\.query\(', '数据库查询'),
            (r'\.filter\(', '数据库过滤'),
            (r'\.all\(\)', '获取所有记录'),
            (r'SELECT\s+\*', 'SELECT * 查询'),
        ]
        
        for pattern, name in query_patterns:
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_number = code[:match.start()].count('\n') + 1
                
                if 'SELECT *' in match.group().upper():
                    issues.append(CodeIssue(
                        issue_type=IssueType.PERFORMANCE,
                        severity=Severity.MEDIUM,
                        line_number=line_number,
                        message="SELECT * 查询",
                        description="使用 SELECT * 可能返回不必要的数据",
                        suggestion="明确指定需要的字段",
                        code_snippet=code.split('\n')[line_number-1][:60]
                    ))
                
                if 'all()' in match.group():
                    issues.append(CodeIssue(
                        issue_type=IssueType.PERFORMANCE,
                        severity=Severity.LOW,
                        line_number=line_number,
                        message="获取所有记录",
                        description="使用 all() 可能返回大量数据",
                        suggestion="考虑使用分页或限制返回数量",
                        code_snippet=code.split('\n')[line_number-1][:60]
                    ))
        
        return issues

    def check_memory_usage(self, code: str) -> List[CodeIssue]:
        """检查内存使用"""
        issues = []
        
        patterns = [
            (r'\.read\(\)', '读取整个文件到内存'),
            (r'\.loadAll\(', '加载所有数据到内存'),
            (r'list\(.*\.keys\(\)\)', '将所有键转换为列表'),
        ]
        
        for pattern, message in patterns:
            matches = re.finditer(pattern, code)
            for match in matches:
                line_number = code[:match.start()].count('\n') + 1
                issues.append(CodeIssue(
                    issue_type=IssueType.PERFORMANCE,
                    severity=Severity.LOW,
                    line_number=line_number,
                    message=f"内存使用: {message}",
                    description=f"第 {line_number} 行可能存在内存使用问题",
                    suggestion="考虑使用生成器或流式处理",
                    code_snippet=code.split('\n')[line_number-1][:60]
                ))
        
        return issues


class BestPracticeChecker:
    """最佳实践检查器"""

    def __init__(self):
        self.python_best_practices = {
            'context_manager': r'with\s+.*:\s*\n',
            'type_hints': r'def\s+\w+\([^)]*\)\s*->',
            'docstring': r'def\s+\w+\([^)]*\):\s*\n\s+"""',
            'exception_specific': r'except\s+Exception\s+as\s+\w+:',
            'logging': r'logger\s*=.*logging\.getLogger',
        }

    def check_best_practices(self, code: str) -> List[CodeIssue]:
        """检查最佳实践"""
        issues = []
        
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            if line.strip().startswith('except:'):
                issues.append(CodeIssue(
                    issue_type=IssueType.BEST_PRACTICE,
                    severity=Severity.MEDIUM,
                    line_number=i,
                    message="捕获所有异常",
                    description="捕获所有异常可能隐藏真实问题",
                    suggestion="考虑捕获特定异常类型",
                    code_snippet=line
                ))
        
        for pattern_name, pattern in self.python_best_practices.items():
            matches = re.finditer(pattern, code)
            for match in matches:
                line_number = code[:match.start()].count('\n') + 1
                
                if pattern_name == 'type_hints' and not match.group().endswith('->'):
                    issues.append(CodeIssue(
                        issue_type=IssueType.BEST_PRACTICE,
                        severity=Severity.LOW,
                        line_number=line_number,
                        message="缺少类型提示",
                        description="函数缺少返回类型提示",
                        suggestion="添加类型提示以提高代码可读性",
                        code_snippet=code.split('\n')[line_number-1][:60]
                    ))
                
                if pattern_name == 'logging' and 'logger' not in code[:match.start()]:
                    issues.append(CodeIssue(
                        issue_type=IssueType.BEST_PRACTICE,
                        severity=Severity.LOW,
                        line_number=line_number,
                        message="缺少日志记录",
                        description="建议使用日志记录而不是 print",
                        suggestion="使用 logging 模块记录日志",
                        code_snippet=code.split('\n')[line_number-1][:60]
                    ))
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    has_docstring = ast.get_docstring(node) is not None
                    
                    if not has_docstring and len(code.split('\n')) > 10:
                        issues.append(CodeIssue(
                            issue_type=IssueType.BEST_PRACTICE,
                            severity=Severity.LOW,
                            line_number=node.lineno,
                            message="缺少文档字符串",
                            description=f"函数 '{node.name}' 缺少文档字符串",
                            suggestion="添加文档字符串说明函数用途",
                            code_snippet=code.split('\n')[node.lineno-1][:60]
                        ))
        except:
            pass
        
        return issues

    def check_design_patterns(self, code: str) -> List[CodeIssue]:
        """检查设计模式应用"""
        issues = []
        
        patterns = {
            'singleton': r'class\s+\w+:.*_instance\s*=\s*None',
            'factory': r'class\s+\w+Factory',
            'observer': r'class\s+\w+Observer',
        }
        
        for pattern_name, pattern in patterns.items():
            if re.search(pattern, code, re.DOTALL):
                issues.append(CodeIssue(
                    issue_type=IssueType.BEST_PRACTICE,
                    severity=Severity.INFO,
                    line_number=0,
                    message=f"设计模式: {pattern_name}",
                    description=f"检测到 {pattern_name} 设计模式",
                    suggestion="确保正确实现设计模式",
                    code_snippet=""
                ))
        
        return issues

    def check_error_handling(self, code: str) -> List[CodeIssue]:
        """检查错误处理"""
        issues = []
        
        patterns = [
            (r'pass\s*$', '空的 except 代码块'),
            (r'raise\s+NotImplemented', 'NotImplementedError 被抛出'),
        ]
        
        for pattern, message in patterns:
            matches = re.finditer(pattern, code, re.MULTILINE)
            for match in matches:
                line_number = code[:match.start()].count('\n') + 1
                
                issues.append(CodeIssue(
                    issue_type=IssueType.BEST_PRACTICE,
                    severity=Severity.MEDIUM,
                    line_number=line_number,
                    message=f"错误处理: {message}",
                    description=f"第 {line_number} 行",
                    suggestion="添加适当的错误处理逻辑",
                    code_snippet=code.split('\n')[line_number-1]
                ))
        
        return issues


class AdvancedCodeReviewer(BaseReviewer):
    """高级代码审查器"""

    def __init__(self):
        super().__init__()
        self.performance_checker = PerformanceChecker()
        self.best_practice_checker = BestPracticeChecker()

    def review_file_advanced(self, file_path: str, code: str) -> List[CodeIssue]:
        """高级文件审查"""
        all_issues = []
        
        all_issues.extend(self.performance_checker.check_performance(code))
        all_issues.extend(self.performance_checker.check_database_queries(code))
        all_issues.extend(self.performance_checker.check_memory_usage(code))
        
        all_issues.extend(self.best_practice_checker.check_best_practices(code))
        all_issues.extend(self.best_practice_checker.check_design_patterns(code))
        all_issues.extend(self.best_practice_checker.check_error_handling(code))
        
        return all_issues


def create_advanced_reviewer() -> AdvancedCodeReviewer:
    """创建高级审查器"""
    return AdvancedCodeReviewer()
