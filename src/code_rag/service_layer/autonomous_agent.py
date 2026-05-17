"""
Code RAG v23.0 - 自主代码分析代理
主动监控、分析和建议的 AI 代理系统
"""

import re
import time
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class AgentState(Enum):
    """代理状态"""
    IDLE = "idle"
    ANALYZING = "analyzing"
    RECOMMENDING = "recommending"
    MONITORING = "monitoring"


class AnalysisType(Enum):
    """分析类型"""
    PERFORMANCE = "performance"
    SECURITY = "security"
    QUALITY = "quality"
    ARCHITECTURE = "architecture"
    DEPENDENCIES = "dependencies"


@dataclass
class CodeInsight:
    """代码洞察"""
    insight_type: str
    title: str
    description: str
    priority: int = 1
    impact: str = "medium"
    affected_lines: List[int] = field(default_factory=list)
    suggestion: str = ""


@dataclass
class AgentAction:
    """代理行动"""
    action_type: str
    description: str
    target: str = ""
    priority: int = 1
    auto_execute: bool = False


class PerceptionModule:
    """感知模块 - 理解代码上下文"""
    
    def __init__(self):
        self.context_history: List[Dict] = []
    
    def analyze_context(self, code: str, language: str = "python") -> Dict:
        """分析代码上下文"""
        context = {
            "language": language,
            "lines": len(code.split('\n')),
            "patterns": self._detect_patterns(code),
            "structure": self._analyze_structure(code),
            "complexity": self._estimate_complexity(code)
        }
        
        self.context_history.append(context)
        return context
    
    def _detect_patterns(self, code: str) -> List[str]:
        """检测代码模式"""
        patterns = []
        
        if re.search(r'\bfor\b.*\bin\b.*range', code):
            patterns.append("loop_with_range")
        if re.search(r'\bif\b.*==.*None\b', code):
            patterns.append("null_check")
        if re.search(r'\bexcept\s*:\s*pass\b', code):
            patterns.append("bare_except")
        if re.search(r'\bglobal\b', code):
            patterns.append("global_usage")
        if re.search(r'\blambda\b', code):
            patterns.append("lambda_usage")
        
        return patterns
    
    def _analyze_structure(self, code: str) -> Dict:
        """分析代码结构"""
        lines = code.split('\n')
        
        return {
            "functions": len(re.findall(r'\bdef\b', code)),
            "classes": len(re.findall(r'\bclass\b', code)),
            "imports": len(re.findall(r'\bimport\b|\bfrom\b', code)),
            "docstrings": len(re.findall(r'""".*?"""|\'\'\'.*?\'\'\'', code, re.DOTALL)),
        }
    
    def _estimate_complexity(self, code: str) -> int:
        """估算复杂度"""
        keywords = ['if', 'elif', 'else', 'for', 'while', 'and', 'or', 'except']
        complexity = 1
        
        for keyword in keywords:
            complexity += len(re.findall(rf'\b{keyword}\b', code))
        
        return min(complexity, 20)


class DecisionEngine:
    """决策引擎 - 基于洞察决定行动"""
    
    def __init__(self):
        self.rules: List[Dict] = self._load_rules()
    
    def _load_rules(self) -> List[Dict]:
        """加载决策规则"""
        return [
            {
                "condition": lambda ctx: ctx.get("complexity", 0) > 10,
                "action": {
                    "type": "refactor",
                    "description": "建议重构以降低复杂度"
                },
                "priority": 1
            },
            {
                "condition": lambda ctx: ctx.get("structure", {}).get("bare_except", False),
                "action": {
                    "type": "security_review",
                    "description": "发现潜在安全问题"
                },
                "priority": 2
            },
            {
                "condition": lambda ctx: ctx.get("lines", 0) > 500,
                "action": {
                    "type": "split_file",
                    "description": "建议拆分大文件"
                },
                "priority": 3
            }
        ]
    
    def decide(self, context: Dict) -> List[AgentAction]:
        """基于上下文做出决策"""
        actions = []
        
        for rule in self.rules:
            if rule["condition"](context):
                actions.append(AgentAction(
                    action_type=rule["action"]["type"],
                    description=rule["action"]["description"],
                    priority=rule["priority"]
                ))
        
        return sorted(actions, key=lambda a: a.priority)


