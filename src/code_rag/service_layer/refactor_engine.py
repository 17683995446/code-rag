"""
Code RAG v21.0 - 自动重构引擎
基于代码理解的智能重构建议
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class RefactorType(Enum):
    """重构类型"""
    RENAME = "rename"
    EXTRACT_METHOD = "extract_method"
    INLINE_VARIABLE = "inline_variable"
    INTRODUCE_PARAMETER = "introduce_parameter"
    EXTRACT_INTERFACE = "extract_interface"
    REMOVE_DEAD_CODE = "remove_dead_code"
    ADD_TYPE_HINTS = "add_type_hints"
    IMPROVE_NAMING = "improve_naming"
    SIMPLIFY_CONDITION = "simplify_condition"
    OPTIMIZE_IMPORTS = "optimize_imports"


class Complexity(Enum):
    """复杂度级别"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class CodeIssue:
    """代码问题"""
    issue_type: str
    message: str
    line: int
    severity: str = "warning"
    suggestion: str = ""


@dataclass
class RefactorSuggestion:
    """重构建议"""
    refactor_type: RefactorType
    title: str
    description: str
    original_code: str
    suggested_code: str
    benefits: List[str] = field(default_factory=list)
    impact: str = "low"
    automated: bool = False


@dataclass
class ComplexityMetrics:
    """复杂度指标"""
    cyclomatic_complexity: int = 0
    lines_of_code: int = 0
    function_count: int = 0
    class_count: int = 0
    depth: int = 0
    parameter_count: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "cyclomatic_complexity": self.cyclomatic_complexity,
            "lines_of_code": self.lines_of_code,
            "function_count": self.function_count,
            "class_count": self.class_count,
            "depth": self.depth,
            "parameter_count": self.parameter_count
        }


class PatternDetector:
    """代码模式检测器"""
    
    def __init__(self):
        self.patterns = self._load_patterns()
    
    def _load_patterns(self) -> Dict:
        """加载检测模式"""
        return {
            "long_function": {
                "pattern": r"def \w+\(.*\):",
                "threshold": 50,
                "issue_type": "function_length"
            },
            "deep_nesting": {
                "pattern": r"(?:if|for|while).*:",
                "threshold": 4,
                "issue_type": "nesting_depth"
            },
            "long_lines": {
                "pattern": r".{121,}",
                "threshold": 120,
                "issue_type": "line_length"
            }
        }
    
    def detect_issues(self, code: str) -> List[CodeIssue]:
        """检测代码问题"""
        issues = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            # 长函数
            if 'def ' in line:
                func_lines = self._count_function_lines(code, line_num)
                if func_lines > self.patterns["long_function"]["threshold"]:
                    issues.append(CodeIssue(
                        issue_type="long_function",
                        message=f"Function exceeds {self.patterns['long_function']['threshold']} lines",
                        line=line_num,
                        severity="warning",
                        suggestion="Consider extracting smaller functions"
                    ))
            
            # 长行
            if len(line) > self.patterns["long_lines"]["threshold"]:
                issues.append(CodeIssue(
                    issue_type="long_line",
                    message=f"Line exceeds {self.patterns['long_lines']['threshold']} characters",
                    line=line_num,
                    severity="info"
                ))
            
            # 深度嵌套
            if line.strip().startswith(('if ', 'for ', 'while ')):
                indent = len(line) - len(line.lstrip())
                if indent > 16:
                    issues.append(CodeIssue(
                        issue_type="deep_nesting",
                        message="Deep nesting detected",
                        line=line_num,
                        severity="warning"
                    ))
        
        return issues
    
    def _count_function_lines(self, code: str, start_line: int) -> int:
        """计算函数行数"""
        lines = code.split('\n')
        if start_line > len(lines):
            return 0
        
        indent = len(lines[start_line - 1]) - len(lines[start_line - 1].lstrip())
        count = 0
        
        for i in range(start_line, len(lines)):
            line = lines[i]
            if line.strip() == '':
                count += 1
                continue
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indent and line.strip():
                break
            count += 1
        
        return count


