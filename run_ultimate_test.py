#!/usr/bin/env python3
"""
快速启动终极测试
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from v7_ultimate_real_world_test import UltimateRealWorldTest

if __name__ == "__main__":
    # 先用10分钟快速版本测试
    print("=" * 80)
    print("🚀 知识图谱记忆系统 v7.0 - 终极真实世界场景测试")
    print("=" * 80)
    
    duration = 600  # 10分钟快速版本
    print(f"目标时长: {duration}秒 ({duration/60:.1f}分钟)")
    print()
    
    test = UltimateRealWorldTest(duration_seconds=duration)
    test.run()
