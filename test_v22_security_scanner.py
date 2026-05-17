#!/usr/bin/env python3
"""
Code RAG v22.0 - 安全审计与扫描测试
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("="*80)
print("🧪 Code RAG v22.0 - 安全审计与扫描测试")
print("="*80)

from code_rag.processing_layer.security_scanner import (
    create_security_scanner,
    SecurityScanner,
    SecurityPatternDetector,
    DependencyScanner,
    VulnerabilityType,
    VulnerabilitySeverity
)


def test_pattern_detector():
    """测试模式检测器"""
    print("\n" + "="*70)
    print("测试 1: 安全模式检测器")
    print("="*70)
    
    detector = SecurityPatternDetector()
    
    dangerous_code = """
# This code has security issues
password = "my_secret_password_123"

cursor.execute("SELECT * FROM users WHERE name = '" + username + "'")

os.system("rm -rf " + user_input)

os.path.join("/tmp", user_provided_path)

import random
value = random.randint(0, 100)
"""
    
    vulnerabilities = detector.detect(dangerous_code)
    
    assert len(vulnerabilities) > 0
    print(f"  ✅ 检测到 {len(vulnerabilities)} 个潜在安全漏洞")
    
    for vuln in vulnerabilities:
        print(f"     - [{vuln.severity.value}] {vuln.vulnerability_type.value}")
        print(f"       位置: 行 {vuln.line_number}")
        print(f"       代码: {vuln.code_snippet}")
    
    return True


def test_security_report_generation():
    """测试安全报告生成"""
    print("\n" + "="*70)
    print("测试 2: 安全报告生成")
    print("="*70)
    
    scanner = create_security_scanner()
    
    test_code = """
password = "hardcoded_secret_key_here"

def unsafe_function():
    cursor.execute("SELECT * FROM users WHERE name = '" + name + "'")
    return result
"""
    
    report = scanner.scan_code(test_code, "python", "Test Project")
    
    assert report is not None
    print(f"  ✅ 安全报告生成成功")
    print(f"     - 漏洞总数: {report.total_vulnerabilities}")
    print(f"     - 风险评分: {report.risk_score}")
    
    print(f"     - 严重级别分布:")
    for severity, count in report.severity_counts.items():
        if count > 0:
            print(f"       * {severity}: {count}")
    
    print(f"     - 建议数量: {len(report.recommendations)}")
    for rec in report.recommendations[:3]:
        print(f"       - {rec}")
    
    return True


def test_dependency_scanner():
    """测试依赖项扫描器"""
    print("\n" + "="*70)
    print("测试 3: 依赖项扫描器")
    print("="*70)
    
    dep_scanner = DependencyScanner()
    
    requirements = """
requests==2.0.0
flask==0.12.0
numpy==1.19.0
safe-package==1.0.0
"""
    
    issues = dep_scanner.scan_dependencies(requirements)
    
    print(f"  ✅ 扫描到 {len(issues)} 个有问题的依赖项")
    
    for issue in issues:
        print(f"     - {issue['package']} {issue['version']}: {issue['severity']}")
    
    return True


def test_multilanguage_security_scanning():
    """测试多语言安全扫描"""
    print("\n" + "="*70)
    print("测试 4: 多语言安全扫描")
    print("="*70)
    
    scanner = create_security_scanner()
    
    test_cases = [
        ("python", """
password = "secret123"
cursor.execute(sql)
        """),
        ("javascript", """
var password = "secret123";
document.write(user_input);
eval(user_code);
        """),
        ("java", """
String password = "secret123";
Runtime.getRuntime().exec(cmd);
        """),
    ]
    
    for lang, code in test_cases:
        report = scanner.scan_code(code, lang, f"Test {lang}")
        print(f"  ✅ {lang}: 发现 {report.total_vulnerabilities} 个问题, 风险评分 {report.risk_score}")
    
    return True


def test_scan_history_summary():
    """测试扫描历史摘要"""
    print("\n" + "="*70)
    print("测试 5: 扫描历史和摘要")
    print("="*70)
    
    scanner = create_security_scanner()
    
    # 多次扫描
    for i in range(3):
        code = f"password = 'test{i}'"
        scanner.scan_code(code, "python", f"Project {i}")
    
    summary = scanner.get_scan_summary()
    
    assert summary is not None
    assert summary.get("status") != "no_scans"
    
    print(f"  ✅ 扫描历史摘要生成成功")
    print(f"     - 扫描次数: {summary.get('scan_count', 0)}")
    print(f"     - 总漏洞数: {summary.get('total_vulnerabilities', 0)}")
    print(f"     - 最新风险评分: {summary.get('latest_risk_score', 0)}")
    
    return True


def test_clean_code_scan():
    """测试清洁代码的扫描（无问题）"""
    print("\n" + "="*70)
    print("测试 6: 清洁代码扫描")
    print("="*70)
    
    scanner = create_security_scanner()
    
    clean_code = """
def safe_function():
    result = calculate()
    return result
"""
    
    report = scanner.scan_code(clean_code, "python", "Clean Project")
    
    print(f"  ✅ 清洁代码扫描完成")
    print(f"     - 发现问题: {report.total_vulnerabilities}")
    print(f"     - 风险评分: {report.risk_score}")
    
    for rec in report.recommendations:
        print(f"       - {rec}")
    
    return True


def run_all_tests():
    """运行所有测试"""
    tests = [
        ("安全模式检测器", test_pattern_detector),
        ("安全报告生成", test_security_report_generation),
        ("依赖项扫描器", test_dependency_scanner),
        ("多语言安全扫描", test_multilanguage_security_scanning),
        ("扫描历史摘要", test_scan_history_summary),
        ("清洁代码扫描", test_clean_code_scan)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            print(f"\n[{passed+1+failed}/{len(tests)}] 执行: {name}")
            if test_func():
                passed += 1
                print(f"\n✅ {name} - 通过")
            else:
                failed += 1
                print(f"\n❌ {name} - 失败")
        except Exception as e:
            failed += 1
            print(f"\n❌ {name} - 异常: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80)
    print("📋 安全审计与扫描测试总结")
    print("="*80)
    print(f"📊 总测试数: {len(tests)}")
    print(f"✅ 通过: {passed}")
    print(f"❌ 失败: {failed}")
    print(f"📈 通过率: {(passed/len(tests)*100):.1f}%")
    
    if failed == 0:
        print("\n🎉 所有安全审计与扫描测试通过！")
        return True
    else:
        print(f"\n⚠️ {failed}个测试失败")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
