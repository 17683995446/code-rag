"""
产品级安全、备份、评估模块测试
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import (
    RateLimiter,
    InputValidator,
    SecurityManager,
    BackupManager,
    VersionControl,
    RAGEvaluator,
    TestCase,
    create_default_test_suite
)


def test_rate_limiter():
    """测试限流器"""
    print("🧪 测试: RateLimiter")

    limiter = RateLimiter(max_requests=5, window_seconds=60)

    # 测试正常请求
    for i in range(5):
        assert limiter.check_rate_limit(f"client_{i}") == True

    # 测试限流
    assert limiter.check_rate_limit("client_0") == False

    # 统计
    stats = limiter.get_stats()
    print(f"  - 命中: {stats['hits']}")
    print(f"  - 拒绝: {stats['misses']}")
    print(f"  - 剩余: {stats['remaining']}")

    assert stats['hits'] == 5
    assert stats['misses'] == 1

    print("  ✅ RateLimiter测试通过")
    return True


def test_input_validator():
    """测试输入验证器"""
    print("🧪 测试: InputValidator")

    validator = InputValidator()

    # 测试路径验证
    assert validator.validate_path("/safe/path") == True
    assert validator.validate_path("../../../etc/passwd") == False
    assert validator.validate_path("path<script>") == False

    # 测试查询验证
    assert validator.validate_query("正常查询") == True
    assert validator.validate_query("<script>alert(1)</script>") == False

    # 测试清理
    sanitized = validator.sanitize_path("path/../with/../danger")
    assert '..' not in sanitized

    print("  ✅ InputValidator测试通过")
    return True


def test_security_manager():
    """测试安全管理器"""
    print("🧪 测试: SecurityManager")

    manager = SecurityManager()

    # 测试认证
    assert manager.check_auth("valid_key_1234567890123456789012") == True
    assert manager.check_auth("short") == False
    assert manager.check_auth(None) == False

    # 测试审计日志
    manager.audit_log("test_action", {"key": "value"})
    logs = manager.get_audit_log()
    assert len(logs) > 0

    print(f"  - 审计日志: {len(logs)} 条")

    print("  ✅ SecurityManager测试通过")
    return True


def test_backup_manager():
    """测试备份管理器"""
    print("🧪 测试: BackupManager")

    # 创建测试目录
    test_dir = Path("/tmp/test_backup_source")
    test_dir.mkdir(exist_ok=True)
    (test_dir / "test.txt").write_text("test content")

    # 创建备份
    manager = BackupManager("/tmp/test_backups")
    backup_id = manager.create_backup(
        str(test_dir),
        description="测试备份",
        tags=["test"]
    )

    assert backup_id is not None
    print(f"  - 创建备份: {backup_id}")

    # 列出备份
    backups = manager.list_backups()
    assert len(backups) > 0
    print(f"  - 备份数量: {len(backups)}")

    # 统计
    stats = manager.get_stats()
    print(f"  - 总备份: {stats.total_backups}")
    print(f"  - 总大小: {stats.total_size_bytes} bytes")

    # 清理
    manager.delete_backup(backup_id)
    print("  ✅ BackupManager测试通过")
    return True


def test_version_control():
    """测试版本控制"""
    print("🧪 测试: VersionControl")

    vc = VersionControl("/tmp/test_versions")

    # 创建版本
    v1 = vc.create_version("v1.0", "初始版本")
    v2 = vc.create_version("v2.0", "新增功能")

    assert v1 is not None
    assert v2 is not None

    # 列出版本
    versions = vc.list_versions()
    assert len(versions) >= 2
    print(f"  - 版本数量: {len(versions)}")

    # 获取版本
    version = vc.get_version(v1)
    assert version is not None
    assert version['name'] == "v1.0"

    print("  ✅ VersionControl测试通过")
    return True


def test_rag_evaluator():
    """测试RAG评估器"""
    print("🧪 测试: RAGEvaluator")

    from src.core import CodeRAG

    # 创建评估器
    evaluator = RAGEvaluator()

    # 添加测试用例
    test_cases = [
        TestCase(
            query="FAISS向量数据库",
            expected_contexts=["FAISS", "向量"],
            expected_keywords=["FAISS", "向量", "数据库"],
            category="knowledge",
            difficulty="easy"
        ),
        TestCase(
            query="Python排序算法",
            expected_contexts=["排序", "Python"],
            expected_keywords=["排序", "算法", "Python"],
            category="code",
            difficulty="medium"
        )
    ]

    # 评估RAG系统
    rag = CodeRAG(implementation="simplified")
    report = evaluator.evaluate_rag(rag, test_cases)

    assert report is not None
    assert report.total_tests == 2

    print(f"  - 总测试: {report.total_tests}")
    print(f"  - 通过: {report.passed_tests}")
    print(f"  - 失败: {report.failed_tests}")
    print(f"  - 总体得分: {report.overall_score:.2f}")

    # 显示指标
    metrics = report.metrics.get('overall')
    if metrics and isinstance(metrics, dict):
        print(f"  - 精确率: {metrics.get('precision', 0):.2%}")
        print(f"  - 召回率: {metrics.get('recall', 0):.2%}")
        print(f"  - F1分数: {metrics.get('f1_score', 0):.2f}")
        print(f"  - 延迟: {metrics.get('latency_ms', 0):.2f}ms")

    print("  ✅ RAGEvaluator测试通过")
    return True


def test_create_default_suite():
    """测试默认测试套件"""
    print("🧪 测试: create_default_test_suite")

    test_cases = create_default_test_suite()

    assert len(test_cases) > 0
    assert all(isinstance(tc, TestCase) for tc in test_cases)

    print(f"  - 测试用例数量: {len(test_cases)}")
    for tc in test_cases:
        print(f"    - {tc.category}: {tc.query[:30]}...")

    print("  ✅ create_default_test_suite测试通过")
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 60)
    print("  🔒🛡️  产品级安全、备份、评估模块测试")
    print("=" * 60)

    all_passed = True
    tests = [
        ("RateLimiter", test_rate_limiter),
        ("InputValidator", test_input_validator),
        ("SecurityManager", test_security_manager),
        ("BackupManager", test_backup_manager),
        ("VersionControl", test_version_control),
        ("RAGEvaluator", test_rag_evaluator),
        ("DefaultTestSuite", test_create_default_suite),
    ]

    for test_name, test_func in tests:
        try:
            print()
            if not test_func():
                all_passed = False
        except Exception as e:
            print(f"  ❌ {test_name}测试失败: {e}")
            import traceback
            traceback.print_exc()
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("  ✅ 所有新模块测试通过！")
    else:
        print("  ❌ 部分测试失败")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