class ActionExecutor:
    """行动执行器"""
    
    def __init__(self):
        self.execution_history: List[Dict] = []
    
    def execute(self, action: AgentAction, code: str) -> Dict:
        """执行行动"""
        result = {
            "action": action.action_type,
            "description": action.description,
            "success": True,
            "timestamp": time.time()
        }
        
        if action.action_type == "refactor":
            result["output"] = self._generate_refactor_suggestions(code)
        elif action.action_type == "security_review":
            result["output"] = self._generate_security_insights(code)
        elif action.action_type == "split_file":
            result["output"] = self._suggest_file_split(code)
        else:
            result["output"] = "Generic suggestion"
        
        self.execution_history.append(result)
        return result
    
    def _generate_refactor_suggestions(self, code: str) -> List[str]:
        """生成重构建议"""
        suggestions = []
        
        if len(code.split('\n')) > 100:
            suggestions.append("考虑将长函数拆分为多个小函数")
        
        if 'global' in code:
            suggestions.append("避免使用全局变量，考虑使用类或参数传递")
        
        if re.search(r'\bfor\b.*\bfor\b', code):
            suggestions.append("考虑使用列表推导式或 map/filter")
        
        return suggestions
    
    def _generate_security_insights(self, code: str) -> List[str]:
        """生成安全洞察"""
        insights = []
        
        if 'password' in code.lower():
            insights.append("⚠️ 检测到可能的硬编码密码")
        
        if 'eval(' in code:
            insights.append("⚠️ 使用 eval() 可能导致安全问题")
        
        if 'exec(' in code:
            insights.append("⚠️ 使用 exec() 存在安全风险")
        
        return insights
    
    def _suggest_file_split(self, code: str) -> Dict:
        """建议文件拆分"""
        functions = re.findall(r'def (\w+)', code)
        classes = re.findall(r'class (\w+)', code)
        
        return {
            "suggested_modules": [f"{f}.py" for f in functions[:3]],
            "reason": f"检测到 {len(functions)} 个函数和 {len(classes)} 个类"
        }


