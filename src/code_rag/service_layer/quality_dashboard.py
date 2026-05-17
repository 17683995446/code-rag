"""
Code RAG v22.0 - 代码质量仪表板
完整报告和监控系统
"""

import time
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict


class QualityLevel(Enum):
    """质量级别"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


class MetricType(Enum):
    """指标类型"""
    CODE_QUALITY = "code_quality"
    SECURITY = "security"
    MAINTAINABILITY = "maintainability"
    COMPLEXITY = "complexity"


@dataclass
class QualityMetric:
    """质量指标"""
    metric_type: MetricType
    name: str
    value: float
    max_value: float = 100.0
    weight: float = 1.0
    description: str = ""
    
    def get_score(self) -> float:
        """获取标准化分数（0-100）"""
        if self.max_value > 0:
            return min(100.0, (self.value / self.max_value) * 100.0)
        return 0.0
    
    def to_dict(self) -> Dict:
        return {
            "metric_type": self.metric_type.value,
            "name": self.name,
            "value": self.value,
            "max_value": self.max_value,
            "score": self.get_score(),
            "weight": self.weight,
            "description": self.description
        }


@dataclass
class TrendPoint:
    """趋势点"""
    timestamp: float
    value: float
    metric_name: str


@dataclass
class QualityReport:
    """质量报告"""
    report_id: str
    generated_at: float
    overall_score: float
    quality_level: QualityLevel
    metrics: List[QualityMetric] = field(default_factory=list)
    issues: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    trend_data: Dict[str, List[TrendPoint]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "overall_score": self.overall_score,
            "quality_level": self.quality_level.value,
            "metrics": [m.to_dict() for m in self.metrics],
            "issues": self.issues,
            "recommendations": self.recommendations,
            "trend_data": {
                name: [
                    {"timestamp": tp.timestamp, "value": tp.value} 
                    for tp in points
                ] 
                for name, points in self.trend_data.items()
            }
        }


class CodeAnalyzer:
    """代码分析器"""
    
    def __init__(self):
        self.patterns = {
            "todo_comments": r"(?:TODO|FIXME|XXX|HACK)",
            "empty_functions": r"def \w+\([^)]*\):\s*(?:pass|return None|''')",
            "long_functions": r"def \w+",
            "comment_ratio": 0.0
        }
    
    def analyze(self, code: str, language: str = "python") -> List[QualityMetric]:
        """分析代码"""
        metrics = []
        
        lines = code.split('\n')
        total_lines = len([l for l in lines if l.strip()])
        
        # 代码行数
        metrics.append(QualityMetric(
            metric_type=MetricType.CODE_QUALITY,
            name="Line Count",
            value=min(total_lines, 1000),
            max_value=1000,
            weight=1.0,
            description="Total lines of code"
        ))
        
        # 注释比率
        comment_lines = len([l for l in lines if l.strip().startswith('#') or l.strip().startswith('//')])
        comment_ratio = comment_lines / max(1, total_lines) if total_lines > 0 else 0
        metrics.append(QualityMetric(
            metric_type=MetricType.MAINTAINABILITY,
            name="Comment Ratio",
            value=comment_ratio * 100,
            max_value=30.0,
            weight=1.0,
            description="Percentage of comments in code"
        ))
        
        # 复杂度（简化版）
        complexity_score = self._calculate_complexity(code)
        metrics.append(QualityMetric(
            metric_type=MetricType.COMPLEXITY,
            name="Complexity",
            value=complexity_score,
            max_value=20.0,
            weight=2.0,
            description="Cyclomatic complexity"
        ))
        
        # TODO/FIXME 标记
        todo_count = len(re.findall(self.patterns["todo_comments"], code))
        metrics.append(QualityMetric(
            metric_type=MetricType.MAINTAINABILITY,
            name="TODO/FIXME Count",
            value=100.0 - (todo_count * 10),
            max_value=100.0,
            weight=0.5,
            description="Penalty for outstanding tasks"
        ))
        
        return metrics
    
    def _calculate_complexity(self, code: str) -> float:
        """计算复杂度（简化版）"""
        complexity = 1
        keywords = ['if', 'elif', 'else', 'for', 'while', 'and', 'or', 'except', 'with']
        
        lines = code.split('\n')
        for line in lines:
            stripped = line.strip()
            if any(stripped.startswith(kw) for kw in keywords):
                complexity += 1
        
        return min(complexity, 20)


class TrendAnalyzer:
    """趋势分析器"""
    
    def __init__(self):
        self.history: Dict[str, List[TrendPoint]] = defaultdict(list)
    
    def add_point(self, metric_name: str, value: float):
        """添加趋势点"""
        point = TrendPoint(
            timestamp=time.time(),
            value=value,
            metric_name=metric_name
        )
        self.history[metric_name].append(point)
        
        # 只保留最近 100 个点
        if len(self.history[metric_name]) > 100:
            self.history[metric_name] = self.history[metric_name][-100:]
    
    def get_trend(self, metric_name: str) -> List[TrendPoint]:
        """获取趋势"""
        return self.history.get(metric_name, [])
    
    def calculate_trend_direction(self, metric_name: str) -> str:
        """计算趋势方向"""
        points = self.history.get(metric_name, [])
        if len(points) < 3:
            return "insufficient_data"
        
        recent = points[-5:] if len(points) >=5 else points
        if len(recent) < 2:
            return "stable"
        
        first = recent[0].value
        last = recent[-1].value
        
        if last > first:
            return "improving"
        elif last < first:
            return "declining"
        else:
            return "stable"


class QualityDashboard:
    """代码质量仪表板"""
    
    def __init__(self):
        self.analyzer = CodeAnalyzer()
        self.trend_analyzer = TrendAnalyzer()
        self.report_history: List[QualityReport] = []
    
    def analyze_code(self, code: str, language: str = "python", 
                    project_name: str = "default") -> QualityReport:
        """分析代码并生成报告"""
        metrics = self.analyzer.analyze(code, language)
        
        # 计算综合评分
        total_score = sum(m.get_score() * m.weight for m in metrics)
        total_weight = sum(m.weight for m in metrics)
        overall_score = total_score / total_weight if total_weight > 0 else 0
        
        # 确定质量级别
        quality_level = self._determine_quality_level(overall_score)
        
        # 生成问题和建议
        issues = self._detect_issues(code, metrics)
        recommendations = self._generate_recommendations(issues, metrics)
        
        report_id = f"report_{int(time.time())}"
        
        report = QualityReport(
            report_id=report_id,
            generated_at=time.time(),
            overall_score=overall_score,
            quality_level=quality_level,
            metrics=metrics,
            issues=issues,
            recommendations=recommendations,
            trend_data=dict(self.trend_analyzer.history)
        )
        
        # 记录趋势
        for metric in metrics:
            self.trend_analyzer.add_point(metric.name, metric.value)
        
        self.report_history.append(report)
        
        return report
    
    def _determine_quality_level(self, score: float) -> QualityLevel:
        """确定质量级别"""
        if score >= 85:
            return QualityLevel.EXCELLENT
        elif score >= 70:
            return QualityLevel.GOOD
        elif score >= 50:
            return QualityLevel.FAIR
        elif score >= 30:
            return QualityLevel.POOR
        else:
            return QualityLevel.CRITICAL
    
    def _detect_issues(self, code: str, metrics: List[QualityMetric]) -> List[Dict]:
        """检测问题"""
        issues = []
        
        # 从指标中识别问题
        for metric in metrics:
            if metric.name == "Complexity" and metric.value > 10:
                issues.append({
                    "type": "high_complexity",
                    "severity": "warning",
                    "message": f"High complexity ({metric.value:.0f}/20)",
                    "metric": metric.name
                })
            elif metric.name == "Comment Ratio" and metric.get_score() < 10:
                issues.append({
                    "type": "low_comments",
                    "severity": "info",
                    "message": "Low comment ratio",
                    "metric": metric.name
                })
            elif metric.name == "TODO/FIXME Count" and metric.value < 100:
                issues.append({
                    "type": "outstanding_tasks",
                    "severity": "info",
                    "message": "Outstanding TODO/FIXME comments",
                    "metric": metric.name
                })
        
        return issues
    
    def _generate_recommendations(self, issues: List[Dict], 
                                 metrics: List[QualityMetric]) -> List[str]:
        """生成建议"""
        recommendations = []
        
        if not issues:
            recommendations.append("Great job! Keep up the good work!")
        
        for issue in issues:
            if issue["type"] == "high_complexity":
                recommendations.append("Consider refactoring to reduce complexity")
            elif issue["type"] == "low_comments":
                recommendations.append("Add more comments to improve maintainability")
            elif issue["type"] == "outstanding_tasks":
                recommendations.append("Address outstanding TODO/FIXME items")
        
        return recommendations
    
    def get_dashboard_summary(self) -> Dict:
        """获取仪表板摘要"""
        if not self.report_history:
            return {"status": "no_data"}
        
        latest_report = self.report_history[-1]
        
        return {
            "latest_report": latest_report.to_dict(),
            "report_count": len(self.report_history),
            "quality_level": latest_report.quality_level.value,
            "overall_score": latest_report.overall_score,
            "trends": {
                metric_name: self.trend_analyzer.calculate_trend_direction(metric_name)
                for metric_name in self.trend_analyzer.history
            }
        }


def create_quality_dashboard() -> QualityDashboard:
    """创建代码质量仪表板"""
    return QualityDashboard()
