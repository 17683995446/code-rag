"""
Code RAG v22.0 - 安全审计与扫描
自动漏洞检测系统
"""

import re
import hashlib
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum


class VulnerabilitySeverity(Enum):
    """漏洞严重级别"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class VulnerabilityType(Enum):
    """漏洞类型"""
    SQL_INJECTION = "sql_injection"
    XSS = "xss"
    CSRF = "csrf"
    INSECURE_RANDOM = "insecure_random"
    HARDCODED_SECRETS = "hardcoded_secrets"
    PATH_TRAVERSAL = "path_traversal"
    COMMAND_INJECTION = "command_injection"


@dataclass
class Vulnerability:
    """漏洞"""
    vulnerability_type: VulnerabilityType
    severity: VulnerabilitySeverity
    description: str
    line_number: int
    code_snippet: str
    confidence: float = 0.8
    remediation: str = ""
    found_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict:
        return {
            "vulnerability_type": self.vulnerability_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "line_number": self.line_number,
            "code_snippet": self.code_snippet,
            "confidence": self.confidence,
            "remediation": self.remediation,
            "found_at": self.found_at
        }


@dataclass
class SecurityReport:
    """安全报告"""
    report_id: str
    generated_at: float
    total_vulnerabilities: int
    severity_counts: Dict[str, int] = field(default_factory=dict)
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    risk_score: float = 0.0
    recommendations: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at,
            "total_vulnerabilities": self.total_vulnerabilities,
            "severity_counts": self.severity_counts,
            "vulnerabilities": [v.to_dict() for v in self.vulnerabilities],
            "risk_score": self.risk_score,
            "recommendations": self.recommendations
        }


class SecurityPatternDetector:
    """安全模式检测器"""
    
    def __init__(self):
        self.patterns = {
            VulnerabilityType.SQL_INJECTION: {
                "patterns": [
                    r"execute\(\s*['\"]\s*([^'\"]*?SELECT[^'\"]*?)\s*['\"]\s*,\s*(.*?)\s*\)",
                    r"execute\(\s*['\"]\s*(INSERT|UPDATE|DELETE|DROP|TRUNCATE|CREATE)\s.*?\s*['\"]\s*,\s*(.*?)\s*\)",
                    r"\.format\(.*?\)\s*(?:\.|$)",
                ],
                "severity": VulnerabilitySeverity.HIGH,
                "description": "Potential SQL injection vulnerability",
                "remediation": "Use parameterized queries or prepared statements"
            },
            VulnerabilityType.HARDCODED_SECRETS: {
                "patterns": [
                    r"(?:password|secret|api[_-]?key|token)\s*[=:]\s*['\"][^'\"]{8,}['\"]",
                    r"(['\"])([A-Za-z0-9+/]{40,}=*)\1",
                ],
                "severity": VulnerabilitySeverity.CRITICAL,
                "description": "Hardcoded secret detected",
                "remediation": "Use environment variables or secure key management"
            },
            VulnerabilityType.PATH_TRAVERSAL: {
                "patterns": [
                    r"open\(\s*['\"].*?\.\.\./.*?['\"]",
                    r"os\.path\.join\(.*?\.\.\..*?\)",
                ],
                "severity": VulnerabilitySeverity.HIGH,
                "description": "Potential path traversal vulnerability",
                "remediation": "Normalize paths and validate file paths"
            },
            VulnerabilityType.COMMAND_INJECTION: {
                "patterns": [
                    r"system\(\s*['\"]",
                    r"popen\(\s*['\"]",
                    r"subprocess\.(?:call|run|Popen)\(.*?shell\s*=\s*True",
                ],
                "severity": VulnerabilitySeverity.CRITICAL,
                "description": "Potential command injection vulnerability",
                "remediation": "Avoid shell=True and use subprocess.run without shell"
            },
            VulnerabilityType.XSS: {
                "patterns": [
                    r"innerHTML\s*=",
                    r"document\.write\(",
                    r"eval\(",
                ],
                "severity": VulnerabilitySeverity.MEDIUM,
                "description": "Potential XSS vulnerability",
                "remediation": "Use textContent instead of innerHTML or sanitize inputs"
            },
            VulnerabilityType.INSECURE_RANDOM: {
                "patterns": [
                    r"random\.",
                    r"import\s+random",
                ],
                "severity": VulnerabilitySeverity.INFO,
                "description": "Use of insecure random number generator",
                "remediation": "Use secrets module for secure random numbers"
            },
        }
    
    def detect(self, code: str) -> List[Vulnerability]:
        """检测安全漏洞"""
        vulnerabilities = []
        lines = code.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            for vuln_type, config in self.patterns.items():
                for pattern in config["patterns"]:
                    if re.search(pattern, line, re.IGNORECASE):
                        snippet = line.strip()
                        if len(snippet) > 100:
                            snippet = snippet[:97] + "..."
                        
                        vulnerabilities.append(Vulnerability(
                            vulnerability_type=vuln_type,
                            severity=config["severity"],
                            description=config["description"],
                            line_number=line_num,
                            code_snippet=snippet,
                            remediation=config["remediation"],
                            confidence=0.8
                        ))
        
        return vulnerabilities


class SecurityScanner:
    """安全扫描器"""
    
    def __init__(self):
        self.detector = SecurityPatternDetector()
        self.scan_history: List[SecurityReport] = []
    
    def scan_code(self, code: str, language: str = "python", 
                project_name: str = "default") -> SecurityReport:
        """扫描代码"""
        vulnerabilities = self.detector.detect(code)
        
        # 计算严重级别计数
        severity_counts = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
            "info": 0
        }
        
        for vuln in vulnerabilities:
            sev = vuln.severity.value
            if sev in severity_counts:
                severity_counts[sev] += 1
        
        # 计算风险评分
        risk_score = (
            severity_counts["critical"] * 100 +
            severity_counts["high"] * 50 +
            severity_counts["medium"] * 25 +
            severity_counts["low"] * 10 +
            severity_counts["info"] * 5
        )
        
        # 生成建议
        recommendations = self._generate_recommendations(
            vulnerabilities, severity_counts
        )
        
        report = SecurityReport(
            report_id=f"sec_report_{int(time.time())}",
            generated_at=time.time(),
            total_vulnerabilities=len(vulnerabilities),
            severity_counts=severity_counts,
            vulnerabilities=vulnerabilities,
            risk_score=min(risk_score, 100),
            recommendations=recommendations
        )
        
        self.scan_history.append(report)
        
        return report
    
    def _generate_recommendations(self, vulnerabilities: List[Vulnerability], 
                                severity_counts: Dict[str, int]) -> List[str]:
        """生成安全建议"""
        recommendations = []
        
        if severity_counts["critical"] > 0:
            recommendations.append("⚠️ CRITICAL VULNERABILITIES FOUND - ADDRESS IMMEDIATELY!")
        
        if severity_counts["high"] > 0:
            recommendations.append("⚠️ High priority vulnerabilities - fix soon")
        
        if severity_counts["medium"] > 0:
            recommendations.append("Medium priority items - schedule for fix")
        
        if severity_counts["critical"] == 0 and severity_counts["high"] == 0:
            recommendations.append("✅ No critical/high vulnerabilities found!")
        
        # 添加常见的安全最佳实践
        recommendations.extend([
            "Use parameterized queries for database operations",
            "Never hardcode secrets or passwords in code",
            "Validate and sanitize all user inputs",
            "Use environment variables for configuration",
            "Regularly update dependencies",
        ])
        
        return recommendations
    
    def get_scan_summary(self) -> Dict:
        """获取扫描摘要"""
        if not self.scan_history:
            return {"status": "no_scans"}
        
        latest = self.scan_history[-1]
        
        return {
            "scan_count": len(self.scan_history),
            "latest_report": latest.to_dict(),
            "total_vulnerabilities": sum(
                len(r.vulnerabilities) for r in self.scan_history
            ),
            "latest_risk_score": latest.risk_score
        }


class DependencyScanner:
    """依赖项扫描器（简化版）"""
    
    def __init__(self):
        self.known_vulnerable = {
            "requests": {"versions": ["2.0.0", "2.1.0"], "severity": "high"},
            "flask": {"versions": ["0.12.0"], "severity": "medium"},
            "numpy": {"versions": ["1.19.0"], "severity": "low"},
        }
    
    def scan_dependencies(self, requirements_content: str) -> List[Dict]:
        """扫描依赖项"""
        vulnerabilities = []
        
        lines = requirements_content.split('\n')
        for line in lines:
            line = line.strip()
            if '==' in line:
                package, version = line.split('==', 1)
                package = package.strip()
                version = version.strip()
                
                if package in self.known_vulnerable:
                    if version in self.known_vulnerable[package]["versions"]:
                        vulnerabilities.append({
                            "package": package,
                            "version": version,
                            "severity": self.known_vulnerable[package]["severity"],
                            "description": f"Known vulnerability in {package} {version}"
                        })
        
        return vulnerabilities


def create_security_scanner() -> SecurityScanner:
    """创建安全扫描器"""
    return SecurityScanner()
