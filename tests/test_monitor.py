"""
产品级监控模块测试
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core import (
    MetricsCollector,
    PerformanceMonitor,
    get_monitor,
    monitor,
    get_logger
)


def test_metrics_collector():
    """测试指标收集器"""
    print("🧪 测试: MetricsCollector")

    collector = MetricsCollector()

    # 记录指标
    collector.record_metric('test.metric', 10.5)
    collector.record_metric('test.metric', 20.5)
    collector.record_metric('test.metric', 15.0)

    # 计数器
    collector.increment_counter('test.counter', 5)
    collector.increment_counter('test.counter', 3)

    # 仪表
    collector.set_gauge('test.gauge', 100.0)

    # 验证
    stats = collector.get_metric_stats('test.metric')
    assert stats['count'] == 3
    assert stats['min'] == 10.5
    assert stats['max'] == 20.5

    assert collector.get_counter('test.counter') == 8
    assert collector.get_gauge('test.gauge') == 100.0

    print(f"  - 指标统计: {stats}")
    print(f"  - 计数器: {collector.get_counter('test.counter')}")
    print(f"  - 仪表: {collector.get_gauge('test.gauge')}")

    print("  ✅ MetricsCollector测试通过")
    return True


def test_operation_stats():
    """测试操作统计"""
    print("🧪 测试: OperationStats")

    collector = MetricsCollector()

    # 记录操作
    collector.record_operation('search', 0.1)
    collector.record_operation('search', 0.2)
    collector.record_operation('search', 0.15)
    collector.record_operation('search', 0.3, error=True)

    stats = collector.get_operation_stats('search')
    assert stats is not None
    assert stats.count == 4
    assert stats.total_time == 0.75
    assert stats.errors == 1

    print(f"  - 操作统计: count={stats.count}, avg={stats.avg_time:.3f}s, errors={stats.errors}")

    print("  ✅ OperationStats测试通过")
    return True


def test_performance_monitor():
    """测试性能监控器"""
    print("🧪 测试: PerformanceMonitor")

    monitor = PerformanceMonitor()

    # 记录系统指标
    monitor.record_system_metrics()

    # 获取系统信息
    info = monitor.get_system_info()
    assert 'cpu' in info
    assert 'memory' in info

    print(f"  - CPU: {info['cpu']['percent']:.1f}%")
    print(f"  - 内存: {info['memory']['percent']:.1f}%")
    print(f"  - 线程: {info['process']['threads']}")

    print("  ✅ PerformanceMonitor测试通过")
    return True


def test_monitor_context():
    """测试监控上下文管理器"""
    print("🧪 测试: Monitor Context")

    from src.core import monitor as monitor_ctx

    with monitor_ctx('test_operation'):
        time.sleep(0.01)

    mon = get_monitor()
    stats = mon.metrics.get_operation_stats('test_operation')

    assert stats is not None
    assert stats.count == 1

    print(f"  - 操作统计: {stats.count} 次, {stats.total_time:.3f}s")

    print("  ✅ Monitor Context测试通过")
    return True


def test_performance_report():
    """测试性能报告"""
    print("🧪 测试: PerformanceReport")

    monitor = get_monitor()

    # 执行一些操作
    for i in range(3):
        with monitor.monitor_operation('test_report_op'):
            time.sleep(0.01)

    report = monitor.get_performance_report()

    assert 'timestamp' in report
    assert 'system' in report
    assert 'process' in report
    assert 'operations' in report

    print(f"  - 报告时间: {report['timestamp']}")
    print(f"  - CPU使用: {report['system']['cpu_percent']:.1f}%")
    print(f"  - 内存使用: {report['system']['memory_percent']:.1f}%")

    print("  ✅ PerformanceReport测试通过")
    return True


def run_all_monitor_tests():
    """运行所有监控模块测试"""
    print("=" * 60)
    print("  📊 产品级监控模块测试")
    print("=" * 60)

    all_passed = True
    tests = [
        ("MetricsCollector", test_metrics_collector),
        ("OperationStats", test_operation_stats),
        ("PerformanceMonitor", test_performance_monitor),
        ("Monitor Context", test_monitor_context),
        ("PerformanceReport", test_performance_report),
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
        print("  ✅ 所有监控模块测试通过！")
    else:
        print("  ❌ 部分测试失败")
    print("=" * 60)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(run_all_monitor_tests())
