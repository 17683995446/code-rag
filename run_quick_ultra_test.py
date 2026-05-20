#!/usr/bin/env python3
"""
快速版本：运行超深度测试的前4个核心测试（跳过长时间测试）
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 临时修改测试6为1分钟
import v7_ultra_deep_stress_test
original_test6 = v7_ultra_deep_stress_test.UltraDeepStressTest.test_6_extended_stability

def quick_test6(self, duration_seconds=60):
    """快速版本：1分钟稳定性测试"""
    return original_test6(self, duration_seconds=60)

v7_ultra_deep_stress_test.UltraDeepStressTest.test_6_extended_stability = quick_test6

# 导入修改后的测试
from v7_ultra_deep_stress_test import UltraDeepStressTest

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 超深度压力测试 - 快速版本（跳过长时间测试）")
    print("=" * 80)
    print()
    
    tester = UltraDeepStressTest()
    
    # 只运行前5个测试
    tests = [
        ("测试1: 超大规模数据", tester.test_1_ultra_large_scale),
        ("测试2: 超并发压力", tester.test_2_ultra_concurrency),
        ("测试3: 内存泄漏检测", tester.test_3_memory_leak_detection),
        ("测试4: 性能退化测试", tester.test_4_performance_degradation),
        ("测试5: 数据一致性", tester.test_5_data_consistency),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print()
        success = test_func()
        if success:
            passed += 1
            print(f"✅ {test_name} - 通过")
        else:
            failed += 1
            print(f"❌ {test_name} - 失败")
    
    print()
    print("=" * 80)
    print("📊 快速测试总结")
    print("=" * 80)
    print(f" 通过测试: {passed}/{len(tests)}")
    print(f" 失败测试: {failed}/{len(tests)}")
    print(f" 发现问题: {len(tester.results['issues'])}")
    print("=" * 80)
