"""
Code RAG v19.0 - VS Code扩展集成中间件
编辑器集成、LSP基础、实时代码审查、问题面板集成
"""

from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import json


class DiagnosticSeverity(Enum):
    """诊断严重级别"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"
    HINT = "hint"


@dataclass
class CodeDiagnostic:
    """代码诊断（兼容LSP问题）"""
    message: str
    severity: DiagnosticSeverity
    line_start: int
    line_end: int
    column_start: int = 0
    column_end: int = 0
    code: str = ""
    source: str = "CodeRAG"
    suggestions: List[str] = field(default_factory=list)


@dataclass
class CodeSuggestion:
    """代码建议"""
    title: str
    description: str
    code: str = ""
    code_type: str = "quickfix"
    severity: DiagnosticSeverity = DiagnosticSeverity.INFO
    action: Optional[Dict] = field(default_factory=dict)


class CodeReviewer:
    """实时代码审查器"""
    
    def __init__(self):
        self.rules = self._load_rules()
    
    def _load_rules(self):
        """加载审查规则"""
        return [
            {"name": "function_length", "max": 50, "severity": "warning"},
            {"name": "complexity", "threshold": 10, "severity": "warning"},
            {"name": "naming", "check": True, "severity": "info"},
        ]
    
    def review_code(self, code: str, language: str = "python") -> List[CodeDiagnostic]:
        """审查代码并返回诊断"""
        diagnostics = []
        
        # 简单的启发式规则"""
        
        lines = code.split('\n')
        # 行长度检查
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                diagnostics.append(CodeDiagnostic(
                    message=f"Line exceeds 120 characters",
                    severity=DiagnosticSeverity.WARNING,
                    line_start=i,
                    line_end=i
                ))
        
        # 函数长度检查（简化版）
        line_count = len(lines)
        if line_count > 100:
            diagnostics.append(CodeDiagnostic(
                message=f"File is quite long ({line_count} lines)",
                severity=DiagnosticSeverity.INFO,
                line_start=1,
                line_end=1
            ))
        
        return diagnostics
    
    def suggest_improvements(self, code: str, issue: CodeDiagnostic) -> List[CodeSuggestion]:
        """提供改进建议"""
        suggestions = []
        
        suggestions.append(CodeSuggestion(
            title="Refactor for readability",
            description="Consider breaking this into smaller pieces",
            code=""
        ))
        
        return suggestions


class LSPIntegration:
    """LSP协议集成层"""
    
    def __init__(self):
        self.reviewer = CodeReviewer()
        self.diagnostics_cache: Dict[str, List[CodeDiagnostic]] = {}
    
    def on_document_open(self, file_path: str, code: str, language: str = "python"):
        """文档打开事件"""
        diagnostics = self.reviewer.review_code(code, language)
        self.diagnostics_cache[file_path] = diagnostics
        return diagnostics
    
    def on_document_change(self, file_path: str, code: str, language: str = "python"):
        """文档变更事件"""
        return self.on_document_open(file_path, code, language)
    
    def get_diagnostics(self, file_path: str) -> List[CodeDiagnostic]:
        """获取文件诊断"""
        return self.diagnostics_cache.get(file_path, [])
    
    def get_suggestions(self, file_path: str, line: int) -> List[CodeSuggestion]:
        """获取指定行建议"""
        diagnostics = self.get_diagnostics(file_path)
        relevant = [d for d in diagnostics if d.line_start <= line <= d.line_end]
        suggestions = []
        for diag in relevant:
            suggestions.extend(self.reviewer.suggest_improvements("", diag))
        return suggestions


class VscodeExtension:
    """VS Code扩展后端服务"""
    
    def __init__(self):
        self.lsp = LSPIntegration()
        self.active_documents: Dict[str, Dict] = {}
        self.connected = False
    
    def connect(self):
        """连接到编辑器"""
        self.connected = True
        return {"status": "connected", "version": "19.0.0"}
    
    def disconnect(self):
        """断开连接"""
        self.connected = False
        return {"status": "disconnected"}
    
    def open_document(self, file_path: str, content: str, language: str = "python"):
        """打开文档"""
        self.active_documents[file_path] = {
            "content": content,
            "language": language
        }
        diagnostics = self.lsp.on_document_open(file_path, content, language)
        return {
            "diagnostics": self._format_diagnostics(diagnostics)
        }
    
    def update_document(self, file_path: str, content: str):
        """更新文档"""
        if file_path in self.active_documents:
            self.active_documents[file_path]["content"] = content
            diagnostics = self.lsp.on_document_change(file_path, content, self.active_documents[file_path]["language"])
            return {
                "diagnostics": self._format_diagnostics(diagnostics)
            }
        return {"diagnostics": []}
    
    def _format_diagnostics(self, diagnostics: List[CodeDiagnostic]) -> List[Dict]:
        """格式化为LSP兼容格式"""
        formatted = []
        for diag in diagnostics:
            formatted.append({
                "range": {
                    "start": {"line": diag.line_start - 1, "character": diag.column_start},
                    "end": {"line": diag.line_end - 1, "character": diag.column_end}
                },
                "severity": {
                    "error": 1,
                    "warning": 2,
                    "info": 3,
                    "hint": 4
                }[diag.severity.value],
                "source": diag.source,
                "message": diag.message,
                "code": diag.code
            })
        return formatted
    
    def get_code_actions(self, file_path: str, line: int):
        """获取代码操作（Quick Fix）"""
        suggestions = self.lsp.get_suggestions(file_path, line)
        return {
            "actions": [
                {
                    "title": s.title,
                    "kind": "quickfix",
                    "diagnostics": [],
                    "edit": {}
                }
                for s in suggestions
            ]
        }


def create_vscode_service():
    """创建VS Code扩展服务实例"""
    return VscodeExtension()
