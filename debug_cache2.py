#!/usr/bin/env python3
"""详细调试缓存问题"""
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
print("详细调试缓存问题")
print("=" * 70)

print("\n缓存配置:")
print(f"MemorySystem._cache: {type(ms._cache)}")
print(f"MemorySystem._graph._cache: {type(ms._graph._cache)}")

print("\n" + "=" * 70)
print("第一次调用 recall('Item_500')")
print("=" * 70)
result1 = ms.recall("Item_500")
print(f"结果: {len(result1)} 项")
print(f"MS缓存 - 大小: {len(ms._cache._cache)}, keys: {list(ms._cache._cache.keys())}")
print(f"Graph缓存 - 大小: {len(ms._graph._cache._cache)}, keys: {list(ms._graph._cache._cache.keys())}")

print("\n" + "=" * 70)
print("第二次调用 recall('Item_500')")
print("=" * 70)
result2 = ms.recall("Item_500")
print(f"结果: {len(result2)} 项")
print(f"MS缓存 - 大小: {len(ms._cache._cache)}, keys: {list(ms._cache._cache.keys())}")
print(f"Graph缓存 - 大小: {len(ms._graph._cache._cache)}, keys: {list(ms._graph._cache._cache.keys())}")

print("\n" + "=" * 70)
print("分析")
print("=" * 70)
print("问题: MemorySystem 和 NetworkXGraphEngine 有各自的缓存")
print("recall() 使用 MS._cache")
print("但 recall() 内部调用的 search() 使用 Graph._cache")
print("导致缓存没有正确复用！")