class AutonomousCodeAgent:
    """自主代码分析代理"""
    
    def __init__(self):
        self.state = AgentState.IDLE
        self.perception = PerceptionModule()
        self.decision_engine = DecisionEngine()
        self.action_executor = ActionExecutor()
        self.insights_history: List[CodeInsight] = []
        self.is_monitoring = False
    
    def analyze(self, code: str, language: str = "python") -> Dict:
        """分析代码并返回洞察"""
        self.state = AgentState.ANALYZING
        
        context = self.perception.analyze_context(code, language)
        actions = self.decision_engine.decide(context)
        
        results = []
        for action in actions:
            result = self.action_executor.execute(action, code)
            results.append(result)
            
            self.insights_history.append(CodeInsight(
                insight_type=action.action_type,
                title=action.description,
                description=str(result.get("output", "")),
                suggestion=action.description
            ))
        
        self.state = AgentState.IDLE
        
        return {
            "context": context,
            "actions": results,
            "insights_count": len(results),
            "insights": [
                {
                    "type": insight.insight_type,
                    "title": insight.title,
                    "description": insight.description
                }
                for insight in self.insights_history[-5:]
            ]
        }
    
    def monitor(self, code: str, interval: int = 5) -> bool:
        """开始监控代码"""
        self.is_monitoring = True
        self.state = AgentState.MONITORING
        print(f"🤖 代理开始监控 (间隔: {interval}秒)")
        return True
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_monitoring = False
        self.state = AgentState.IDLE
        print("🤖 代理停止监控")
    
    def get_insights(self, code: str, analysis_type: Optional[AnalysisType] = None) -> List[CodeInsight]:
        """获取特定类型的洞察"""
        if analysis_type == AnalysisType.PERFORMANCE:
            return self._analyze_performance(code)
        elif analysis_type == AnalysisType.SECURITY:
            return self._analyze_security(code)
        elif analysis_type == AnalysisType.QUALITY:
            return self._analyze_quality(code)
        elif analysis_type == AnalysisType.ARCHITECTURE:
            return self._analyze_architecture(code)
        else:
            return self._analyze_all(code)
    
    def _analyze_performance(self, code: str) -> List[CodeInsight]:
        """性能分析"""
        insights = []
        
        if re.search(r'\.append\(.*?\+', code):
            insights.append(CodeInsight(
                insight_type="performance",
                title="字符串拼接性能问题",
                description="使用 + 拼接字符串可能导致性能问题",
                suggestion="使用 join() 或列表拼接"
            ))
        
        if 'for' in code and 'list(' in code:
            insights.append(CodeInsight(
                insight_type="performance",
                title="考虑使用列表推导式",
                description="列表推导式通常比循环更快",
                suggestion="优化循环逻辑"
            ))
        
        return insights
    
    def _analyze_security(self, code: str) -> List[CodeInsight]:
        """安全分析"""
        insights = []
        
        dangerous_patterns = [
            (r'eval\s*\(', "使用 eval() 存在安全风险"),
            (r'exec\s*\(', "使用 exec() 存在安全风险"),
            (r'pickle\.load', "使用 pickle.load 可能导致安全问题"),
            (r'os\.system\s*\(', "使用 os.system 可能导致命令注入"),
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, code):
                insights.append(CodeInsight(
                    insight_type="security",
                    title="安全风险检测",
                    description=message,
                    priority=1,
                    impact="high"
                ))
        
        return insights
    
    def _analyze_quality(self, code: str) -> List[CodeInsight]:
        """质量分析"""
        insights = []
        
        if not re.search(r'""".*?"""|\'\'\'.*?\'\'\'', code, re.DOTALL):
            insights.append(CodeInsight(
                insight_type="quality",
                title="缺少文档字符串",
                description="代码缺少文档说明",
                suggestion="添加 docstring"
            ))
        
        if re.search(r'\b[xlt]\s*=\s*\d+\b', code):
            insights.append(CodeInsight(
                insight_type="quality",
                title="使用单字母变量名",
                description="建议使用更有意义的变量名",
                suggestion="重命名变量"
            ))
        
        return insights
    
    def _analyze_architecture(self, code: str) -> List[CodeInsight]:
        """架构分析"""
        insights = []
        
        functions = re.findall(r'def (\w+)', code)
        if len(functions) > 20:
            insights.append(CodeInsight(
                insight_type="architecture",
                title="文件过大",
                description=f"检测到 {len(functions)} 个函数，建议拆分",
                suggestion="考虑模块化拆分"
            ))
        
        imports = re.findall(r'from (\w+)', code)
        if len(set(imports)) > 10:
            insights.append(CodeInsight(
                insight_type="architecture",
                title="过多依赖",
                description=f"导入了 {len(set(imports))} 个模块",
                suggestion="考虑依赖管理和模块化"
            ))
        
        return insights
    
    def _analyze_all(self, code: str) -> List[CodeInsight]:
        """完整分析"""
        all_insights = []
        all_insights.extend(self._analyze_performance(code))
        all_insights.extend(self._analyze_security(code))
        all_insights.extend(self._analyze_quality(code))
        all_insights.extend(self._analyze_architecture(code))
        return all_insights
    
    def generate_report(self) -> Dict:
        """生成分析报告"""
        return {
            "agent_state": self.state.value,
            "total_insights": len(self.insights_history),
            "insights_by_type": self._count_by_type(),
            "monitoring_active": self.is_monitoring,
            "recent_insights": [
                {
                    "type": i.insight_type,
                    "title": i.title,
                    "priority": i.priority
                }
                for i in self.insights_history[-10:]
            ]
        }
    
    def _count_by_type(self) -> Dict[str, int]:
        """按类型统计洞察"""
        counts = {}
        for insight in self.insights_history:
            counts[insight.insight_type] = counts.get(insight.insight_type, 0) + 1
        return counts


def create_autonomous_agent() -> AutonomousCodeAgent:
    """创建自主代码分析代理"""
    return AutonomousCodeAgent()
