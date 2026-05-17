"""
Code RAG v18.0 - 增强问答引擎
智能问答、Bug诊断、代码解释
第一部分：基础问答功能
"""

import ast
import re
from typing import List, Dict, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class QAResponse:
    """问答响应"""
    answer: str
    confidence: float
    related_code: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CodeExplanation:
    """代码解释"""
    summary: str
    line_by_line: List[Dict[str, str]] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    complexity: str = ""
    suggestions: List[str] = field(default_factory=list)


@dataclass
class BugAnalysis:
    """Bug分析"""
    bug_type: str
    severity: str
    location: str
    cause: str
    suggestion: str
    fixed_code: Optional[str] = None


class CodeExplainer:
    """代码解释器"""

    def explain_code(self, code: str) -> CodeExplanation:
        """解释代码"""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return CodeExplanation(
                summary="代码存在语法错误，无法解析",
                line_by_line=[],
                dependencies=[],
                complexity="ERROR"
            )

        summary = self._generate_summary(tree, code)
        line_explanations = self._explain_lines(code)
        dependencies = self._find_dependencies(tree)
        complexity = self._assess_complexity(tree, code)

        return CodeExplanation(
            summary=summary,
            line_by_line=line_explanations,
            dependencies=dependencies,
            complexity=complexity,
            suggestions=self._generate_suggestions(tree, code)
        )

    def _generate_summary(self, tree: ast.AST, code: str) -> str:
        """生成摘要"""
        functions = []
        classes = []
        imports = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    imports.append(node.module or 'unknown')

        summary_parts = []

        if classes:
            summary_parts.append(f"定义了 {len(classes)} 个类: {', '.join(classes[:3])}")
        if functions:
            summary_parts.append(f"包含 {len(functions)} 个函数: {', '.join(functions[:5])}")
        if imports:
            summary_parts.append(f"导入了 {len(set(imports))} 个模块")

        return '; '.join(summary_parts) if summary_parts else "空代码模块"

    def _explain_lines(self, code: str) -> List[Dict[str, str]]:
        """逐行解释"""
        lines = code.split('\n')
        explanations = []

        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            explanation = self._explain_single_line(line)
            if explanation:
                explanations.append({
                    'line': i,
                    'code': line,
                    'explanation': explanation
                })

        return explanations[:20]

    def _explain_single_line(self, line: str) -> str:
        """解释单行代码"""
        if line.startswith('def '):
            match = re.match(r'def (\w+)\((.*?)\):', line)
            if match:
                name, params = match.groups()
                return f"定义函数 '{name}'，参数: {params or '无'}"

        elif line.startswith('class '):
            match = re.match(r'class (\w+)(.*?):', line)
            if match:
                name, bases = match.groups()
                return f"定义类 '{name}'" + (f"，继承自 {bases}" if bases else "")

        elif 'import ' in line:
            return f"导入模块: {line.split('import ')[-1].strip()}"

        elif line.startswith('return '):
            return f"返回: {line[7:].strip()}"

        elif line.startswith('if '):
            return f"条件判断: {line[3:].strip()}"

        elif line.startswith('for '):
            return f"循环遍历: {line[4:].strip()}"

        elif line.startswith('@'):
            return f"装饰器: {line[1:].strip()}"

        elif '=' in line and not line.startswith('if '):
            return f"赋值: {line.strip()}"

        return ""

    def _find_dependencies(self, tree: ast.AST) -> List[str]:
        """查找依赖"""
        dependencies = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.add(node.module)

        return sorted(list(dependencies))[:10]

    def _assess_complexity(self, tree: ast.AST, code: str) -> str:
        """评估复杂度"""
        lines = len(code.split('\n'))
        functions = sum(1 for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))
        classes = sum(1 for node in ast.walk(tree) if isinstance(node, ast.ClassDef))

        if lines > 200 or functions > 10:
            return "HIGH"
        elif lines > 100 or functions > 5:
            return "MEDIUM"
        else:
            return "LOW"

    def _generate_suggestions(self, tree: ast.AST, code: str) -> List[str]:
        """生成建议"""
        suggestions = []

        if not any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree)):
            suggestions.append("考虑添加文档字符串")

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not ast.get_docstring(node):
                suggestions.append(f"函数 '{node.name}' 缺少文档字符串")
                break

        if 'except:' in code:
            suggestions.append("考虑使用更具体的异常类型")

        if 'print(' in code:
            suggestions.append("考虑使用 logging 模块代替 print")

        return suggestions[:3]


