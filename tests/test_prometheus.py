"""
Prometheus监控模块测试
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import (
    PrometheusMetrics,
    get_prometheus_metrics
)


def test_prometheus_initialization():
    """测试Prometheus初始化"""
    print("🧪 测试: Prometheus初始化")

    prom = PrometheusMetrics()

    assert prom is not None
    print(f"  - Prometheus可用: {prom.is_available()}")

    print("  ✅ Prometheus初始化测试通过")
    return True


def test_prometheus_counters():
    """测试计数器功能"""
    print("🧪 测试: Prometheus计数器")

    prom = PrometheusMetrics()

    # 测试各种计数器
    prom.inc_search()
    prom.inc_search()
    prom.inc_ask()
    prom.inc_index()
    prom.inc_api_request('search')
    prom.inc_api_error('search')

    print("  - 计数器操作成功")

    # 测试文档计数
    prom.set_documents_indexed(100)
    prom.set_vector_dimension(384)

    print("  ✅ Prometheus计数器测试通过")
    return True


def test_prometheus_timing():
    """测试时间测量"""
    print("🧪 测试: Prometheus时间测量")

    prom = PrometheusMetrics()

    # 测量操作
    with prom.measure_operation('search'):
        time.sleep(0.01)

    with prom.measure_operation('ask'):
        time.sleep(0.02)

    with prom.measure_operation('index'):
        time.sleep(0.05)

    print("  - 时间测量操作成功")

    print("  ✅ Prometheus时间测量测试通过")
    return True


def test_prometheus_metrics_text():
    """测试指标文本生成"""
    print("🧪 测试: Prometheus指标文本")

    prom = PrometheusMetrics()

    metrics_text = prom.get_metrics_text()

    assert metrics_text is not None
    print(f"  - 指标文本长度: {len(metrics_text)}")
    print(f"  - 指标文本预览: {metrics_text[:100]}")

    print("  ✅ Prometheus指标文本测试通过")
    return True


def test_get_prometheus_metrics():
    """测试全局获取函数"""
    print("🧪 测试: get_prometheus_metrics全局函数")

    prom1 = get_prometheus_metrics()
    prom2 = get_prometheus_metrics()

    assert prom1 is not None
    assert prom2 is not None
    assert prom1 is prom2  # 应该是同一个单例

    print("  ✅ get_prometheus_metrics测试通过")
    return True


def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("  📊 Prometheus监控模块测试")
    print("=" * 70)

    all_passed = True
    tests = [
        ("初始化", test_prometheus_initialization),
        ("计数器", test_prometheus_counters),
        ("时间测量", test_prometheus_timing),
        ("指标文本", test_prometheus_metrics_text),
        ("全局获取函数", test_get_prometheus_metrics),
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

    print("\n" + "=" * 70)
    if all_passed:
        print("  ✅ 所有Prometheus监控模块测试通过！")
    else:
        print("  ❌ 部分测试失败")
    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
