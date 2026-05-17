"""
Code RAG v18.0 - 代码审查AI系统
智能代码审查、质量评估和优化建议
第一部分：基础审查引擎
"""

import re
import ast
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Severity(Enum):
    """问题严重程度"""
    CRITICAL = "critical"    # 严重，必须修复
    HIGH = "high"           # 高，应修复
    MEDIUM = "medium"       # 中，建议修复
    LOW = "low"             # 低，可以修复
    INFO = "info"           # 信息，建议改进


class IssueType(Enum):
    """问题类型"""
    COMPLEXITY = "complexity"              # 复杂度问题
    NAMING = "naming"                      # 命名问题
    DUPLICATION = "duplication"            # 代码重复
    SECURITY = "security"                   # 安全问题
    PERFORMANCE = "performance"             # 性能问题
    STYLE = "style"                        # 代码风格
    DOCUMENTATION = "documentation"        # 文档问题
    BEST_PRACTICE = "best_practice"        # 最佳实践


@dataclass
class CodeIssue:
    """代码问题"""
    issue_type: IssueType
    severity: Severity
    line_number: int
    message: str
    description: str
    suggestion: str
    code_snippet: str = ""


@dataclass
class ReviewReport:
    """审查报告"""
    file_path: str
    review_date: datetime
    total_lines: int
    issues: List[CodeIssue]
    metrics: Dict[str, Any] = field(default_factory=dict)
    summary: Dict[str, int] = field(default_factory=dict)


class ComplexityChecker:
    """复杂度检查器"""

    @staticmethod
    def calculate_complexity(code: str) -> int:
        """计算圈复杂度"""
        complexity = 1
        
        patterns = [
            r'\bif\b', r'\belse\b', r'\belif\b',
            r'\bfor\b', r'\bwhile\b',
            r'\band\b', r'\bor\b',
            r'\bexcept\b', r'\bcatch\b',
            r'\bcase\b', r'\bswitch\b',
        ]
        
        for pattern in patterns:
            complexity += len(re.findall(pattern, code))
        
        return complexity

    @staticmethod
    def check_function_complexity(function_node: ast.FunctionDef) -> Tuple[int, List[str]]:
        """检查函数复杂度"""
        complexity = ComplexityChecker.calculate_complexity(
            ast.unparse(function_node)
        )
        
        issues = []
        
        if complexity > 20:
            issues.append(f"函数 '{function_node.name}' 复杂度太高: {complexity}")
        
        return complexity, issues

    @staticmethod
    def check_function_length(function_node: ast.FunctionDef) -> List[str]:
        """检查函数长度"""
        issues = []
        
        line_count = function_node.end_lineno - function_node.lineno + 1
        
        if line_count > 100:
            issues.append(f"函数 '{function_node.name}' 太长: {line_count} 行 (建议 <100 行)")
        elif line_count > 50:
            issues.append(f"函数 '{function_node.name}' 较长: {line_count} 行 (建议 <50 行)")
        
        return issues


class NamingChecker:
    """命名规范检查器"""

    def __init__(self):
        self.bad_names = {
            'tmp', 'temp', 'temp1', 'temp2',
            'foo', 'bar', 'baz', 'qux',
            'data', 'info', 'item', 'obj',
            'x', 'y', 'z', 'a', 'b', 'c'
        }
        
        self.bad_patterns = [
            (r'^[a-z]+$', '函数名应使用 snake_case 或 CamelCase'),
            (r'[A-Z]+', '常量应使用 UPPER_CASE'),
            (r'^_$', '变量名不能是单个下划线'),
            (r'__.*__$', '双下划线开头和结尾的名字是保留的'),
        ]

    def check_function_name(self, name: str) -> List[str]:
        """检查函数命名"""
        issues = []
        
        if name in self.bad_names:
            issues.append(f"函数名 '{name}' 太通用，应使用更有描述性的名称")
        
        if name.isupper():
            issues.append(f"函数名 '{name}' 不应全部大写 (常量除外)")
        
        return issues

    def check_variable_name(self, name: str) -> List[str]:
        """检查变量命名"""
        issues = []
        
        if len(name) == 1 and name.isalpha():
            issues.append(f"变量名 '{name}' 太短，应使用有意义的名称")
        
        if name in self.bad_names:
            issues.append(f"变量名 '{name}' 太通用")
        
        return issues

    def check_class_name(self, name: str) -> List[str]:
        """检查类命名"""
        issues = []
        
        if name[0].islower():
            issues.append(f"类名 '{name}' 应使用 CamelCase")
        
        if name.endswith('Manager') or name.endswith('Handler'):
            if len(name) < 10:
                issues.append(f"类名 '{name}' 过于通用，考虑更具体的名称")
        
        return issues