class BugDiagnoser:
    """Bug诊断器"""

    def __init__(self):
        self.common_errors = {
            'NameError': {
                'pattern': r"NameError.*'(\w+)'",
                'cause': "变量未定义或未导入",
                'suggestion': "检查变量名拼写，确保已导入相关模块"
            },
            'TypeError': {
                'pattern': r"TypeError.*",
                'cause': "类型不匹配",
                'suggestion': "检查变量类型，使用类型转换或调整逻辑"
            },
            'AttributeError': {
                'pattern': r"AttributeError.*'(\w+)'",
                'cause': "对象没有该属性",
                'suggestion': "检查对象类型，确保属性存在"
            },
            'IndexError': {
                'pattern': r"IndexError.*list index out of range",
                'cause': "列表索引超出范围",
                'suggestion': "添加边界检查或使用异常处理"
            },
            'KeyError': {
                'pattern': r"KeyError.*'(\w+)'",
                'cause': "字典键不存在",
                'suggestion': "使用 dict.get() 或先检查键是否存在"
            },
            'SyntaxError': {
                'pattern': r"SyntaxError.*",
                'cause': "语法错误",
                'suggestion': "检查代码语法，确保括号、引号等配对正确"
            },
            'IndentationError': {
                'pattern': r"IndentationError.*",
                'cause': "缩进错误",
                'suggestion': "使用一致的缩进（4个空格）"
            }
        }

    def diagnose(self, error_message: str, code: str = "") -> BugAnalysis:
        """诊断Bug"""
        for error_type, info in self.common_errors.items():
            if error_type in error_message:
                pattern = info['pattern']
                match = re.search(pattern, error_message)
                
                if match:
                    groups = match.groups()
                    details = groups[0] if groups else ""
                else:
                    details = ""
                
                return BugAnalysis(
                    bug_type=error_type,
                    severity=self._assess_severity(error_type),
                    location=self._find_location(error_message, code),
                    cause=info['cause'],
                    suggestion=info['suggestion'],
                    fixed_code=self._suggest_fix(error_type, details, code)
                )

        return BugAnalysis(
            bug_type="Unknown",
            severity="MEDIUM",
            location="Unknown",
            cause="未知错误",
            suggestion="请提供更多信息或完整的错误信息"
        )

    def _assess_severity(self, error_type: str) -> str:
        """评估严重程度"""
        severity_map = {
            'SyntaxError': 'HIGH',
            'IndentationError': 'HIGH',
            'NameError': 'MEDIUM',
            'TypeError': 'MEDIUM',
            'AttributeError': 'MEDIUM',
            'IndexError': 'LOW',
            'KeyError': 'LOW'
        }
        return severity_map.get(error_type, 'MEDIUM')

    def _find_location(self, error_message: str, code: str) -> str:
        """查找位置"""
        line_match = re.search(r'line (\d+)', error_message)
        if line_match:
            return f"第 {line_match.group(1)} 行"
        return "位置未知"

    def _suggest_fix(self, error_type: str, details: str, code: str) -> Optional[str]:
        """建议修复"""
        fixes = {
            'NameError': f"# 确保变量 '{details}' 已定义\n# 或者导入相关模块\n{code}",
            'IndexError': "# 添加边界检查\nif index < len(list):\n    item = list[index]",
            'KeyError': "# 使用 dict.get() 提供默认值\nvalue = my_dict.get('key', 'default')",
            'TypeError': "# 检查变量类型，必要时进行类型转换"
        }
        return fixes.get(error_type)


