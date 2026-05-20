#!/usr/bin/env python3
"""调试缓存问题"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from kg_memory.core import MemorySystem
import tempfile

temp_dir = tempfile.mkdtemp()
ms = MemorySystem(temp_dir)
ms.clear()

# 添加数据
for i in range(1000):
    ms.remember(f"Item_{i}", {"data": f"value_{i}"})

print("=" * 70)
print("调试缓存问题")
print("=" * 70)

# 第一次查询
print("\n第一次调用 recall('Item_500')")
result1 = ms.recall("Item_500")
print(f"结果数量: {len(result1)}")
cache_stats1 = ms._graph._cache.stats()
print(f"缓存统计: {cache_stats1}")

# 第二次查询
print("\n第二次调用 recall('Item_500')")
result2 = ms.recall("Item_500")
print(f"结果数量: {len(result2)}")
cache_stats2 = ms._graph._cache.stats()
print(f"缓存统计: {cache_stats2}")

# 检查缓存内容
print("\n缓存详情:")
cache = ms._graph._cache
print(f"缓存大小: {len(cache._cache)}")
print(f"缓存命中率: {cache_stats2.get('hit_rate', 0) * 100:.1f}%")

# 检查缓存 key
print("\n缓存中的 keys:")
for i, key in enumerate(list(cache._cache.keys())[:10]):
    print(f"  {i+1}. {key}")

# 测试 search 方法
print("\n" + "=" * 70)
print("测试 search 方法")
print("=" * 70)

cache.clear()

print("\n第一次调用 search('Item_500')")
result1 = ms._graph.search("Item_500", k=10)
print(f"结果数量: {len(result1)}")
cache_stats1 = ms._graph._cache.stats()
print(f"缓存统计: {cache_stats1}")

print("\n第二次调用 search('Item_500')")
result2 = ms._graph.search("Item_500", k=10)
print(f"结果数量: {len(result2)}")
cache_stats2 = ms._graph._cache.stats()
print(f"缓存统计: {cache_stats2}")

print("\n缓存中的 keys:")
for i, key in enumerate(list(cache._cache.keys())[:10]):
    print(f"  {i+1}. {key}")