class RefactorEngine:
    """重构引擎"""
    
    def __init__(self):
        self.pattern_detector = PatternDetector()
        self.refactor_templates = self._load_templates()
    
    def _load_templates(self) -> Dict:
        """加载重构模板"""
        return {
            "add_type_hints": {
                "description": "Add type hints to function parameters and return values",
                "examples": {
                    "python": "def func(param: int) -> str: ..."
                }
            },
            "rename_variables": {
                "description": "Rename variables to be more descriptive",
                "patterns": [
                    (r'\bx\b', 'x', 'value'),
                    (r'\btmp\b', 'tmp', 'temporary'),
                ]
            },
            "extract_method": {
                "description": "Extract repeated code into a function"
            }
        }
    
    def analyze_complexity(self, code: str) -> ComplexityMetrics:
        """分析代码复杂度"""
        metrics = ComplexityMetrics()
        
        lines = code.split('\n')
        metrics.lines_of_code = len([l for l in lines if l.strip()])
        
        # 计算圈复杂度（简化版）
        complexity_keywords = ['if', 'elif', 'for', 'while', 'and', 'or', 'except']
        for line in lines:
            stripped = line.strip()
            if any(stripped.startswith(kw) for kw in complexity_keywords):
                metrics.cyclomatic_complexity += 1
        
        # 统计函数和类
        for line in lines:
            if re.match(r'def \w+\(', line):
                metrics.function_count += 1
            elif re.match(r'class \w+', line):
                metrics.class_count += 1
        
        return metrics
    
    def suggest_refactors(self, code: str, language: str = "python") -> List[RefactorSuggestion]:
        """建议重构"""
        suggestions = []
        
        issues = self.pattern_detector.detect_issues(code)
        metrics = self.analyze_complexity(code)
        
        # 基于问题的建议
        for issue in issues:
            if issue.issue_type == "long_function":
                suggestions.append(RefactorSuggestion(
                    refactor_type=RefactorType.EXTRACT_METHOD,
                    title="Extract long function",
                    description=f"Function at line {issue.line} is too long",
                    original_code=f"def long_function(): ...",
                    suggested_code="def short_function(): ...",
                    benefits=["Improved readability", "Better testability", "Easier maintenance"],
                    impact="medium",
                    automated=False
                ))
            elif issue.issue_type == "long_line":
                suggestions.append(RefactorSuggestion(
                    refactor_type=RefactorType.RENAME,
                    title="Break long line",
                    description=f"Line {issue.line} exceeds 120 characters",
                    original_code="long_line = 'very_long_string_that_exceeds_the_limit'",
                    suggested_code="long_line = 'very_long_string_that_exceeds_the_limit'",
                    benefits=["Improved readability", "Easier to read in editors"],
                    impact="low",
                    automated=False
                ))
        
        # 基于复杂度的建议
        if metrics.cyclomatic_complexity > 10:
            suggestions.append(RefactorSuggestion(
                refactor_type=RefactorType.SIMPLIFY_CONDITION,
                title="Reduce complexity",
                description=f"Cyclomatic complexity is {metrics.cyclomatic_complexity}",
                original_code="if condition1 and condition2 or condition3: ...",
                suggested_code="if is_valid(): ...",
                benefits=["Better maintainability", "Easier testing", "Reduced bug risk"],
                impact="high",
                automated=False
            ))
        
        # 命名改进建议
        if language == "python":
            suggestions.append(RefactorSuggestion(
                refactor_type=RefactorType.ADD_TYPE_HINTS,
                title="Add type hints",
                description="Function parameters lack type hints",
                original_code="def func(param1, param2): ...",
                suggested_code="def func(param1: int, param2: str) -> bool: ...",
                benefits=["Better IDE support", "Type checking", "Documentation"],
                impact="low",
                automated=True
            ))
        
        return suggestions
    
    def generate_report(self, code: str, language: str = "python") -> Dict:
        """生成重构报告"""
        issues = self.pattern_detector.detect_issues(code)
        metrics = self.analyze_complexity(code)
        suggestions = self.suggest_refactors(code, language)
        
        return {
            "summary": {
                "total_issues": len(issues),
                "total_suggestions": len(suggestions),
                "complexity_metrics": metrics.to_dict()
            },
            "issues": [
                {
                    "type": i.issue_type,
                    "message": i.message,
                    "line": i.line,
                    "severity": i.severity
                }
                for i in issues
            ],
            "suggestions": [
                {
                    "type": s.refactor_type.value,
                    "title": s.title,
                    "description": s.description,
                    "impact": s.impact,
                    "automated": s.automated
                }
                for s in suggestions
            ]
        }


def create_refactor_engine() -> RefactorEngine:
    """创建重构引擎"""
    return RefactorEngine()
