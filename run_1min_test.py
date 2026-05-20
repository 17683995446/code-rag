#!/usr/bin/env python3
"""
运行1分钟快速测试，确保修改正确
"""
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from v7_ultimate_real_world_test import UltimateRealWorldTest

if __name__ == "__main__":
    print("=" * 80)
    print("🚀 知识图谱记忆系统 v7.0 - 1分钟快速测试")
    print("=" * 80)
    
    duration = 60  # 1分钟
    print(f"目标时长: {duration}秒")
    print(f"开始时间: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 80)
    print()
    
    test = UltimateRealWorldTest(duration_seconds=duration)
    
    try:
        test.run()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户提前终止!")
    
    print(f"\n完成时间: {datetime.now().strftime('%H:%M:%S')}")