class DuplicationChecker:
    """代码重复检查器"""

    def __init__(self, min_length: int = 5):
        self.min_length = min_length

    def find_duplications(self, code_lines: List[str]) -> List[Dict]:
        """查找重复代码"""
        duplications = []
        
        code_normalized = [
            line.strip() for line in code_lines
            if line.strip() and not line.strip().startswith('#')
        ]
        
        for i, line1 in enumerate(code_normalized):
            for j, line2 in enumerate(code_normalized[i+1:], i+1):
                if self._are_similar(line1, line2):
                    duplications.append({
                        'line1': i,
                        'line2': j,
                        'code': line1[:50],
                        'similarity': self._calculate_similarity(line1, line2)
                    })
        
        return duplications

    def _are_similar(self, line1: str, line2: str) -> bool:
        """判断两行代码是否相似"""
        if len(line1) < self.min_length or len(line2) < self.min_length:
            return False
        
        similarity = self._calculate_similarity(line1, line2)
        return similarity > 0.8

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """计算相似度"""
        str1_lower = str1.lower()
        str2_lower = str2.lower()
        
        if str1_lower == str2_lower:
            return 1.0
        
        common_chars = set(str1_lower) & set(str2_lower)
        total_chars = set(str1_lower) | set(str2_lower)
        
        if not total_chars:
            return 0.0
        
        return len(common_chars) / len(total_chars)


class SecurityChecker:
    """安全检查器"""

    def __init__(self):
        self.dangerous_patterns = {
            'eval': (r'\beval\s*\(', '使用 eval() 可能导致代码注入'),
            'exec': (r'\bexec\s*\(', '使用 exec() 可能导致代码注入'),
            'pickle': (r'\bpickle\.loads?\s*\(', 'pickle 反序列化存在安全风险'),
            'hardcoded_password': (r'(password|passwd|pwd)\s*=\s*["\'][^"\']{1,20}["\']', '硬编码密码'),
            'sql_injection': (r'".*%s.*".*%s.*%\s*%\s*\(', 'SQL注入风险：使用字符串格式化'),
            'secret_key': (r'(secret|token|api_key)\s*=\s*["\'][^"\']{8,}["\']', '可能存在密钥泄露'),
        }

    def check_security(self, code: str, file_path: str) -> List[CodeIssue]:
        """检查安全漏洞"""
        issues = []
        
        for pattern_name, (pattern, message) in self.dangerous_patterns.items():
            matches = re.finditer(pattern, code, re.IGNORECASE)
            for match in matches:
                line_number = code[:match.start()].count('\n') + 1
                
                severity = Severity.CRITICAL if pattern_name in [
                    'eval', 'exec', 'pickle', 'sql_injection'
                ] else Severity.HIGH
                
                issues.append(CodeIssue(
                    issue_type=IssueType.SECURITY,
                    severity=severity,
                    line_number=line_number,
                    message=f"安全风险: {message}",
                    description=f"在第 {line_number} 行发现潜在安全问题",
                    suggestion=f"考虑使用更安全的替代方案",
                    code_snippet=code.split('\n')[line_number-1] if line_number <= len(code.split('\n')) else ""
                ))
        
        return issues


class StyleChecker:
    """代码风格检查器"""

    def __init__(self):
        self.max_line_length = 120

    def check_line_length(self, code: str) -> List[CodeIssue]:
        """检查行长度"""
        issues = []
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > self.max_line_length:
                issues.append(CodeIssue(
                    issue_type=IssueType.STYLE,
                    severity=Severity.LOW,
                    line_number=i,
                    message=f"行过长: {len(line)} 字符",
                    description=f"建议不超过 {self.max_line_length} 字符",
                    suggestion="考虑拆分或使用变量",
                    code_snippet=line[:80] + "..." if len(line) > 80 else line
                ))
        
        return issues

    def check_trailing_whitespace(self, code: str) -> List[CodeIssue]:
        """检查尾随空格"""
        issues = []
        
        lines = code.split('\n')
        for i, line in enumerate(lines, 1):
            if line.rstrip() != line.rstrip('\n'):
                issues.append(CodeIssue(
                    issue_type=IssueType.STYLE,
                    severity=Severity.INFO,
                    line_number=i,
                    message="尾随空格",
                    description="行尾存在多余空格",
                    suggestion="移除尾随空格",
                    code_snippet=line
                ))
        
        return issues