class EnhancedQAEngine:
    """增强问答引擎"""

    def __init__(self):
        self.code_explainer = CodeExplainer()
        self.bug_diagnoser = BugDiagnoser()

    def ask(self, question: str, context: Optional[str] = None) -> QAResponse:
        """问答"""
        question_lower = question.lower()

        if any(keyword in question_lower for keyword in ['解释', 'explain', '什么是', '这个函数']):
            return self._handle_explanation(question, context)

        elif any(keyword in question_lower for keyword in ['bug', '错误', '报错', '出错了']):
            return self._handle_bug_diagnosis(question, context)

        elif any(keyword in question_lower for keyword in ['怎么', '如何', 'how to', 'how do']):
            return self._handle_howto(question)

        elif any(keyword in question_lower for keyword in ['为什么', 'why', '原因']):
            return self._handle_why(question)

        else:
            return self._handle_general(question)

    def _handle_explanation(self, question: str, context: Optional[str]) -> QAResponse:
        """处理解释请求"""
        if not context:
            return QAResponse(
                answer="请提供要解释的代码，我可以帮你详细分析。",
                confidence=1.0,
                suggestions=["提供代码片段", "提供文件路径"]
            )

        explanation = self.code_explainer.explain_code(context)

        answer_parts = [f"代码摘要: {explanation.summary}\n"]
        answer_parts.append(f"复杂度: {explanation.complexity}\n")

        if explanation.line_by_line:
            answer_parts.append("\n逐行解释:")
            for item in explanation.line_by_line[:5]:
                answer_parts.append(f"  第{item['line']}行: {item['explanation']}")

        if explanation.suggestions:
            answer_parts.append("\n建议:")
            for suggestion in explanation.suggestions:
                answer_parts.append(f"  • {suggestion}")

        return QAResponse(
            answer=''.join(answer_parts),
            confidence=0.9,
            related_code=[context[:200]] if context else [],
            suggestions=["需要更详细的解释吗？", "要我检查代码质量吗？"]
        )

    def _handle_bug_diagnosis(self, question: str, context: Optional[str]) -> QAResponse:
        """处理Bug诊断"""
        if not context:
            return QAResponse(
                answer="请提供错误信息或相关代码，我可以帮你诊断问题。",
                confidence=1.0,
                suggestions=["粘贴完整的错误信息", "提供出错的代码"]
            )

        diagnosis = self.bug_diagnoser.diagnose(context, "")

        answer_parts = [
            f"🔍 Bug类型: {diagnosis.bug_type}\n",
            f"⚠️ 严重程度: {diagnosis.severity}\n",
            f"📍 位置: {diagnosis.location}\n",
            f"💡 原因: {diagnosis.cause}\n",
            f"🔧 建议: {diagnosis.suggestion}\n"
        ]

        if diagnosis.fixed_code:
            answer_parts.append("\n修复代码示例:")
            answer_parts.append(diagnosis.fixed_code)

        return QAResponse(
            answer=''.join(answer_parts),
            confidence=0.85,
            related_code=[context[:200]] if context else [],
            suggestions=["还有其他问题吗？", "需要我生成修复代码吗？"]
        )

    def _handle_howto(self, question: str) -> QAResponse:
        """处理HowTo问题"""
        templates = {
            'import': "使用 `import 模块名` 或 `from 模块名 import 函数名`",
            'function': "使用 `def 函数名(参数):` 定义函数",
            'class': "使用 `class 类名:` 定义类",
            'loop': "使用 `for i in range(n):` 或 `while 条件:`",
            'condition': "使用 `if 条件:` 进行条件判断",
            'error': "使用 `try: ... except Exception:` 处理异常",
            'file': "使用 `with open('file.txt', 'r') as f:` 打开文件"
        }

        answer = "根据你的问题，以下是实现方法：\n\n"

        for key, suggestion in templates.items():
            if key in question.lower():
                answer += f"• {suggestion}\n"

        if answer == "根据你的问题，以下是实现方法：\n\n":
            answer = "请具体说明你想实现什么功能，我可以提供更准确的指导。"

        return QAResponse(
            answer=answer,
            confidence=0.8,
            suggestions=["可以给你具体的代码示例", "需要更详细的解释吗？"]
        )

    def _handle_why(self, question: str) -> QAResponse:
        """处理Why问题"""
        return QAResponse(
            answer="这个问题可能由以下原因导致：\n\n"
                   "1. 代码逻辑错误\n"
                   "2. 数据类型不匹配\n"
                   "3. 变量未正确定义\n"
                   "4. 依赖库未正确导入\n\n"
                   "请提供具体的代码或错误信息，我可以帮你分析原因。",
            confidence=0.7,
            suggestions=["提供具体的代码", "粘贴错误信息"]
        )

    def _handle_general(self, question: str) -> QAResponse:
        """处理一般问题"""
        return QAResponse(
            answer=f"你问的是: {question}\n\n"
                   "我可以帮你：\n"
                   "• 解释代码功能\n"
                   "• 诊断Bug原因\n"
                   "• 提供实现方法\n"
                   "• 分析代码质量\n\n"
                   "请提供更多细节或相关代码。",
            confidence=0.6,
            suggestions=["解释代码", "诊断Bug", "查找实现方法"]
        )


def create_qa_engine() -> EnhancedQAEngine:
    """创建问答引擎"""
    return EnhancedQAEngine()
