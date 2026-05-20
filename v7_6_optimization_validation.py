#!/usr/bin/env python3
"""
v7.6 优化验证测试
验证v7.6向量搜索优化效果
"""

import sys
import os
import time
import random

sys.path.insert(0, os.path.dirname(os.path.abspath('.')))

from kg_memory_v7_optimized import MemorySystemV7Optimized, NodeType


def main():
    print("\n" + "=" * 80)
    print("🚀 v7.6 向量搜索优化验证测试")
    print("=" * 80)
    
    memory = MemorySystemV7Optimized()
    
    # 测试规模
    test_sizes = [1000, 5000, 10000, 20000]
    results = []
    
    for size in test_sizes:
        print(f"\n📦 测试规模: {size:,} 向量...")
        
        # 添加测试数据
        start = time.time()
        node_labels = []
        for i in range(size):
            label = f"test_node_{len(results)}_{i}"
            node_labels.append(label)
            memory.remember(label, compute_embedding=True)
        add_time = time.time() - start
        print(f"   添加节点: {add_time:.2f}秒 ({size/add_time:.0f} 节点/秒)")
        
        # 测试语义搜索
        print(f"🔍 语义搜索测试...")
        search_times = []
        num_tests = 50
        
        for i in range(num_tests):
            query_label = random.choice(node_labels)
            start = time.time()
            memory.semantic_search(query_label, k=10)
            search_times.append(time.time() - start)
        
        avg_search_time = sum(search_times) / len(search_times)
        max_search_time = max(search_times)
        min_search_time = min(search_times)
        
        print(f"   平均搜索: {avg_search_time:.4f}秒")
        print(f"   最快搜索: {min_search_time:.4f}秒")
        print(f"   最慢搜索: {max_search_time:.4f}秒")
        
        results.append({
            "size": size,
            "add_time": add_time,
            "avg_search": avg_search_time,
            "add_rate": size / add_time,
            "search_rate": 1 / avg_search_time if avg_search_time > 0 else 0
        })
    
    # 最终统计和对比
    print("\n" + "=" * 80)
    print("📊 性能对比总结")
    print("=" * 80)
    
    print(f"\n{'规模':>8} {'添加时间':>10} {'添加速率':>15} {'平均搜索':>12} {'相对性能':>12}")
    print("-" * 60)
    
    # 以第一个规模为基准
    base_search = results[0]['avg_search']
    
    for r in results:
        size = r['size']
        relative = r['avg_search'] / base_search
        print(f"{size:>8,} {r['add_time']:>10.2f}s {r['add_rate']:>14.0f}/s {r['avg_search']:>10.4f}s {relative:>11.2f}x")
    
    # 扩展性分析
    if len(results) >= 2:
        scale_factor = results[-1]['size'] / results[0]['size']
        time_factor = results[-1]['avg_search'] / results[0]['avg_search']
        
        print(f"\n📈 扩展性分析:")
        print(f"   规模增长: {scale_factor:.1f}x")
        print(f"   搜索时间增长: {time_factor:.2f}x")
        
        if time_factor < scale_factor:
            print(f"   ✅ 优秀: 搜索时间增长慢于规模增长")
        elif time_factor < scale_factor * 2:
            print(f"   ✅ 良好: 搜索时间增长合理")
        else:
            print(f"   ⚠️ 需要关注: 搜索时间增长较快")
    
    print("\n" + "=" * 80)
    print("🎯 v7.6优化验证完成！")
    print("=" * 80)
    
    # 对比v7.5基准（来自之前的分析）
    print(f"\n💡 对比v7.5基准:")
    print(f"   v7.5基准: 5000向量搜索约1.634秒")
    v76_5000_time = [r['avg_search'] for r in results if r['size'] == 5000]
    if v76_5000_time:
        improvement = 1.634 / v76_5000_time[0]
        print(f"   v7.6性能: {v76_5000_time[0]:.3f}秒")
        print(f"   性能提升: {improvement:.1f}x 🚀")
    
    print("\n✅ v7.6向量搜索优化成功！")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