class CodeReviewer:
    """代码审查主类"""

    def __init__(self):
        self.complexity_checker = ComplexityChecker()
        self.naming_checker = NamingChecker()
        self.duplication_checker = DuplicationChecker()
        self.security_checker = SecurityChecker()
        self.style_checker = StyleChecker()

    def review_file(self, file_path: str, code: str) -> ReviewReport:
        """审查文件"""
        issues = []
        
        lines = code.split('\n')
        total_lines = len(lines)
        
        issues.extend(self.style_checker.check_line_length(code))
        issues.extend(self.style_checker.check_trailing_whitespace(code))
        issues.extend(self.security_checker.check_security(code, file_path))
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    complexity, complexity_issues = self.complexity_checker.check_function_complexity(node)
                    for issue_msg in complexity_issues:
                        issues.append(CodeIssue(
                            issue_type=IssueType.COMPLEXITY,
                            severity=Severity.HIGH,
                            line_number=node.lineno,
                            message=issue_msg,
                            description=f"圈复杂度: {complexity}",
                            suggestion="考虑拆分函数"
                        ))
                    
                    for issue_msg in self.complexity_checker.check_function_length(node):
                        issues.append(CodeIssue(
                            issue_type=IssueType.COMPLEXITY,
                            severity=Severity.MEDIUM,
                            line_number=node.lineno,
                            message=issue_msg,
                            description="函数长度检查",
                            suggestion="考虑拆分为更小的函数"
                        ))
                    
                    for issue_msg in self.naming_checker.check_function_name(node.name):
                        issues.append(CodeIssue(
                            issue_type=IssueType.NAMING,
                            severity=Severity.LOW,
                            line_number=node.lineno,
                            message=issue_msg,
                            description="函数命名检查",
                            suggestion="使用描述性名称"
                        ))
                
                elif isinstance(node, ast.ClassDef):
                    for issue_msg in self.naming_checker.check_class_name(node.name):
                        issues.append(CodeIssue(
                            issue_type=IssueType.NAMING,
                            severity=Severity.LOW,
                            line_number=node.lineno,
                            message=issue_msg,
                            description="类命名检查",
                            suggestion="使用描述性名称"
                        ))
        
        except SyntaxError as e:
            issues.append(CodeIssue(
                issue_type=IssueType.STYLE,
                severity=Severity.CRITICAL,
                line_number=e.lineno or 0,
                message=f"语法错误: {e.msg}",
                description="代码存在语法错误",
                suggestion="修复语法错误",
                code_snippet=""
            ))
        
        severity_counts = {}
        for issue in issues:
            severity_name = issue.severity.value
            severity_counts[severity_name] = severity_counts.get(severity_name, 0) + 1
        
        report = ReviewReport(
            file_path=file_path,
            review_date=datetime.now(),
            total_lines=total_lines,
            issues=issues,
            metrics={
                'total_lines': total_lines,
                'issue_count': len(issues),
                'critical_count': severity_counts.get('critical', 0),
                'high_count': severity_counts.get('high', 0),
            },
            summary=severity_counts
        )
        
        return report

    def review_directory(self, directory: str) -> List[ReviewReport]:
        """审查目录"""
        from pathlib import Path
        
        reports = []
        dir_path = Path(directory)
        
        for py_file in dir_path.rglob("*.py"):
            if any(skip in str(py_file) for skip in ['__pycache__', '.git', 'venv', 'test']):
                continue
            
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                
                report = self.review_file(str(py_file), code)
                reports.append(report)
            except Exception as e:
                print(f"审查文件 {py_file} 时出错: {e}")
        
        return reports


def create_code_reviewer() -> CodeReviewer:
    """创建代码审查器"""
    return CodeReviewer()
